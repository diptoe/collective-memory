"""
Collective Memory Platform - Persona Routes

CRUD operations for AI personas.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Persona


def register_persona_routes(api: Api):
    """Register persona routes with the API."""

    ns = api.namespace(
        'personas',
        description='AI persona management',
        path='/personas'
    )

    # Define models for OpenAPI documentation
    persona_model = ns.model('Persona', {
        'persona_key': fields.String(readonly=True, description='Unique persona identifier'),
        'name': fields.String(required=True, description='Persona display name'),
        'model': fields.String(required=True, description='AI model identifier'),
        'role': fields.String(required=True, description='Persona role'),
        'system_prompt': fields.String(description='System prompt for the persona'),
        'personality': fields.Raw(description='Personality traits as JSON'),
        'capabilities': fields.List(fields.String, description='Persona capabilities'),
        'avatar_url': fields.String(description='Avatar image URL'),
        'color': fields.String(description='Theme color (hex)'),
        'status': fields.String(description='Status: active, inactive, archived'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    persona_create = ns.model('PersonaCreate', {
        'name': fields.String(required=True, description='Persona display name'),
        'model': fields.String(required=True, description='AI model identifier'),
        'role': fields.String(required=True, description='Persona role'),
        'system_prompt': fields.String(description='System prompt'),
        'personality': fields.Raw(description='Personality traits'),
        'capabilities': fields.List(fields.String, description='Capabilities'),
        'avatar_url': fields.String(description='Avatar URL'),
        'color': fields.String(description='Theme color', default='#d97757'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class PersonaList(Resource):
        @ns.doc('list_personas')
        @ns.param('role', 'Filter by role')
        @ns.param('model', 'Filter by model')
        @ns.param('include_archived', 'Include archived personas', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self):
            """List all personas."""
            role = request.args.get('role')
            model = request.args.get('model')
            include_archived = request.args.get('include_archived', 'false').lower() == 'true'

            if include_archived:
                personas = Persona.get_all()
            else:
                personas = Persona.get_active()

            if role:
                personas = [p for p in personas if p.role == role]
            if model:
                personas = [p for p in personas if p.model == model]

            return {
                'success': True,
                'msg': f'Found {len(personas)} personas',
                'data': {
                    'personas': [p.to_dict() for p in personas]
                }
            }

        @ns.doc('create_persona')
        @ns.expect(persona_create)
        @ns.marshal_with(response_model, code=201)
        def post(self):
            """Create a new persona."""
            data = request.json

            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400
            if not data.get('model'):
                return {'success': False, 'msg': 'model is required'}, 400
            if not data.get('role'):
                return {'success': False, 'msg': 'role is required'}, 400

            persona = Persona(
                name=data['name'],
                model=data['model'],
                role=data['role'],
                system_prompt=data.get('system_prompt'),
                personality=data.get('personality', {}),
                capabilities=data.get('capabilities', []),
                avatar_url=data.get('avatar_url'),
                color=data.get('color', '#d97757'),
                status='active'
            )

            try:
                persona.save()
                return {
                    'success': True,
                    'msg': 'Persona created',
                    'data': persona.to_dict(include_system_prompt=True)
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:persona_key>')
    @ns.param('persona_key', 'Persona identifier')
    class PersonaDetail(Resource):
        @ns.doc('get_persona')
        @ns.param('include_system_prompt', 'Include system prompt', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self, persona_key):
            """Get a persona by key."""
            include_prompt = request.args.get('include_system_prompt', 'false').lower() == 'true'

            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            return {
                'success': True,
                'msg': 'Persona retrieved',
                'data': persona.to_dict(include_system_prompt=include_prompt)
            }

        @ns.doc('update_persona')
        @ns.expect(persona_create)
        @ns.marshal_with(response_model)
        def put(self, persona_key):
            """Update a persona."""
            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            data = request.json
            persona.update_from_dict(data)

            try:
                persona.save()
                return {
                    'success': True,
                    'msg': 'Persona updated',
                    'data': persona.to_dict(include_system_prompt=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_persona')
        @ns.marshal_with(response_model)
        def delete(self, persona_key):
            """Archive a persona (soft delete)."""
            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            try:
                persona.archive()
                return {
                    'success': True,
                    'msg': 'Persona archived',
                    'data': persona.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:persona_key>/activate')
    @ns.param('persona_key', 'Persona identifier')
    class PersonaActivate(Resource):
        @ns.doc('activate_persona')
        @ns.marshal_with(response_model)
        def post(self, persona_key):
            """Reactivate an archived persona."""
            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            try:
                persona.activate()
                return {
                    'success': True,
                    'msg': 'Persona activated',
                    'data': persona.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
