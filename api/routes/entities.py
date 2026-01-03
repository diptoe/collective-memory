"""
Collective Memory Platform - Entity Routes

CRUD operations for knowledge graph entities.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Entity, db


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
        'context_domain': fields.String(description='Context domain (e.g., work.jai-platform)'),
        'confidence': fields.Float(description='Confidence score 0.0-1.0'),
        'source': fields.String(description='Source of this entity'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    entity_create = ns.model('EntityCreate', {
        'entity_type': fields.String(required=True, description='Type: Person, Project, Technology, Document, Organization, Concept'),
        'name': fields.String(required=True, description='Entity name'),
        'properties': fields.Raw(description='Additional properties as JSON'),
        'context_domain': fields.String(description='Context domain'),
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
        @ns.param('domain', 'Filter by context domain')
        @ns.param('search', 'Search by name')
        @ns.param('limit', 'Maximum results', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        def get(self):
            """List entities with optional filtering."""
            entity_type = request.args.get('type')
            domain = request.args.get('domain')
            search = request.args.get('search')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            query = Entity.query

            if entity_type:
                query = query.filter_by(entity_type=entity_type)
            if domain:
                query = query.filter_by(context_domain=domain)
            if search:
                query = query.filter(Entity.name.ilike(f'%{search}%'))

            total = query.count()
            entities = query.limit(limit).offset(offset).all()

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
        def post(self):
            """Create a new entity."""
            data = request.json

            if not data.get('entity_type'):
                return {'success': False, 'msg': 'entity_type is required'}, 400
            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400

            entity = Entity(
                entity_type=data['entity_type'],
                name=data['name'],
                properties=data.get('properties', {}),
                context_domain=data.get('context_domain'),
                confidence=data.get('confidence', 1.0),
                source=data.get('source')
            )

            try:
                entity.save()
                return {
                    'success': True,
                    'msg': 'Entity created',
                    'data': entity.to_dict()
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:entity_key>')
    @ns.param('entity_key', 'Entity identifier')
    class EntityDetail(Resource):
        @ns.doc('get_entity')
        @ns.param('include_relationships', 'Include relationships', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self, entity_key):
            """Get an entity by key."""
            include_rels = request.args.get('include_relationships', 'false').lower() == 'true'

            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            return {
                'success': True,
                'msg': 'Entity retrieved',
                'data': entity.to_dict(include_relationships=include_rels)
            }

        @ns.doc('update_entity')
        @ns.expect(entity_create)
        @ns.marshal_with(response_model)
        def put(self, entity_key):
            """Update an entity."""
            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            data = request.json
            entity.update_from_dict(data)

            try:
                entity.save()
                return {
                    'success': True,
                    'msg': 'Entity updated',
                    'data': entity.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_entity')
        @ns.marshal_with(response_model)
        def delete(self, entity_key):
            """Delete an entity."""
            entity = Entity.get_by_key(entity_key)
            if not entity:
                return {'success': False, 'msg': 'Entity not found'}, 404

            try:
                entity.delete()
                return {
                    'success': True,
                    'msg': 'Entity deleted',
                    'data': None
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
