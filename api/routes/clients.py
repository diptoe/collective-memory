"""
Collective Memory Platform - Client Routes

Routes for Client CRUD operations.
Clients represent connecting platforms (Claude Code, Cursor, etc.)
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import (
    Client, Model, Persona,
    get_client_types, get_client_affinities, is_valid_client
)
from api.services.auth import require_auth


def register_client_routes(api: Api):
    """Register client routes with the API."""

    ns = api.namespace(
        'clients',
        description='Client operations',
        path='/clients'
    )

    # Define models for OpenAPI documentation
    client_schema = ns.model('Client', {
        'client_key': fields.String(description='Client key (primary key)'),
        'name': fields.String(description='Client display name'),
        'description': fields.String(description='Client description'),
        'publisher': fields.String(description='Publisher/vendor name'),
        'entity_key': fields.String(description='Linked knowledge graph entity key'),
        'status': fields.String(description='Status: active, deprecated'),
        'extra_data': fields.Raw(description='Additional data (icon, website, etc.)'),
        'created_at': fields.DateTime(description='Created timestamp'),
        'updated_at': fields.DateTime(description='Last updated timestamp'),
        'models_count': fields.Integer(description='Number of linked models'),
        'personas_count': fields.Integer(description='Number of linked personas'),
    })

    client_create_schema = ns.model('ClientCreate', {
        'client_key': fields.String(required=True, description='Client key (e.g., client-claude-code)'),
        'name': fields.String(required=True, description='Client display name'),
        'description': fields.String(description='Client description'),
        'publisher': fields.String(description='Publisher/vendor name'),
        'extra_data': fields.Raw(description='Additional data'),
    })

    client_update_schema = ns.model('ClientUpdate', {
        'name': fields.String(description='Client display name'),
        'description': fields.String(description='Client description'),
        'publisher': fields.String(description='Publisher/vendor name'),
        'status': fields.String(description='Status: active, deprecated'),
        'extra_data': fields.Raw(description='Additional data'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    # Legacy compatibility model
    client_type_schema = ns.model('ClientType', {
        'value': fields.String(description='Client type value'),
        'name': fields.String(description='Human-readable name'),
        'description': fields.String(description='Description'),
        'suggested_personas': fields.List(fields.String, description='Suggested persona roles'),
    })

    @ns.route('')
    class ClientList(Resource):
        @ns.doc('list_clients')
        @ns.marshal_with(response_model)
        def get(self):
            """List all clients.

            Query params:
            - status: Filter by status (active, deprecated)
            - include_counts: Include models/personas counts (default: true)
            - legacy: Return legacy enum format (default: false)
            """
            legacy = request.args.get('legacy', 'false').lower() == 'true'

            # Return legacy enum format if requested
            if legacy:
                clients = get_client_types()
                return {
                    'success': True,
                    'msg': f'Found {len(clients)} client types (legacy)',
                    'data': {'clients': clients}
                }

            # New model-based clients
            status = request.args.get('status')
            include_counts = request.args.get('include_counts', 'true').lower() == 'true'

            if status:
                clients = Client.query.filter_by(status=status).all()
            else:
                clients = Client.get_all()

            return {
                'success': True,
                'msg': f'Found {len(clients)} clients',
                'data': {
                    'clients': [c.to_dict(include_counts=include_counts) for c in clients]
                }
            }

        @ns.doc('create_client')
        @ns.expect(client_create_schema)
        @ns.marshal_with(response_model)
        @require_auth
        def post(self):
            """Create a new client."""
            data = request.get_json()

            # Validate required fields
            if not data.get('client_key'):
                return {'success': False, 'msg': 'client_key is required'}, 400
            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400

            # Check if client already exists
            existing = Client.get_by_key(data['client_key'])
            if existing:
                return {'success': False, 'msg': f"Client '{data['client_key']}' already exists"}, 409

            # Create client
            client = Client.create(
                client_key=data['client_key'],
                name=data['name'],
                description=data.get('description'),
                publisher=data.get('publisher'),
                extra_data=data.get('extra_data'),
            )

            return {
                'success': True,
                'msg': f'Client created: {client.name}',
                'data': client.to_dict(include_counts=True)
            }, 201

    @ns.route('/seed')
    class ClientSeed(Resource):
        @ns.doc('seed_clients')
        @ns.marshal_with(response_model)
        @require_auth
        def post(self):
            """Seed default clients.

            Creates default clients if they don't exist.
            Safe to call multiple times - will skip existing clients.
            """
            clients = Client.seed_defaults()

            return {
                'success': True,
                'msg': f'Seeded {len(clients)} clients',
                'data': {
                    'clients': [c.to_dict(include_counts=True) for c in clients]
                }
            }

    @ns.route('/<string:key>')
    @ns.param('key', 'Client key (e.g., client-claude-code or claude-code for legacy)')
    class ClientDetail(Resource):
        @ns.doc('get_client')
        @ns.marshal_with(response_model)
        def get(self, key):
            """Get a specific client by key.

            Supports both new format (client-claude-code) and legacy format (claude-code).
            """
            # Try new model first
            client = Client.get_by_key(key)

            # Try with client- prefix
            if not client and not key.startswith('client-'):
                client = Client.get_by_key(f'client-{key}')

            if client:
                return {
                    'success': True,
                    'msg': 'Client retrieved',
                    'data': client.to_dict(include_counts=True)
                }

            # Fall back to legacy enum
            if is_valid_client(key):
                clients = get_client_types()
                client_info = next((c for c in clients if c['value'] == key), None)
                if client_info:
                    return {
                        'success': True,
                        'msg': 'Client type retrieved (legacy)',
                        'data': client_info
                    }

            return {'success': False, 'msg': f"Client not found: '{key}'"}, 404

        @ns.doc('update_client')
        @ns.expect(client_update_schema)
        @ns.marshal_with(response_model)
        @require_auth
        def put(self, key):
            """Update a client."""
            client = Client.get_by_key(key)
            if not client and not key.startswith('client-'):
                client = Client.get_by_key(f'client-{key}')

            if not client:
                return {'success': False, 'msg': f"Client not found: '{key}'"}, 404

            data = request.get_json()

            # Update fields
            if 'name' in data:
                client.name = data['name']
            if 'description' in data:
                client.description = data['description']
            if 'publisher' in data:
                client.publisher = data['publisher']
            if 'status' in data:
                if data['status'] not in ('active', 'deprecated'):
                    return {'success': False, 'msg': 'status must be active or deprecated'}, 400
                client.status = data['status']
            if 'extra_data' in data:
                client.extra_data = data['extra_data']

            client.save()

            return {
                'success': True,
                'msg': f'Client updated: {client.name}',
                'data': client.to_dict(include_counts=True)
            }

        @ns.doc('delete_client')
        @ns.marshal_with(response_model)
        @require_auth
        def delete(self, key):
            """Archive a client (soft delete).

            Sets status to 'deprecated' instead of deleting.
            """
            client = Client.get_by_key(key)
            if not client and not key.startswith('client-'):
                client = Client.get_by_key(f'client-{key}')

            if not client:
                return {'success': False, 'msg': f"Client not found: '{key}'"}, 404

            client.status = 'deprecated'
            client.save()

            return {
                'success': True,
                'msg': f'Client archived: {client.name}',
                'data': client.to_dict(include_counts=True)
            }

    @ns.route('/<string:key>/models')
    @ns.param('key', 'Client key')
    class ClientModels(Resource):
        @ns.doc('get_client_models')
        @ns.marshal_with(response_model)
        def get(self, key):
            """Get models linked to a client."""
            client = Client.get_by_key(key)
            if not client and not key.startswith('client-'):
                client = Client.get_by_key(f'client-{key}')

            if not client:
                return {'success': False, 'msg': f"Client not found: '{key}'"}, 404

            models = list(client.models)

            return {
                'success': True,
                'msg': f'Found {len(models)} models for client {client.name}',
                'data': {
                    'client_key': client.client_key,
                    'models': [m.to_dict() for m in models]
                }
            }

    @ns.route('/<string:key>/personas')
    @ns.param('key', 'Client key')
    class ClientPersonas(Resource):
        @ns.doc('get_client_personas')
        @ns.marshal_with(response_model)
        def get(self, key):
            """Get personas linked to a client.

            Returns:
            - personas: Personas with client_key matching this client
            - suggested_personas: Personas from suggested_clients list (legacy)
            - affinity_roles: Roles from affinity mapping (legacy)
            """
            # Try new model
            client = Client.get_by_key(key)
            if not client and not key.startswith('client-'):
                client = Client.get_by_key(f'client-{key}')

            if client:
                # Get personas linked via FK
                linked_personas = list(client.personas)

                # Also get personas with this client in suggested_clients (legacy)
                client_type = key.replace('client-', '') if key.startswith('client-') else key
                suggested_personas = Persona.get_by_client(client_type)

                # Get affinity roles
                affinity_roles = client.get_suggested_personas()

                # Combine without duplicates
                all_personas = {p.persona_key: p for p in linked_personas}
                for p in suggested_personas:
                    if p.persona_key not in all_personas:
                        all_personas[p.persona_key] = p

                return {
                    'success': True,
                    'msg': f'Found {len(all_personas)} personas for client {client.name}',
                    'data': {
                        'client_key': client.client_key,
                        'personas': [p.to_dict() for p in all_personas.values()],
                        'affinity_roles': affinity_roles
                    }
                }

            # Fall back to legacy
            if is_valid_client(key):
                personas = Persona.get_by_client(key)
                affinity_roles = get_client_affinities(key)

                return {
                    'success': True,
                    'msg': f'Found {len(personas)} suggested personas for {key}',
                    'data': {
                        'client': key,
                        'personas': [p.to_dict() for p in personas],
                        'affinity_roles': affinity_roles
                    }
                }

            return {'success': False, 'msg': f"Client not found: '{key}'"}, 404

    @ns.route('/<string:key>/entity')
    @ns.param('key', 'Client key')
    class ClientEntity(Resource):
        @ns.doc('ensure_client_entity')
        @ns.marshal_with(response_model)
        @require_auth
        def post(self, key):
            """Ensure a system-scoped Entity exists for this client.

            Creates or updates the knowledge graph entity for the client.
            Uses strong link pattern: entity_key = client_key.
            """
            client = Client.get_by_key(key)
            if not client and not key.startswith('client-'):
                client = Client.get_by_key(f'client-{key}')

            if not client:
                return {'success': False, 'msg': f"Client not found: '{key}'"}, 404

            entity_key = client.ensure_entity()

            return {
                'success': True,
                'msg': f'Entity ensured for client {client.name}',
                'data': {
                    'client_key': client.client_key,
                    'entity_key': entity_key
                }
            }
