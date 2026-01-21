"""
Collective Memory Platform - Persona Routes

CRUD operations for AI personas (behavioral roles, decoupled from models).
Persona modifications require system admin role.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Persona, Client, is_valid_client
from api.services.auth import require_admin


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
        'role': fields.String(required=True, description='Persona role (unique identifier)'),
        'system_prompt': fields.String(description='System prompt for the persona'),
        'personality': fields.Raw(description='Personality traits as JSON'),
        'capabilities': fields.List(fields.String, description='Persona capabilities'),
        'suggested_clients': fields.List(fields.String, description='Suggested client types (deprecated)'),
        'client_key': fields.String(description='Linked client key'),
        'avatar_url': fields.String(description='Avatar image URL'),
        'color': fields.String(description='Theme color (hex)'),
        'status': fields.String(description='Status: active, inactive, archived'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    persona_create = ns.model('PersonaCreate', {
        'name': fields.String(required=True, description='Persona display name'),
        'role': fields.String(required=True, description='Persona role (unique identifier)'),
        'system_prompt': fields.String(description='System prompt'),
        'personality': fields.Raw(description='Personality traits'),
        'capabilities': fields.List(fields.String, description='Capabilities'),
        'suggested_clients': fields.List(fields.String, description='Suggested client types (deprecated)'),
        'client_key': fields.String(description='Linked client key (e.g., client-claude-code)'),
        'avatar_url': fields.String(description='Avatar URL'),
        'color': fields.String(description='Theme color', default='#d97757'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    def _expand_persona(persona: Persona, include_system_prompt: bool = False) -> dict:
        """Expand persona to include client info."""
        data = persona.to_dict(include_system_prompt=include_system_prompt)
        if persona.client_key and persona.client:
            data['client'] = {
                'client_key': persona.client.client_key,
                'name': persona.client.name,
                'publisher': persona.client.publisher,
            }
        return data

    @ns.route('')
    class PersonaList(Resource):
        @ns.doc('list_personas')
        @ns.param('role', 'Filter by role')
        @ns.param('client', 'Filter by suggested client type (legacy)')
        @ns.param('client_key', 'Filter by client key')
        @ns.param('include_archived', 'Include archived personas', type=bool, default=False)
        @ns.param('expand', 'Include related objects (client)', type=bool, default=True)
        @ns.marshal_with(response_model)
        def get(self):
            """List all personas."""
            role = request.args.get('role')
            client = request.args.get('client')  # Legacy filter
            client_key = request.args.get('client_key')
            include_archived = request.args.get('include_archived', 'false').lower() == 'true'
            expand = request.args.get('expand', 'true').lower() == 'true'

            if include_archived:
                personas = Persona.get_all()
            else:
                personas = Persona.get_active()

            if role:
                personas = [p for p in personas if p.role == role]
            if client:
                # Legacy: filter by suggested_clients list
                personas = [p for p in personas if client in (p.suggested_clients or [])]
            if client_key:
                # New: filter by client_key FK
                if not client_key.startswith('client-'):
                    client_key = f'client-{client_key}'
                personas = [p for p in personas if p.client_key == client_key]

            return {
                'success': True,
                'msg': f'Found {len(personas)} personas',
                'data': {
                    'personas': [_expand_persona(p) if expand else p.to_dict() for p in personas]
                }
            }

        @ns.doc('create_persona')
        @ns.expect(persona_create)
        @ns.marshal_with(response_model, code=201)
        @require_admin
        def post(self):
            """Create a new persona. Requires admin role."""
            data = request.json

            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400
            if not data.get('role'):
                return {'success': False, 'msg': 'role is required'}, 400

            # Validate suggested_clients if provided (legacy)
            suggested_clients = data.get('suggested_clients', [])
            for client in suggested_clients:
                if not is_valid_client(client):
                    return {'success': False, 'msg': f"Invalid client type: '{client}'"}, 400

            # Validate client_key if provided (new way)
            client_key = data.get('client_key')
            if client_key:
                if not client_key.startswith('client-'):
                    client_key = f'client-{client_key}'
                client = Client.get_by_key(client_key)
                if not client:
                    return {'success': False, 'msg': f"Client not found: '{client_key}'"}, 400

            # Check for duplicate role
            existing = Persona.get_by_role(data['role'])
            if existing:
                return {'success': False, 'msg': f"Persona with role '{data['role']}' already exists"}, 400

            persona = Persona(
                name=data['name'],
                role=data['role'],
                system_prompt=data.get('system_prompt'),
                personality=data.get('personality', {}),
                capabilities=data.get('capabilities', []),
                suggested_clients=suggested_clients,
                client_key=client_key,
                avatar_url=data.get('avatar_url'),
                color=data.get('color', '#d97757'),
                status='active'
            )

            try:
                persona.save()
                return {
                    'success': True,
                    'msg': 'Persona created',
                    'data': _expand_persona(persona, include_system_prompt=True)
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
                'data': _expand_persona(persona, include_system_prompt=include_prompt)
            }

        @ns.doc('update_persona')
        @ns.expect(persona_create)
        @ns.marshal_with(response_model)
        @require_admin
        def put(self, persona_key):
            """Update a persona. Requires admin role."""
            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            data = request.json

            # Validate client_key if provided
            if 'client_key' in data:
                client_key = data['client_key']
                if client_key:
                    if not client_key.startswith('client-'):
                        client_key = f'client-{client_key}'
                    client = Client.get_by_key(client_key)
                    if not client:
                        return {'success': False, 'msg': f"Client not found: '{client_key}'"}, 400
                    data['client_key'] = client_key

            persona.update_from_dict(data)

            try:
                persona.save()
                return {
                    'success': True,
                    'msg': 'Persona updated',
                    'data': _expand_persona(persona, include_system_prompt=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_persona')
        @ns.marshal_with(response_model)
        @require_admin
        def delete(self, persona_key):
            """Archive a persona (soft delete). Requires admin role."""
            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            try:
                persona.archive()
                return {
                    'success': True,
                    'msg': 'Persona archived',
                    'data': _expand_persona(persona)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:persona_key>/activate')
    @ns.param('persona_key', 'Persona identifier')
    class PersonaActivate(Resource):
        @ns.doc('activate_persona')
        @ns.marshal_with(response_model)
        @require_admin
        def post(self, persona_key):
            """Reactivate an archived persona. Requires admin role."""
            persona = Persona.get_by_key(persona_key)
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            try:
                persona.activate()
                return {
                    'success': True,
                    'msg': 'Persona activated',
                    'data': _expand_persona(persona)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/by-role/<string:role>')
    @ns.param('role', 'Persona role')
    class PersonaByRole(Resource):
        @ns.doc('get_persona_by_role')
        @ns.param('include_system_prompt', 'Include system prompt', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self, role):
            """Get a persona by its role (unique identifier)."""
            include_prompt = request.args.get('include_system_prompt', 'false').lower() == 'true'

            personas = Persona.get_by_role(role)
            if not personas:
                return {'success': False, 'msg': f"Persona with role '{role}' not found"}, 404

            # get_by_role returns a list, but role is unique so we take first
            persona = personas[0]

            return {
                'success': True,
                'msg': 'Persona retrieved',
                'data': _expand_persona(persona, include_system_prompt=include_prompt)
            }
