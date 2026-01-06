"""
Collective Memory Platform - Agent Routes

Agent registration, status operations, and checkpointing.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Agent, AgentCheckpoint, Model, Persona, is_valid_client, get_client_affinities
from api.services.checkpoint import checkpoint_service
from api.services.activity import activity_service


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
        'agent_id': fields.String(required=True, description='Agent ID (e.g., claude-code-wayne-project)'),
        'client': fields.String(description='Client type: claude-code, claude-desktop, codex, gemini-cli'),
        'model_key': fields.String(description='Foreign key to model'),
        'persona_key': fields.String(description='Foreign key to persona'),
        'focus': fields.String(description='Current work focus'),
        'focus_updated_at': fields.DateTime(description='When focus was last updated'),
        'role': fields.String(description='Legacy role field (deprecated)'),
        'capabilities': fields.List(fields.String, description='Agent capabilities'),
        'status': fields.Raw(description='Current status as JSON'),
        'is_active': fields.Boolean(readonly=True, description='Whether agent is active'),
        'last_heartbeat': fields.DateTime(readonly=True),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    agent_register = ns.model('AgentRegister', {
        'agent_id': fields.String(required=True, description='Agent ID'),
        'client': fields.String(required=True, description='Client type: claude-code, claude-desktop, codex, gemini-cli'),
        'model_key': fields.String(description='Model key (optional)'),
        'persona_key': fields.String(description='Persona key (optional)'),
        'focus': fields.String(description='Current work focus'),
        'role': fields.String(description='Legacy role (deprecated, use persona_key)'),
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
        @ns.param('client', 'Filter by client type')
        @ns.param('persona_key', 'Filter by persona')
        @ns.param('role', 'Filter by role (legacy)')
        @ns.marshal_with(response_model)
        def get(self):
            """List all registered agents."""
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            client = request.args.get('client')
            persona_key = request.args.get('persona_key')
            role = request.args.get('role')

            if active_only:
                agents = Agent.get_active_agents()
            else:
                agents = Agent.get_all()

            if client:
                agents = [a for a in agents if a.client == client]
            if persona_key:
                agents = [a for a in agents if a.persona_key == persona_key]
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
            """Register a new agent or update existing.

            New registration protocol accepts:
            - agent_id (required): Unique agent identifier
            - client (required): Client type (claude-code, claude-desktop, codex, gemini-cli)
            - model_key: Reference to AI model being used
            - persona_key: Reference to behavioral persona
            - focus: Current work focus/description
            - role: Legacy field (deprecated, use persona_key)
            - capabilities: List of capabilities
            """
            data = request.json

            if not data.get('agent_id'):
                return {'success': False, 'msg': 'agent_id is required'}, 400

            # Validate client - REQUIRED
            client = data.get('client')
            if not client:
                return {
                    'success': False,
                    'msg': 'client is required. Valid options: claude-code, claude-desktop, codex, gemini-cli'
                }, 400
            if not is_valid_client(client):
                return {
                    'success': False,
                    'msg': f"Invalid client type: '{client}'. Valid options: claude-code, claude-desktop, codex, gemini-cli"
                }, 400

            # Validate model_key if provided
            model_key = data.get('model_key')
            if model_key:
                model = Model.get_by_key(model_key)
                if not model:
                    return {'success': False, 'msg': f"Model not found: '{model_key}'"}, 404

            # Validate persona_key if provided
            persona_key = data.get('persona_key')
            persona = None
            if persona_key:
                persona = Persona.get_by_key(persona_key)
                if not persona:
                    return {'success': False, 'msg': f"Persona not found: '{persona_key}'"}, 404

            # Check affinity warning
            affinity_warning = None
            if client and persona:
                suggested_clients = persona.suggested_clients or []
                if client not in suggested_clients:
                    affinity_roles = get_client_affinities(client)
                    affinity_warning = f"Persona '{persona.role}' is not typically used with client '{client}'. Suggested personas for {client}: {affinity_roles}"

            # Check if agent already exists
            existing = Agent.get_by_agent_id(data['agent_id'])

            if existing:
                # Update existing agent (reconnection)
                if client:
                    existing.client = client
                if model_key:
                    existing.model_key = model_key
                if persona_key:
                    existing.persona_key = persona_key
                if data.get('focus'):
                    existing.update_focus(data['focus'])
                if data.get('role'):
                    existing.role = data['role']
                if data.get('capabilities'):
                    existing.capabilities = data['capabilities']
                existing.update_heartbeat()
                existing.save()

                # Record reconnection activity
                activity_service.record_agent_registered(
                    actor=existing.agent_id,
                    agent_key=existing.agent_key,
                    client=existing.client,
                    persona=existing.persona_key,
                    model=existing.model_key,
                    is_reconnect=True
                )

                result = {
                    'success': True,
                    'msg': 'Agent updated',
                    'data': existing.to_dict()
                }
                if affinity_warning:
                    result['data']['affinity_warning'] = affinity_warning
                return result

            # Create new agent
            agent = Agent(
                agent_id=data['agent_id'],
                client=client,
                model_key=model_key,
                persona_key=persona_key,
                focus=data.get('focus'),
                role=data.get('role'),
                capabilities=data.get('capabilities', []),
                status={'progress': 'not_started'}
            )

            # Update focus timestamp if focus provided
            if data.get('focus'):
                from api.models.base import get_now
                agent.focus_updated_at = get_now()

            try:
                agent.save()
                # Record registration activity
                activity_service.record_agent_registered(
                    actor=agent.agent_id,
                    agent_key=agent.agent_key,
                    client=agent.client,
                    persona=agent.persona_key,
                    model=agent.model_key
                )
                result = {
                    'success': True,
                    'msg': 'Agent registered',
                    'data': agent.to_dict()
                }
                if affinity_warning:
                    result['data']['affinity_warning'] = affinity_warning
                return result, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:agent_key>')
    @ns.param('agent_key', 'Agent Key or Agent ID')
    class AgentDetail(Resource):
        @ns.doc('get_agent')
        @ns.marshal_with(response_model)
        def get(self, agent_key):
            """Get agent by key or agent_id."""
            # Try by key first, then by agent_id
            agent = Agent.get_by_key(agent_key)
            if not agent:
                agent = Agent.get_by_agent_id(agent_key)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            return {
                'success': True,
                'msg': 'Agent retrieved',
                'data': agent.to_dict()
            }

        @ns.doc('delete_agent')
        @ns.marshal_with(response_model)
        def delete(self, agent_key):
            """Delete an agent. Only inactive agents can be deleted."""
            # Try by key first, then by agent_id
            agent = Agent.get_by_key(agent_key)
            if not agent:
                agent = Agent.get_by_agent_id(agent_key)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            # Check if agent is active
            if agent.is_active:
                return {
                    'success': False,
                    'msg': 'Cannot delete an active agent. Wait for it to become inactive (15 min timeout).'
                }, 400

            agent_id = agent.agent_id
            try:
                agent.delete()
                return {
                    'success': True,
                    'msg': f'Agent {agent_id} deleted',
                    'data': {'agent_id': agent_id, 'agent_key': agent_key}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/inactive')
    class InactiveAgents(Resource):
        @ns.doc('delete_inactive_agents')
        @ns.marshal_with(response_model)
        def delete(self):
            """Delete all inactive agents."""
            all_agents = Agent.get_all()
            inactive_agents = [a for a in all_agents if not a.is_active]

            if not inactive_agents:
                return {
                    'success': True,
                    'msg': 'No inactive agents to delete',
                    'data': {'deleted_count': 0}
                }

            deleted = []
            errors = []
            for agent in inactive_agents:
                try:
                    deleted.append(agent.agent_id)
                    agent.delete()
                except Exception as e:
                    errors.append({'agent_id': agent.agent_id, 'error': str(e)})

            return {
                'success': True,
                'msg': f'Deleted {len(deleted)} inactive agents',
                'data': {
                    'deleted_count': len(deleted),
                    'deleted_agents': deleted,
                    'errors': errors if errors else None
                }
            }

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
            """Update agent heartbeat. Returns unread message count including autonomous tasks."""
            from api.models import Message

            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            try:
                agent.update_heartbeat()

                # Get unread message counts for this agent
                unread_count = Message.get_unread_count(agent_id=agent_id)
                autonomous_count = Message.get_unread_autonomous_count(agent_id=agent_id)

                # Record activity with message counts
                activity_service.record_agent_heartbeat(
                    actor=agent.agent_id,
                    agent_key=agent.agent_key,
                    status=agent.status.get('progress') if agent.status else None,
                    unread_messages=unread_count,
                    autonomous_tasks=autonomous_count
                )

                # Build response with message notification and focused mode info
                agent_data = agent.to_dict()
                agent_data['unread_messages'] = unread_count
                agent_data['autonomous_tasks'] = autonomous_count
                agent_data['recommended_heartbeat_seconds'] = 30 if agent.is_focused else 300

                # Build notification message
                if autonomous_count > 0:
                    msg = f'Heartbeat updated. 🚨 AUTONOMOUS TASK(S): You have {autonomous_count} autonomous task(s) waiting. These require your immediate attention - work on them and reply when complete. Use get_messages to see details.'
                elif unread_count > 0:
                    msg = f'Heartbeat updated. ACTION REQUIRED: You have {unread_count} unread message(s). Use get_messages to check them.'
                else:
                    msg = 'Heartbeat updated'

                # Add focused mode expiry warning
                if agent.is_focused and agent.focused_mode_expires_at:
                    from api.models.base import get_now
                    remaining = (agent.focused_mode_expires_at - get_now()).total_seconds() / 60
                    if remaining < 2:
                        msg += f' ⏱️ Focused mode expires in {remaining:.0f} minute(s).'

                return {
                    'success': True,
                    'msg': msg,
                    'data': agent_data
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    # Focus update model
    focus_update = ns.model('FocusUpdate', {
        'focus': fields.String(required=True, description='Current work focus description'),
    })

    @ns.route('/<string:agent_id>/focus')
    @ns.param('agent_id', 'Agent ID')
    class AgentFocus(Resource):
        @ns.doc('get_agent_focus')
        @ns.marshal_with(response_model)
        def get(self, agent_id):
            """Get agent's current focus."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            return {
                'success': True,
                'msg': 'Agent focus retrieved',
                'data': {
                    'agent_id': agent.agent_id,
                    'focus': agent.focus,
                    'focus_updated_at': agent.focus_updated_at.isoformat() if agent.focus_updated_at else None
                }
            }

        @ns.doc('update_agent_focus')
        @ns.expect(focus_update)
        @ns.marshal_with(response_model)
        def put(self, agent_id):
            """Update agent's current work focus. Send empty string to clear focus."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            data = request.json

            # Allow empty string to clear focus, but require the key to be present
            if 'focus' not in data:
                return {'success': False, 'msg': 'focus field is required (can be empty string to clear)'}, 400

            try:
                focus_value = data['focus'] or None  # Convert empty string to None for storage
                agent.update_focus(focus_value)
                return {
                    'success': True,
                    'msg': 'Focus cleared' if not focus_value else 'Focus updated',
                    'data': agent.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    # Focused mode model
    focused_mode_update = ns.model('FocusedModeUpdate', {
        'enabled': fields.Boolean(required=True, description='Enable or disable focused mode'),
        'duration_minutes': fields.Integer(description='Duration in minutes (default 10)', default=10),
    })

    @ns.route('/<string:agent_id>/focused-mode')
    @ns.param('agent_id', 'Agent ID')
    class AgentFocusedMode(Resource):
        @ns.doc('get_focused_mode')
        @ns.marshal_with(response_model)
        def get(self, agent_id):
            """Get agent's focused mode status."""
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            return {
                'success': True,
                'msg': 'Focused mode status retrieved',
                'data': {
                    'agent_id': agent.agent_id,
                    'focused_mode': agent.focused_mode,
                    'is_focused': agent.is_focused,
                    'focused_mode_expires_at': agent.focused_mode_expires_at.isoformat() if agent.focused_mode_expires_at else None,
                    'recommended_heartbeat_seconds': 30 if agent.is_focused else 300
                }
            }

        @ns.doc('set_focused_mode')
        @ns.expect(focused_mode_update)
        @ns.marshal_with(response_model)
        def put(self, agent_id):
            """
            Set focused mode for fast heartbeats.

            When enabled, the agent signals it's actively waiting for a response.
            Heartbeat interval should be reduced (30 seconds vs 5 minutes).
            Focused mode auto-expires after duration_minutes (default 10).
            """
            agent = Agent.get_by_agent_id(agent_id)
            if not agent:
                return {'success': False, 'msg': 'Agent not found'}, 404

            data = request.json

            if 'enabled' not in data:
                return {'success': False, 'msg': 'enabled field is required'}, 400

            try:
                enabled = data['enabled']
                duration = data.get('duration_minutes', 10)
                agent.set_focused_mode(enabled, duration)

                if enabled:
                    msg = f'Focused mode enabled for {duration} minutes. Use 30-second heartbeat interval.'
                else:
                    msg = 'Focused mode disabled. Resume normal 5-minute heartbeat interval.'

                return {
                    'success': True,
                    'msg': msg,
                    'data': {
                        'agent_id': agent.agent_id,
                        'focused_mode': agent.focused_mode,
                        'is_focused': agent.is_focused,
                        'focused_mode_expires_at': agent.focused_mode_expires_at.isoformat() if agent.focused_mode_expires_at else None,
                        'recommended_heartbeat_seconds': 30 if agent.is_focused else 300
                    }
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
