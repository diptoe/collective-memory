"""
Collective Memory Platform - Knowledge Routes

Statistics and overview of knowledge graph composition by scope.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields
from sqlalchemy import func

from api.models import Entity, db
from api.models.relationship import Relationship
from api.models.domain import Domain
from api.models.team import Team
from api.models.user import User
from api.services.auth import require_auth
from api.services.scope import scope_service


def register_knowledge_routes(api: Api):
    """Register knowledge routes with the API."""

    ns = api.namespace(
        'knowledge',
        description='Knowledge graph statistics and overview',
        path='/knowledge'
    )

    # Define models for OpenAPI documentation
    scope_stats_model = ns.model('ScopeStats', {
        'scope_type': fields.String(description='Scope type: domain, team, or user'),
        'scope_key': fields.String(description='Scope key'),
        'name': fields.String(description='Human-readable scope name'),
        'entity_count': fields.Integer(description='Number of entities in scope'),
        'entity_types': fields.Raw(description='Entity type counts'),
        'relationship_count': fields.Integer(description='Number of relationships in scope'),
    })

    cross_scope_model = ns.model('CrossScopeRelationship', {
        'from_scope': fields.Raw(description='Source scope {scope_type, scope_key}'),
        'to_scope': fields.Raw(description='Target scope {scope_type, scope_key}'),
        'count': fields.Integer(description='Number of cross-scope relationships'),
    })

    totals_model = ns.model('KnowledgeTotals', {
        'entities': fields.Integer(description='Total entities'),
        'relationships': fields.Integer(description='Total relationships'),
        'scopes': fields.Integer(description='Total scopes'),
    })

    stats_response_model = ns.model('KnowledgeStatsResponse', {
        'scopes': fields.List(fields.Nested(scope_stats_model)),
        'cross_scope_relationships': fields.List(fields.Nested(cross_scope_model)),
        'totals': fields.Nested(totals_model),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('/stats')
    class KnowledgeStats(Resource):
        @ns.doc('get_knowledge_stats')
        @ns.param('domain_key', 'Filter by domain (admin only)')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Get knowledge graph statistics by scope.

            Returns scope-aggregated entity and relationship counts.
            Admins can filter by domain_key. Non-admins see only their accessible scopes.
            """
            user = g.current_user
            domain_filter = request.args.get('domain_key')

            # Only admins can filter by domain
            if domain_filter and not user.is_admin:
                return {'success': False, 'msg': 'Admin access required for domain filtering'}, 403

            # Build base query filtered by user's access
            entity_query = Entity.query

            if user.is_admin and domain_filter:
                # Admin filtering by specific domain
                entity_query = entity_query.filter(Entity.domain_key == domain_filter)
            elif not user.is_admin:
                # Non-admin: filter by accessible scopes
                entity_query = scope_service.filter_query_by_scope(entity_query, user, Entity)

            # Get scope statistics
            scopes_data = _get_scope_stats(entity_query, user, domain_filter)

            # Get cross-scope relationships
            cross_scope = _get_cross_scope_relationships(user, domain_filter)

            # Calculate totals
            total_entities = sum(s['entity_count'] for s in scopes_data)
            total_relationships = sum(s['relationship_count'] for s in scopes_data)

            return {
                'success': True,
                'msg': f'Knowledge stats retrieved for {len(scopes_data)} scopes',
                'data': {
                    'scopes': scopes_data,
                    'cross_scope_relationships': cross_scope,
                    'totals': {
                        'entities': total_entities,
                        'relationships': total_relationships,
                        'scopes': len(scopes_data)
                    }
                }
            }

    @ns.route('/domains')
    class KnowledgeDomains(Resource):
        @ns.doc('list_domains_for_knowledge')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            List domains available for knowledge filtering.

            Admin only - returns all active domains for domain switcher.
            """
            user = g.current_user

            if not user.is_admin:
                return {'success': False, 'msg': 'Admin access required'}, 403

            domains = Domain.query.filter_by(status='active').order_by(Domain.name).all()

            return {
                'success': True,
                'msg': f'Found {len(domains)} domains',
                'data': {
                    'domains': [
                        {
                            'domain_key': d.domain_key,
                            'name': d.name,
                            'slug': d.slug
                        }
                        for d in domains
                    ]
                }
            }


def _get_scope_stats(base_query, user, domain_filter=None):
    """
    Get entity statistics grouped by scope.

    Args:
        base_query: Pre-filtered SQLAlchemy query
        user: Current user
        domain_filter: Optional domain key for admin filtering

    Returns:
        List of scope statistics dictionaries
    """
    # Query entities grouped by scope
    scope_query = db.session.query(
        Entity.scope_type,
        Entity.scope_key,
        Entity.domain_key,
        func.count(Entity.entity_key).label('entity_count')
    ).group_by(
        Entity.scope_type,
        Entity.scope_key,
        Entity.domain_key
    )

    # Apply same filters as base query
    if user.is_admin and domain_filter:
        scope_query = scope_query.filter(Entity.domain_key == domain_filter)
    elif not user.is_admin:
        scope_query = scope_service.filter_query_by_scope(scope_query, user, Entity)

    scope_results = scope_query.all()

    # Build scope data with names and entity types
    scopes_data = []

    # Group by normalized scope key
    scope_map = {}
    for row in scope_results:
        scope_type = row.scope_type or 'domain'
        scope_key = row.scope_key or row.domain_key

        key = (scope_type, scope_key)
        if key not in scope_map:
            scope_map[key] = {
                'scope_type': scope_type,
                'scope_key': scope_key,
                'domain_key': row.domain_key,
                'entity_count': 0
            }
        scope_map[key]['entity_count'] += row.entity_count

    # Resolve names and get entity types for each scope
    for (scope_type, scope_key), data in scope_map.items():
        name = _resolve_scope_name(scope_type, scope_key)

        # Get entity types for this scope
        entity_types = _get_entity_types_for_scope(scope_type, scope_key, data['domain_key'])

        # Get relationship count for this scope
        rel_count = _get_relationship_count_for_scope(scope_type, scope_key, data['domain_key'])

        scopes_data.append({
            'scope_type': scope_type,
            'scope_key': scope_key,
            'name': name,
            'entity_count': data['entity_count'],
            'entity_types': entity_types,
            'relationship_count': rel_count
        })

    # Sort by entity count descending
    scopes_data.sort(key=lambda x: x['entity_count'], reverse=True)

    return scopes_data


def _resolve_scope_name(scope_type: str, scope_key: str) -> str:
    """Resolve scope key to human-readable name."""
    if scope_type == 'domain':
        domain = Domain.query.filter_by(domain_key=scope_key).first()
        return domain.name if domain else scope_key
    elif scope_type == 'team':
        team = Team.query.filter_by(team_key=scope_key).first()
        return team.name if team else scope_key
    elif scope_type == 'user':
        user = User.query.filter_by(user_key=scope_key).first()
        return user.display_name if user else scope_key
    return scope_key


def _get_entity_types_for_scope(scope_type: str, scope_key: str, domain_key: str) -> dict:
    """Get entity type counts for a specific scope."""
    query = db.session.query(
        Entity.entity_type,
        func.count(Entity.entity_key).label('count')
    )

    if scope_type == 'domain':
        query = query.filter(
            db.or_(Entity.scope_type.is_(None), Entity.scope_type == 'domain'),
            Entity.domain_key == scope_key
        )
    else:
        query = query.filter(
            Entity.scope_type == scope_type,
            Entity.scope_key == scope_key
        )

    results = query.group_by(Entity.entity_type).all()

    return {row.entity_type: row.count for row in results}


def _get_relationship_count_for_scope(scope_type: str, scope_key: str, domain_key: str) -> int:
    """Get count of relationships where both entities are in the specified scope."""
    # Subquery to get entity keys in this scope
    if scope_type == 'domain':
        entity_subq = db.session.query(Entity.entity_key).filter(
            db.or_(Entity.scope_type.is_(None), Entity.scope_type == 'domain'),
            Entity.domain_key == scope_key
        ).subquery()
    else:
        entity_subq = db.session.query(Entity.entity_key).filter(
            Entity.scope_type == scope_type,
            Entity.scope_key == scope_key
        ).subquery()

    # Count relationships where both from and to are in scope
    count = Relationship.query.filter(
        Relationship.from_entity_key.in_(db.select(entity_subq)),
        Relationship.to_entity_key.in_(db.select(entity_subq))
    ).count()

    return count


def _get_cross_scope_relationships(user, domain_filter=None):
    """
    Get relationships that cross scope boundaries.

    Returns list of {from_scope, to_scope, count} dictionaries.
    """
    # This is a more complex query - we need to join entities to get their scopes
    # For performance, we'll limit this to meaningful cross-scope connections

    query = db.session.query(
        Entity.scope_type.label('from_scope_type'),
        Entity.scope_key.label('from_scope_key'),
        db.aliased(Entity).scope_type.label('to_scope_type'),
        db.aliased(Entity).scope_key.label('to_scope_key'),
        func.count(Relationship.relationship_key).label('count')
    )

    # Alias for the to_entity
    ToEntity = db.aliased(Entity)

    query = db.session.query(
        Entity.scope_type.label('from_scope_type'),
        Entity.scope_key.label('from_scope_key'),
        ToEntity.scope_type.label('to_scope_type'),
        ToEntity.scope_key.label('to_scope_key'),
        func.count(Relationship.relationship_key).label('count')
    ).join(
        Relationship, Entity.entity_key == Relationship.from_entity_key
    ).join(
        ToEntity, ToEntity.entity_key == Relationship.to_entity_key
    ).filter(
        # Only count cross-scope relationships (different scope_key or scope_type)
        db.or_(
            Entity.scope_type != ToEntity.scope_type,
            Entity.scope_key != ToEntity.scope_key
        )
    )

    # Apply access filters
    if user.is_admin and domain_filter:
        query = query.filter(
            Entity.domain_key == domain_filter,
            ToEntity.domain_key == domain_filter
        )
    elif not user.is_admin:
        # For non-admins, filter to accessible scopes
        # This is simplified - could be more precise with scope_service
        if user.domain_key:
            query = query.filter(Entity.domain_key == user.domain_key)

    query = query.group_by(
        Entity.scope_type,
        Entity.scope_key,
        ToEntity.scope_type,
        ToEntity.scope_key
    ).having(
        func.count(Relationship.relationship_key) > 0
    ).order_by(
        func.count(Relationship.relationship_key).desc()
    ).limit(20)  # Limit to top 20 cross-scope connections

    results = query.all()

    cross_scope = []
    for row in results:
        from_type = row.from_scope_type or 'domain'
        from_key = row.from_scope_key
        to_type = row.to_scope_type or 'domain'
        to_key = row.to_scope_key

        cross_scope.append({
            'from_scope': {
                'scope_type': from_type,
                'scope_key': from_key,
                'name': _resolve_scope_name(from_type, from_key) if from_key else None
            },
            'to_scope': {
                'scope_type': to_type,
                'scope_key': to_key,
                'name': _resolve_scope_name(to_type, to_key) if to_key else None
            },
            'count': row.count
        })

    return cross_scope
