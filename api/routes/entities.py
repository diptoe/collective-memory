"""
Collective Memory Platform - Entity Routes

CRUD operations for knowledge graph entities.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Entity, db
from api.services.activity import activity_service
from api.services.auth import require_auth, require_auth_strict, require_domain_admin, require_write_access
from api.services.scope import scope_service


def get_actor() -> str:
    """Get actor from X-Agent-Id header or return 'system'."""
    return request.headers.get('X-Agent-Id', 'system')


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key for activity tracking."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


def register_entity_routes(api: Api):
    """Register entity routes with the API."""

    ns = api.namespace(
        'entities',
        description='Knowledge graph entity operations',
        path='/entities'
    )

    # Define models for OpenAPI documentation
    entity_properties = ns.model('EntityProperties', {
        'key': fields.String(description='Any additional property key'),
    })

    entity_model = ns.model('Entity', {
        'entity_key': fields.String(readonly=True, description='Unique entity identifier'),
        'entity_type': fields.String(required=True, description='Type: Person, Project, Technology, Document, Organization, Concept'),
        'name': fields.String(required=True, description='Entity name'),
        'properties': fields.Raw(description='Additional properties as JSON'),
        'domain_key': fields.String(description='Domain key for multi-tenancy'),
        'confidence': fields.Float(description='Confidence score 0.0-1.0'),
        'source': fields.String(description='Source of this entity'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    entity_create = ns.model('EntityCreate', {
        'entity_type': fields.String(required=True, description='Type: Person, Project, Technology, Document, Organization, Concept'),
        'name': fields.String(required=True, description='Entity name'),
        'properties': fields.Raw(description='Additional properties as JSON'),
        'domain_key': fields.String(description='Domain key for multi-tenancy'),
        'confidence': fields.Float(description='Confidence score 0.0-1.0', default=1.0),
        'source': fields.String(description='Source of this entity'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class EntityList(Resource):
        @ns.doc('list_entities')
        @ns.param('type', 'Filter by entity type')
        @ns.param('search', 'Search by name')
        @ns.param('scope_type', 'Filter by scope type: domain, team, or user')
        @ns.param('scope_key', 'Filter by specific scope key (requires scope_type)')
        @ns.param('limit', 'Maximum results', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """List entities with optional filtering. Filtered by user's accessible scopes."""
            entity_type = request.args.get('type')
            search = request.args.get('search')
            scope_type_filter = request.args.get('scope_type')
            scope_key_filter = request.args.get('scope_key')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            query = Entity.query

            # Multi-tenancy: filter by user's accessible scopes (domain, teams, personal)
            user = g.current_user if hasattr(g, 'current_user') else None
            if user:
                # If specific scope filter requested, validate access and filter
                if scope_type_filter:
                    # Validate user has access to this scope
                    if scope_key_filter and not scope_service.can_access_scope(user, scope_type_filter, scope_key_filter):
                        return {'success': False, 'msg': 'Access denied to this scope'}, 403

                    # Apply specific scope filter
                    if scope_type_filter == 'system':
                        # System scope: global entities visible to all (e.g., Client entities)
                        query = query.filter(
                            Entity.scope_type == 'system',
                            Entity.scope_key.is_(None)
                        )
                    elif scope_type_filter == 'domain':
                        query = query.filter(
                            db.or_(Entity.scope_type.is_(None), Entity.scope_type == 'domain'),
                            Entity.domain_key == (scope_key_filter or user.domain_key)
                        )
                    elif scope_type_filter == 'team':
                        if not scope_key_filter:
                            return {'success': False, 'msg': 'scope_key required for team scope filter'}, 400
                        query = query.filter(Entity.scope_type == 'team', Entity.scope_key == scope_key_filter)
                    elif scope_type_filter == 'user':
                        query = query.filter(Entity.scope_type == 'user', Entity.scope_key == (scope_key_filter or user.user_key))
                else:
                    # No specific scope filter - show all accessible scopes
                    query = scope_service.filter_query_by_scope(query, user, Entity)
            else:
                # Fall back to domain filter for legacy/unauthenticated requests
                user_domain = get_user_domain_key()
                if user_domain:
                    query = query.filter_by(domain_key=user_domain)

            if entity_type:
                query = query.filter_by(entity_type=entity_type)
            if search:
                query = query.filter(Entity.name.ilike(f'%{search}%'))

            total = query.count()
            entities = query.limit(limit).offset(offset).all()

            # Record search activity if a search was performed
            if search or entity_type:
                activity_service.record_search(
                    actor=get_actor(),
                    query=search,
                    search_type='entity',
                    entity_type=entity_type,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key(),
                    result_count=total
                )

            return {
                'success': True,
                'msg': f'Found {total} entities',
                'data': {
                    'entities': [e.to_dict() for e in entities],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

        @ns.doc('create_entity')
        @ns.expect(entity_create)
        @ns.marshal_with(response_model, code=201)
        @require_write_access
        def post(self):
            """Create a new entity. Automatically assigned to user's domain."""
            data = request.json

            if not data.get('entity_type'):
                return {'success': False, 'msg': 'entity_type is required'}, 400
            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400

            # Check if entity_key is specified and already exists
            custom_key = data.get('entity_key')
            if custom_key:
                existing = Entity.get_by_key(custom_key)
                if existing:
                    return {'success': False, 'msg': f'Entity with key {custom_key} already exists'}, 409

            # Multi-tenancy: automatically set domain from authenticated user
            user_domain = get_user_domain_key()

            # Handle scope - default to domain scope if not specified
            scope_type = data.get('scope_type')
            scope_key = data.get('scope_key')

            # Validate scope if provided
            if scope_type:
                user = g.current_user if hasattr(g, 'current_user') else None
                if user and scope_key:
                    if not scope_service.can_access_scope(user, scope_type, scope_key):
                        return {'success': False, 'msg': 'Access denied to specified scope'}, 403

            entity = Entity(
                entity_type=data['entity_type'],
                name=data['name'],
                properties=data.get('properties', {}),
                domain_key=user_domain,  # Auto-set from user's domain
                confidence=data.get('confidence', 1.0),
                source=data.get('source'),
                scope_type=scope_type,
                scope_key=scope_key,
                work_session_key=data.get('work_session_key')
            )

            # Override auto-generated key if custom key provided
            if custom_key:
                entity.entity_key = custom_key

            try:
                entity.save()
                # Record activity
                activity_service.record_entity_created(
                    actor=get_actor(),
                    entity_key=entity.entity_key,
                    entity_type=entity.entity_type,
                    entity_name=entity.name,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )
                return {
                    'success': True,
                    'msg': 'Entity created',
                    'data': {'entity': entity.to_dict()}
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/types')
    class EntityTypes(Resource):
        @ns.doc('list_entity_types')
        @ns.param('scope_type', 'Filter by scope type: domain, team, or user')
        @ns.param('scope_key', 'Filter by specific scope key (requires scope_type)')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """Get all distinct entity types with counts. Filtered by user's accessible scopes."""
            from sqlalchemy import func

            scope_type_filter = request.args.get('scope_type')
            scope_key_filter = request.args.get('scope_key')

            query = db.session.query(
                Entity.entity_type,
                func.count(Entity.entity_key).label('count')
            )

            # Multi-tenancy: filter by user's domain first
            user_domain = get_user_domain_key()
            if user_domain:
                query = query.filter(Entity.domain_key == user_domain)

            # Apply scope filtering (same logic as list endpoint)
            user = g.current_user if hasattr(g, 'current_user') else None
            if user and scope_type_filter:
                # Validate user has access to this scope
                if scope_key_filter and not scope_service.can_access_scope(user, scope_type_filter, scope_key_filter):
                    return {'success': False, 'msg': 'Access denied to this scope'}, 403

                # Apply specific scope filter
                if scope_type_filter == 'domain':
                    query = query.filter(
                        db.or_(Entity.scope_type.is_(None), Entity.scope_type == 'domain'),
                        Entity.domain_key == (scope_key_filter or user.domain_key)
                    )
                elif scope_type_filter == 'team':
                    if not scope_key_filter:
                        return {'success': False, 'msg': 'scope_key required for team scope filter'}, 400
                    query = query.filter(Entity.scope_type == 'team', Entity.scope_key == scope_key_filter)
                elif scope_type_filter == 'user':
                    query = query.filter(Entity.scope_type == 'user', Entity.scope_key == (scope_key_filter or user.user_key))
            elif user:
                # No specific scope filter - show all accessible scopes
                query = scope_service.filter_query_by_scope(query, user, Entity)

            results = query.group_by(Entity.entity_type).order_by(Entity.entity_type).all()

            types = [
                {'type': row.entity_type, 'count': row.count}
                for row in results
            ]

            return {
                'success': True,
                'msg': f'Found {len(types)} entity types',
                'data': {
                    'types': types
                }
            }

    def _check_entity_access(entity, user):
        """Check if user has access to entity based on scope."""
        if not user:
            return False  # No user, deny access

        # Use scope service to check access
        return scope_service.can_access_scope(
            user,
            entity.scope_type,
            entity.scope_key or entity.domain_key
        )

    @ns.route('/<string:entity_key>')
    @ns.param('entity_key', 'Entity identifier')
    class EntityDetail(Resource):
        @ns.doc('get_entity')
        @ns.param('include_relationships', 'Include relationships', type=bool, default=False)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, entity_key):
            """Get an entity by key. Must be accessible in user's scope."""
            include_rels = request.args.get('include_relationships', 'false').lower() == 'true'

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify scope access
            user = g.current_user if hasattr(g, 'current_user') else None
            if not _check_entity_access(entity, user):
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Record activity
            activity_service.record_entity_read(
                actor=get_actor(),
                entity_key=entity.entity_key,
                entity_type=entity.entity_type,
                entity_name=entity.name,
                domain_key=get_user_domain_key(),
                user_key=get_user_key()
            )

            return {
                'success': True,
                'msg': 'Entity retrieved',
                'data': {'entity': entity.to_dict(include_relationships=include_rels)}
            }

        @ns.doc('update_entity')
        @ns.expect(entity_create)
        @ns.marshal_with(response_model)
        @require_write_access
        def put(self, entity_key):
            """Update an entity. Requires write access. Must be accessible in user's scope."""
            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify scope access
            user = g.current_user if hasattr(g, 'current_user') else None
            if not _check_entity_access(entity, user):
                return {'success': False, 'msg': 'Entity not found'}, 404

            data = request.json
            entity.update_from_dict(data)

            try:
                entity.save()
                # Record activity
                activity_service.record_entity_updated(
                    actor=get_actor(),
                    entity_key=entity.entity_key,
                    entity_type=entity.entity_type,
                    entity_name=entity.name,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )
                return {
                    'success': True,
                    'msg': 'Entity updated',
                    'data': {'entity': entity.to_dict()}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_entity')
        @ns.marshal_with(response_model)
        @require_write_access
        def delete(self, entity_key):
            """Delete an entity and all its relationships. Requires write access. Must be accessible in user's scope."""
            from api.models.relationship import Relationship

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify scope access
            user = g.current_user if hasattr(g, 'current_user') else None
            if not _check_entity_access(entity, user):
                return {'success': False, 'msg': 'Entity not found'}, 404

            try:
                # Capture entity info before deletion for activity recording
                entity_name = entity.name
                entity_type = entity.entity_type

                # Delete all relationships involving this entity first
                relationships = Relationship.get_by_entity(entity_key)
                rel_count = len(relationships)
                for rel in relationships:
                    db.session.delete(rel)

                # Now delete the entity
                entity.delete()

                # Record activity
                activity_service.record_entity_deleted(
                    actor=get_actor(),
                    entity_key=entity_key,
                    entity_type=entity_type,
                    entity_name=entity_name,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                return {
                    'success': True,
                    'msg': f'Entity deleted along with {rel_count} relationships',
                    'data': {'relationships_deleted': rel_count}
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:entity_key>/embed')
    @ns.param('entity_key', 'Entity identifier')
    class EntityEmbed(Resource):
        @ns.doc('embed_entity')
        @ns.marshal_with(response_model)
        @require_write_access
        def post(self, entity_key):
            """Generate embedding for an entity. Requires write access. Must be accessible in user's scope."""
            from api.services import embedding_service

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify scope access
            user = g.current_user if hasattr(g, 'current_user') else None
            if not _check_entity_access(entity, user):
                return {'success': False, 'msg': 'Entity not found'}, 404

            try:
                entity.generate_embedding(embedding_service)
                entity.save()
                return {
                    'success': True,
                    'msg': 'Embedding generated',
                    'data': {
                        'entity_key': entity.entity_key,
                        'has_embedding': True
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': f'Embedding error: {str(e)}'}, 500

    move_scope_model = ns.model('MoveScope', {
        'scope_type': fields.String(required=True, description='Target scope type: domain, team, or user'),
        'scope_key': fields.String(required=True, description='Target scope key (domain_key, team_key, or user_key)'),
        'include_related': fields.Boolean(description='Include related entities recursively', default=True),
    })

    @ns.route('/<string:entity_key>/move-scope')
    @ns.param('entity_key', 'Entity identifier')
    class EntityMoveScope(Resource):
        @ns.doc('move_entity_scope')
        @ns.expect(move_scope_model)
        @ns.marshal_with(response_model)
        @require_domain_admin
        def post(self, entity_key):
            """
            Move an entity to a different scope. Requires domain_admin or admin role.

            Recursively updates the entity and all related entities (via relationships)
            to the new scope. Use this for moving projects between teams, or from
            domain to team scope.
            """
            from api.models.relationship import Relationship

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Verify entity is in user's domain
            user = g.current_user
            if entity.domain_key != user.domain_key:
                return {'success': False, 'msg': 'Entity not found'}, 404

            data = request.json
            target_scope_type = data.get('scope_type')
            target_scope_key = data.get('scope_key')
            include_related = data.get('include_related', True)

            if not target_scope_type or not target_scope_key:
                return {'success': False, 'msg': 'scope_type and scope_key are required'}, 400

            if target_scope_type not in ('domain', 'team', 'user'):
                return {'success': False, 'msg': 'scope_type must be domain, team, or user'}, 400

            # Validate target scope access
            if not scope_service.can_access_scope(user, target_scope_type, target_scope_key):
                return {'success': False, 'msg': 'Cannot move to this scope - access denied'}, 403

            try:
                # Collect entities to update
                entities_to_update = {entity_key: entity}
                source_scope_type = entity.scope_type
                source_scope_key = entity.scope_key

                if include_related:
                    # Find related entities, but be conservative:
                    # 1. Only follow OUTGOING relationships (where source is from_entity_key)
                    # 2. Only include entities in the SAME current scope as source
                    # This prevents accidentally moving unrelated projects that share
                    # common entities like technologies or people
                    visited = {entity_key}
                    to_visit = [entity_key]

                    while to_visit:
                        current_key = to_visit.pop(0)
                        # Only get outgoing relationships (current entity is the source)
                        relationships = Relationship.query.filter_by(from_entity_key=current_key).all()

                        for rel in relationships:
                            other_key = rel.to_entity_key

                            if other_key not in visited:
                                visited.add(other_key)
                                other_entity = Entity.get_by_key(other_key)

                                # Only include entities that:
                                # 1. Are in the same domain
                                # 2. Are in the same current scope as the source entity
                                if (other_entity and
                                    other_entity.domain_key == user.domain_key and
                                    other_entity.scope_type == source_scope_type and
                                    other_entity.scope_key == source_scope_key):
                                    entities_to_update[other_key] = other_entity
                                    to_visit.append(other_key)

                # Update all entities
                updated_keys = []
                for ent_key, ent in entities_to_update.items():
                    ent.scope_type = target_scope_type
                    ent.scope_key = target_scope_key
                    ent.save()
                    updated_keys.append(ent_key)

                # Record activity
                activity_service.record_entity_updated(
                    actor=get_actor(),
                    entity_key=entity_key,
                    entity_type=entity.entity_type,
                    entity_name=f"{entity.name} (moved to {target_scope_type} scope, {len(updated_keys)} entities)",
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                return {
                    'success': True,
                    'msg': f'Moved {len(updated_keys)} entities to {target_scope_type} scope',
                    'data': {
                        'entity_key': entity_key,
                        'scope_type': target_scope_type,
                        'scope_key': target_scope_key,
                        'updated_entities': updated_keys,
                        'total_updated': len(updated_keys)
                    }
                }

            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': f'Failed to move scope: {str(e)}'}, 500
