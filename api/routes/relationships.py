"""
Collective Memory Platform - Relationship Routes

CRUD operations for entity relationships.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Relationship, Entity
from api.services.activity import activity_service
from api.services.auth import require_auth, require_auth_strict, require_write_access


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


def register_relationship_routes(api: Api):
    """Register relationship routes with the API."""

    ns = api.namespace(
        'relationships',
        description='Knowledge graph relationship operations',
        path='/relationships'
    )

    # Define models for OpenAPI documentation
    relationship_model = ns.model('Relationship', {
        'relationship_key': fields.String(readonly=True, description='Unique relationship identifier'),
        'from_entity_key': fields.String(required=True, description='Source entity key'),
        'to_entity_key': fields.String(required=True, description='Target entity key'),
        'relationship_type': fields.String(required=True, description='Type: WORKS_ON, USES_TECHNOLOGY, DEPENDS_ON, etc.'),
        'properties': fields.Raw(description='Additional properties as JSON'),
        'confidence': fields.Float(description='Confidence score 0.0-1.0'),
        'valid_from': fields.DateTime(description='Relationship valid from date'),
        'valid_to': fields.DateTime(description='Relationship valid to date'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    relationship_create = ns.model('RelationshipCreate', {
        'from_entity_key': fields.String(required=True, description='Source entity key'),
        'to_entity_key': fields.String(required=True, description='Target entity key'),
        'relationship_type': fields.String(required=True, description='Relationship type'),
        'properties': fields.Raw(description='Additional properties as JSON'),
        'confidence': fields.Float(description='Confidence score 0.0-1.0', default=1.0),
        'valid_from': fields.DateTime(description='Relationship valid from date'),
        'valid_to': fields.DateTime(description='Relationship valid to date'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class RelationshipList(Resource):
        @ns.doc('list_relationships')
        @ns.param('type', 'Filter by relationship type')
        @ns.param('entity', 'Filter by entity key (source or target)')
        @ns.param('limit', 'Maximum results', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """List relationships with optional filtering."""
            rel_type = request.args.get('type')
            entity_key = request.args.get('entity')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            query = Relationship.query

            if rel_type:
                query = query.filter_by(relationship_type=rel_type)
            if entity_key:
                query = query.filter(
                    (Relationship.from_entity_key == entity_key) |
                    (Relationship.to_entity_key == entity_key)
                )

            total = query.count()
            relationships = query.limit(limit).offset(offset).all()

            return {
                'success': True,
                'msg': f'Found {total} relationships',
                'data': {
                    'relationships': [r.to_dict(include_entities=True) for r in relationships],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

        @ns.doc('create_relationship')
        @ns.expect(relationship_create)
        @ns.marshal_with(response_model, code=201)
        @require_write_access
        def post(self):
            """Create a new relationship. Requires write access."""
            data = request.json

            # Validate required fields
            if not data.get('from_entity_key'):
                return {'success': False, 'msg': 'from_entity_key is required'}, 400
            if not data.get('to_entity_key'):
                return {'success': False, 'msg': 'to_entity_key is required'}, 400
            if not data.get('relationship_type'):
                return {'success': False, 'msg': 'relationship_type is required'}, 400

            # Validate that both entities exist
            from_entity = Entity.get_by_key(data['from_entity_key'])
            to_entity = Entity.get_by_key(data['to_entity_key'])

            if not from_entity:
                return {'success': False, 'msg': f"Source entity not found: {data['from_entity_key']}"}, 400
            if not to_entity:
                return {'success': False, 'msg': f"Target entity not found: {data['to_entity_key']}"}, 400

            relationship = Relationship(
                from_entity_key=data['from_entity_key'],
                to_entity_key=data['to_entity_key'],
                relationship_type=data['relationship_type'],
                properties=data.get('properties', {}),
                confidence=data.get('confidence', 1.0),
                valid_from=data.get('valid_from'),
                valid_to=data.get('valid_to')
            )

            try:
                relationship.save()
                # Record activity
                activity_service.record_relationship_created(
                    actor=get_actor(),
                    relationship_key=relationship.relationship_key,
                    from_entity_key=from_entity.entity_key,
                    from_entity_name=from_entity.name,
                    to_entity_key=to_entity.entity_key,
                    to_entity_name=to_entity.name,
                    relationship_type=relationship.relationship_type,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )
                return {
                    'success': True,
                    'msg': 'Relationship created',
                    'data': relationship.to_dict(include_entities=True)
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:relationship_key>')
    @ns.param('relationship_key', 'Relationship identifier')
    class RelationshipDetail(Resource):
        @ns.doc('get_relationship')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, relationship_key):
            """Get a relationship by key."""
            relationship = Relationship.get_by_key(relationship_key)
            if not relationship:
                return {'success': False, 'msg': 'Relationship not found'}, 404

            return {
                'success': True,
                'msg': 'Relationship retrieved',
                'data': relationship.to_dict(include_entities=True)
            }

        @ns.doc('update_relationship')
        @ns.expect(relationship_create)
        @ns.marshal_with(response_model)
        @require_write_access
        def put(self, relationship_key):
            """Update a relationship. Requires write access."""
            relationship = Relationship.get_by_key(relationship_key)
            if not relationship:
                return {'success': False, 'msg': 'Relationship not found'}, 404

            data = request.json
            relationship.update_from_dict(data)

            try:
                relationship.save()
                return {
                    'success': True,
                    'msg': 'Relationship updated',
                    'data': relationship.to_dict(include_entities=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_relationship')
        @ns.marshal_with(response_model)
        @require_write_access
        def delete(self, relationship_key):
            """Delete a relationship. Requires write access."""
            relationship = Relationship.get_by_key(relationship_key)
            if not relationship:
                return {'success': False, 'msg': 'Relationship not found'}, 404

            try:
                # Capture info before deletion
                rel_type = relationship.relationship_type
                from_key = relationship.from_entity_key
                to_key = relationship.to_entity_key

                relationship.delete()

                # Record activity
                activity_service.record_relationship_deleted(
                    actor=get_actor(),
                    relationship_key=relationship_key,
                    from_entity_key=from_key,
                    to_entity_key=to_key,
                    relationship_type=rel_type,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                return {
                    'success': True,
                    'msg': 'Relationship deleted',
                    'data': None
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
