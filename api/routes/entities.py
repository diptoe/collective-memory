"""
Collective Memory Platform - Entity Routes

CRUD operations for knowledge graph entities.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Entity, db
from api.services.activity import activity_service
from api.services.auth import require_auth


def get_actor() -> str:
    """Get actor from X-Agent-Id header or return 'system'."""
    return request.headers.get('X-Agent-Id', 'system')


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
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
        @ns.param('limit', 'Maximum results', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """List entities with optional filtering. Automatically filtered by user's domain."""
            entity_type = request.args.get('type')
            search = request.args.get('search')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            query = Entity.query

            # Multi-tenancy: automatically filter by user's domain
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
        @require_auth
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

            entity = Entity(
                entity_type=data['entity_type'],
                name=data['name'],
                properties=data.get('properties', {}),
                domain_key=user_domain,  # Auto-set from user's domain
                confidence=data.get('confidence', 1.0),
                source=data.get('source')
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
                    entity_name=entity.name
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
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """Get all distinct entity types with counts. Filtered by user's domain."""
            from sqlalchemy import func

            query = db.session.query(
                Entity.entity_type,
                func.count(Entity.entity_key).label('count')
            )

            # Multi-tenancy: filter by user's domain
            user_domain = get_user_domain_key()
            if user_domain:
                query = query.filter(Entity.domain_key == user_domain)

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

    def _check_entity_domain_access(entity, user_domain):
        """Check if user has access to entity based on domain."""
        if user_domain and entity.domain_key != user_domain:
            return False
        return True

    @ns.route('/<string:entity_key>')
    @ns.param('entity_key', 'Entity identifier')
    class EntityDetail(Resource):
        @ns.doc('get_entity')
        @ns.param('include_relationships', 'Include relationships', type=bool, default=False)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, entity_key):
            """Get an entity by key. Must belong to user's domain."""
            include_rels = request.args.get('include_relationships', 'false').lower() == 'true'

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_entity_domain_access(entity, user_domain):
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Record activity
            activity_service.record_entity_read(
                actor=get_actor(),
                entity_key=entity.entity_key,
                entity_type=entity.entity_type,
                entity_name=entity.name
            )

            return {
                'success': True,
                'msg': 'Entity retrieved',
                'data': {'entity': entity.to_dict(include_relationships=include_rels)}
            }

        @ns.doc('update_entity')
        @ns.expect(entity_create)
        @ns.marshal_with(response_model)
        @require_auth
        def put(self, entity_key):
            """Update an entity. Must belong to user's domain."""
            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_entity_domain_access(entity, user_domain):
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
                    entity_name=entity.name
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
        @require_auth
        def delete(self, entity_key):
            """Delete an entity and all its relationships. Must belong to user's domain."""
            from api.models.relationship import Relationship

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_entity_domain_access(entity, user_domain):
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
                    entity_name=entity_name
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
        @require_auth
        def post(self, entity_key):
            """Generate embedding for an entity. Must belong to user's domain."""
            from api.services import embedding_service

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_entity_domain_access(entity, user_domain):
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
