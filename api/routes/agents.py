"""
Collective Memory Platform - Agent Routes

Agent registration and status operations.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Agent


def register_agent_routes(api: Api):
    """Register agent routes with the API."""

    ns = api.namespace(
        'agents',
        description='Agent registration and coordination',
        path='/agents'
    )

    # Define models for OpenAPI documentation
    agent_model = ns.model('Agent', {
        'agent_key': fields.String(readonly=True, description='Unique agent identifier'),
        'agent_id': fields.String(required=True, description='Agent ID (e.g., backend-code)'),
        'role': fields.String(required=True, description='Agent role'),
        'capabilities': fields.List(fields.String, description='Agent capabilities'),
        'status': fields.Raw(description='Current status as JSON'),
        'is_active': fields.Boolean(readonly=True, description='Whether agent is active'),
        'last_heartbeat': fields.DateTime(readonly=True),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    agent_register = ns.model('AgentRegister', {
        'agent_id': fields.String(required=True, description='Agent ID'),
        'role': fields.String(required=True, description='Agent role'),
        'capabilities': fields.List(fields.String, description='Agent capabilities'),
    })

    status_update = ns.model('StatusUpdate', {
        'current_task': fields.String(description='Current task description'),
        'progress': fields.String(description='Progress: not_started, in_progress, blocked, completed'),
        'blocker': fields.String(description='Description of blocker if any'),
        'recent_actions': fields.List(fields.String, description='List of recent actions'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class AgentList(Resource):
        @ns.doc('list_agents')
        @ns.param('active_only', 'Only return active agents', type=bool, default=False)
        @ns.param('role', 'Filter by role')
        @ns.marshal_with(response_model)
        def get(self):
            """List all registered agents."""
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            role = request.args.get('role')

            if active_only:
                agents = Agent.get_active_agents()
            else:
                agents = Agent.get_all()

            if role:
                agents = [a for a in agents if a.role == role]

            return {
                'success': True,
                'msg': f'Found {len(agents)} agents',
                'data': {
                    'agents': [a.to_dict() for a in agents]
                }
            }

    @ns.route('/register')
    class AgentRegister(Resource):
        @ns.doc('register_agent')
        @ns.expect(agent_register)
        @ns.marshal_with(response_model, code=201)
        def post(self):
            """Register a new agent or update existing."""
            data = request.json

            if not data.get('agent_id'):
                return {'success': False, 'msg': 'agent_id is required'}, 400
            if not data.get('role'):
                return {'success': False, 'msg': 'role is required'}, 400

            # Check if agent already exists
            existing = Agent.get_by_agent_id(data['agent_id'])

            if existing:
                # Update existing agent
                existing.role = data['role']
                existing.capabilities = data.get('capabilities', [])
                existing.update_heartbeat()
                existing.save()

                return {
                    'success': True,
                    'msg': 'Agent updated',
                    'data': existing.to_dict()
                }

            # Create new agent
            agent = Agent(
                agent_id=data['agent_id'],
                role=data['role'],
                capabilities=data.get('capabilities', []),
                status={'progress': 'not_started'}
            )

            try:
                agent.save()
                return {
                    'success': True,
                    'msg': 'Agent registered',
                    'data': agent.to_dict()
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:agent_id>/status')
    @ns.param('agent_id', 'Agent ID')
    class AgentStatus(Resource):
        @ns.doc('get_agent_status')
        @ns.marshal_with(response_model)
        def get(self, agent_id):
            """Get agent status."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            return {
                'success': True,
                'msg': 'Agent status retrieved',
                'data': agent.to_dict()
            }

        @ns.doc('update_agent_status')
        @ns.expect(status_update)
        @ns.marshal_with(response_model)
        def put(self, agent_id):
            """Update agent status."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            data = request.json

            try:
                agent.update_status(data)
                return {
                    'success': True,
                    'msg': 'Agent status updated',
                    'data': agent.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:agent_id>/heartbeat')
    @ns.param('agent_id', 'Agent ID')
    class AgentHeartbeat(Resource):
        @ns.doc('agent_heartbeat')
        @ns.marshal_with(response_model)
        def post(self, agent_id):
            """Update agent heartbeat."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            try:
                agent.update_heartbeat()
                return {
                    'success': True,
                    'msg': 'Heartbeat updated',
                    'data': agent.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
