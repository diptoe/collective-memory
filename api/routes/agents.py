"""
Collective Memory Platform - Agent Routes

Agent registration, status operations, and checkpointing.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Agent, AgentCheckpoint
from api.services.checkpoint import checkpoint_service


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

    # Checkpoint models
    checkpoint_model = ns.model('Checkpoint', {
        'checkpoint_key': fields.String(readonly=True, description='Unique checkpoint identifier'),
        'agent_key': fields.String(description='Agent key'),
        'checkpoint_type': fields.String(description='Type: manual, auto, error, milestone'),
        'name': fields.String(description='Checkpoint name'),
        'description': fields.String(description='Checkpoint description'),
        'conversation_keys': fields.List(fields.String, description='Associated conversation keys'),
        'extra_data': fields.Raw(description='Additional context data'),
        'created_at': fields.DateTime(readonly=True),
    })

    checkpoint_create = ns.model('CheckpointCreate', {
        'checkpoint_type': fields.String(default='manual', description='Type: manual, auto, error, milestone'),
        'name': fields.String(description='Checkpoint name'),
        'description': fields.String(description='Optional description'),
        'include_conversations': fields.Boolean(default=True, description='Include conversation references'),
    })

    checkpoint_restore = ns.model('CheckpointRestore', {
        'restore_status': fields.Boolean(default=True, description='Restore agent status from checkpoint'),
    })

    @ns.route('/<string:agent_id>/checkpoints')
    @ns.param('agent_id', 'Agent ID')
    class AgentCheckpoints(Resource):
        @ns.doc('list_checkpoints')
        @ns.param('limit', 'Maximum number of checkpoints', type=int, default=10)
        @ns.param('checkpoint_type', 'Filter by checkpoint type')
        @ns.marshal_with(response_model)
        def get(self, agent_id):
            """List checkpoints for an agent."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            limit = request.args.get('limit', 10, type=int)
            checkpoint_type = request.args.get('checkpoint_type')

            checkpoints = checkpoint_service.get_checkpoints(
                agent_key=agent.agent_key,
                limit=limit,
                checkpoint_type=checkpoint_type,
            )

            return {
                'success': True,
                'msg': f'Found {len(checkpoints)} checkpoints',
                'data': {
                    'checkpoints': [c.to_dict() for c in checkpoints]
                }
            }

        @ns.doc('create_checkpoint')
        @ns.expect(checkpoint_create)
        @ns.marshal_with(response_model, code=201)
        def post(self, agent_id):
            """Create a new checkpoint for an agent."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            data = request.json or {}

            try:
                checkpoint = checkpoint_service.create_checkpoint(
                    agent_key=agent.agent_key,
                    checkpoint_type=data.get('checkpoint_type', 'manual'),
                    name=data.get('name'),
                    description=data.get('description'),
                    include_conversations=data.get('include_conversations', True),
                )

                if not checkpoint:
                    return {'success': False, 'msg': 'Failed to create checkpoint'}, 500

                return {
                    'success': True,
                    'msg': 'Checkpoint created',
                    'data': checkpoint.to_dict()
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:agent_id>/checkpoints/<string:checkpoint_key>')
    @ns.param('agent_id', 'Agent ID')
    @ns.param('checkpoint_key', 'Checkpoint key')
    class AgentCheckpointDetail(Resource):
        @ns.doc('get_checkpoint')
        @ns.param('include_state', 'Include full state data', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self, agent_id, checkpoint_key):
            """Get a specific checkpoint."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            checkpoint = AgentCheckpoint.get_by_key(checkpoint_key)
            if not checkpoint or checkpoint.agent_key != agent.agent_key:
                return {'success': False, 'msg': 'Checkpoint not found'}, 404

            include_state = request.args.get('include_state', 'false').lower() == 'true'

            return {
                'success': True,
                'msg': 'Checkpoint retrieved',
                'data': checkpoint.to_dict(include_state=include_state)
            }

        @ns.doc('delete_checkpoint')
        @ns.marshal_with(response_model)
        def delete(self, agent_id, checkpoint_key):
            """Delete a checkpoint."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            checkpoint = AgentCheckpoint.get_by_key(checkpoint_key)
            if not checkpoint or checkpoint.agent_key != agent.agent_key:
                return {'success': False, 'msg': 'Checkpoint not found'}, 404

            try:
                checkpoint.delete()
                return {
                    'success': True,
                    'msg': 'Checkpoint deleted',
                    'data': None
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:agent_id>/restore/<string:checkpoint_key>')
    @ns.param('agent_id', 'Agent ID')
    @ns.param('checkpoint_key', 'Checkpoint key to restore from')
    class AgentRestore(Resource):
        @ns.doc('restore_checkpoint')
        @ns.expect(checkpoint_restore)
        @ns.marshal_with(response_model)
        def post(self, agent_id, checkpoint_key):
            """Restore an agent to a checkpoint state."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            checkpoint = AgentCheckpoint.get_by_key(checkpoint_key)
            if not checkpoint or checkpoint.agent_key != agent.agent_key:
                return {'success': False, 'msg': 'Checkpoint not found'}, 404

            data = request.json or {}

            try:
                success = checkpoint_service.restore_checkpoint(
                    agent_key=agent.agent_key,
                    checkpoint_key=checkpoint_key,
                    restore_status=data.get('restore_status', True),
                )

                if not success:
                    return {'success': False, 'msg': 'Failed to restore checkpoint'}, 500

                # Get updated agent
                agent = Agent.get_by_agent_id(agent_id)

                return {
                    'success': True,
                    'msg': f'Agent restored to checkpoint: {checkpoint.name}',
                    'data': {
                        'agent': agent.to_dict(),
                        'restored_from': checkpoint.to_dict()
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
