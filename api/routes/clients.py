"""
Collective Memory Platform - Client Routes

Routes for client types and persona affinities.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import get_client_types, get_client_affinities, is_valid_client, Persona


def register_client_routes(api: Api):
    """Register client routes with the API."""

    ns = api.namespace(
        'clients',
        description='Client type operations',
        path='/clients'
    )

    # Define models for OpenAPI documentation
    client_type_schema = ns.model('ClientType', {
        'value': fields.String(description='Client type value'),
        'name': fields.String(description='Human-readable name'),
        'description': fields.String(description='Description'),
        'suggested_personas': fields.List(fields.String, description='Suggested persona roles'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class ClientList(Resource):
        @ns.doc('list_clients')
        @ns.marshal_with(response_model)
        def get(self):
            """List all client types with their persona affinities."""
            clients = get_client_types()

            return {
                'success': True,
                'msg': f'Found {len(clients)} client types',
                'data': {
                    'clients': clients
                }
            }

    @ns.route('/<string:client>')
    @ns.param('client', 'Client type (claude-code, claude-desktop, codex, gemini-cli, cursor)')
    class ClientDetail(Resource):
        @ns.doc('get_client')
        @ns.marshal_with(response_model)
        def get(self, client):
            """Get details for a specific client type."""
            if not is_valid_client(client):
                return {'success': False, 'msg': f"Invalid client type: '{client}'"}, 400

            clients = get_client_types()
            client_info = next((c for c in clients if c['value'] == client), None)

            return {
                'success': True,
                'msg': 'Client type retrieved',
                'data': client_info
            }

    @ns.route('/<string:client>/personas')
    @ns.param('client', 'Client type')
    class ClientPersonas(Resource):
        @ns.doc('get_client_personas')
        @ns.marshal_with(response_model)
        def get(self, client):
            """Get suggested personas for a client type.

            Returns personas that have this client in their suggested_clients list,
            as well as personas from the affinity mapping.
            """
            if not is_valid_client(client):
                return {'success': False, 'msg': f"Invalid client type: '{client}'"}, 400

            # Get personas that suggest this client
            personas = Persona.get_by_client(client)

            # Also get from affinity mapping as fallback
            affinity_roles = get_client_affinities(client)

            return {
                'success': True,
                'msg': f'Found {len(personas)} suggested personas for {client}',
                'data': {
                    'client': client,
                    'personas': [p.to_dict() for p in personas],
                    'affinity_roles': affinity_roles
                }
            }
