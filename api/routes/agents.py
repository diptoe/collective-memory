"""
Collective Memory Platform - Agent Routes

Agent registration, status operations, and checkpointing.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Agent, AgentCheckpoint, Model, Persona, Session, Team, is_valid_client, get_client_affinities
from api.services.checkpoint import checkpoint_service
from api.services.activity import activity_service
from api.services.auth import require_auth


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for activity tracking."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key for activity tracking."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


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
        'client': fields.String(description='Client type: claude-code, claude-desktop, codex, gemini-cli, cursor'),
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
        'client': fields.String(required=True, description='Client type: claude-code, claude-desktop, codex, gemini-cli, cursor'),
        'model_key': fields.String(description='Model key (optional)'),
        'persona_key': fields.String(description='Persona key (optional)'),
        'focus': fields.String(description='Current work focus'),
        'role': fields.String(description='Legacy role (deprecated, use persona_key)'),
        'capabilities': fields.List(fields.String, description='Agent capabilities'),
        # Team and project association
        'team_key': fields.String(description='Team key for team-scoped agents (optional)'),
        'project_key': fields.String(description='Project/Repository entity key (optional)'),
        'project_name': fields.String(description='Project/Repository name (optional)'),
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
        @require_auth
        def get(self):
            """List agents owned by the authenticated user."""
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            client = request.args.get('client')
            persona_key = request.args.get('persona_key')
            role = request.args.get('role')

            # Filter by user's agents only
            user_key = g.current_user.user_key if g.current_user else None

            if user_key:
                if active_only:
                    agents = Agent.get_active_by_user(user_key)
                else:
                    agents = Agent.get_by_user_key(user_key)
            else:
                # No user context (shouldn't happen with require_auth)
                agents = []

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
        @require_auth
        def post(self):
            """Register a new agent or update existing.

            Authentication is required - agents are linked to the authenticated user.
            Use a Personal Access Token (PAT) for authentication.

            New registration protocol accepts:
            - agent_id (required): Unique agent identifier
            - client (required): Client type (claude-code, claude-desktop, codex, gemini-cli, cursor)
            - model_key: Reference to AI model being used
            - persona_key: Reference to behavioral persona
            - focus: Current work focus/description
            - role: Legacy field (deprecated, use persona_key)
            - capabilities: List of capabilities
            """
            data = request.json

            if not data.get('agent_id'):
                return {'success': False, 'msg': 'agent_id is required'}, 400

            # Get the authenticated user
            user_key = g.current_user.user_key if g.current_user else None
            if not user_key:
                return {'success': False, 'msg': 'Authentication required to register agents'}, 401

            # Validate client - REQUIRED
            client = data.get('client')
            if not client:
                return {
                    'success': False,
                    'msg': 'client is required. Valid options: claude-code, claude-desktop, codex, gemini-cli, cursor'
                }, 400
            if not is_valid_client(client):
                return {
                    'success': False,
                    'msg': f"Invalid client type: '{client}'. Valid options: claude-code, claude-desktop, codex, gemini-cli, cursor"
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

            # Get user info for initials suffix and denormalization
            user = g.current_user
            user_initials = user.initials.lower() if user and user.initials else None
            user_name = user.display_name if user else None

            # Resolve team_key and get team_name FIRST (needed for membership_slug)
            team_key = data.get('team_key')
            team_name = None
            if team_key:
                team = Team.get_by_key(team_key)
                if team:
                    team_name = team.name
                else:
                    return {'success': False, 'msg': f"Team not found: '{team_key}'"}, 404

            # Get membership slug for the active team (if applicable)
            membership_slug = None
            if team_key and user:
                from api.models.team import TeamMembership
                membership = TeamMembership.get_user_membership(user.user_key, team_key)
                if membership:
                    # Use existing slug or generate from initials
                    membership_slug = membership.slug or membership.ensure_slug()

            # Use membership_slug if available, otherwise fall back to user_initials
            suffix = membership_slug or user_initials

            # Auto-suffix agent_id with suffix if not already present
            agent_id = data['agent_id']
            if suffix:
                # Check if agent_id already ends with suffix
                if not agent_id.endswith(f'-{suffix}'):
                    # Check if already has short alphanumeric suffix that we should replace
                    parts = agent_id.rsplit('-', 1)
                    if len(parts) == 2 and len(parts[1]) <= 10 and parts[1].replace('-', '').isalnum():
                        # Replace existing suffix with user's suffix
                        agent_id = f"{parts[0]}-{suffix}"
                    else:
                        # Append suffix
                        agent_id = f"{agent_id}-{suffix}"

            # Get project info
            project_key = data.get('project_key')
            project_name = data.get('project_name')

            # Check if agent already exists
            existing = Agent.get_by_agent_id(agent_id)

            if existing:
                # Update existing agent (reconnection)
                # Link to current user if not already linked
                if not existing.user_key:
                    existing.user_key = user_key
                elif existing.user_key != user_key:
                    # Agent belongs to different user - deny access
                    return {'success': False, 'msg': 'Agent is registered to a different user'}, 403

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

                # Update denormalized user info
                existing.user_name = user_name
                existing.user_initials = user_initials.upper() if user_initials else None

                # Update team association if provided
                if team_key:
                    existing.team_key = team_key
                    existing.team_name = team_name

                # Update project association if provided
                if project_key:
                    existing.project_key = project_key
                if project_name:
                    existing.project_name = project_name

                existing.update_heartbeat()
                existing.save()

                # Record reconnection activity
                activity_service.record_agent_registered(
                    actor=existing.agent_id,
                    agent_key=existing.agent_key,
                    client=existing.client,
                    persona=existing.persona_key,
                    model=existing.model_key,
                    is_reconnect=True,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                # Create or update session for this agent connection
                session = Session.create_for_user(
                    user_key=user_key,
                    remember_me=True,  # Agent sessions are long-lived
                    user_agent=f"MCP/{client}" if client else "MCP/unknown",
                    ip_address=request.remote_addr,
                    agent_key=existing.agent_key,
                    cleanup_old=False  # Don't cleanup - agents may have multiple sessions
                )

                result = {
                    'success': True,
                    'msg': 'Agent updated',
                    'data': existing.to_dict()
                }
                result['data']['session_key'] = session.session_key
                if affinity_warning:
                    result['data']['affinity_warning'] = affinity_warning
                return result

            # Create new agent linked to the authenticated user
            agent = Agent(
                agent_id=agent_id,  # Use processed agent_id with initials suffix
                user_key=user_key,
                client=client,
                model_key=model_key,
                persona_key=persona_key,
                focus=data.get('focus'),
                role=data.get('role'),
                capabilities=data.get('capabilities', []),
                status={'progress': 'not_started'},
                # Denormalized user info
                user_name=user_name,
                user_initials=user_initials.upper() if user_initials else None,
                # Team association
                team_key=team_key,
                team_name=team_name,
                # Project association
                project_key=project_key,
                project_name=project_name,
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
                    model=agent.model_key,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                # Create session for this agent connection
                session = Session.create_for_user(
                    user_key=user_key,
                    remember_me=True,  # Agent sessions are long-lived
                    user_agent=f"MCP/{client}" if client else "MCP/unknown",
                    ip_address=request.remote_addr,
                    agent_key=agent.agent_key,
                    cleanup_old=False  # Don't cleanup - agents may have multiple sessions
                )

                result = {
                    'success': True,
                    'msg': 'Agent registered',
                    'data': agent.to_dict()
                }
                result['data']['session_key'] = session.session_key
                if affinity_warning:
                    result['data']['affinity_warning'] = affinity_warning
                return result, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    def _check_agent_access(agent_key_or_id):
        """Helper to check if user has access to an agent."""
        # Try by key first, then by agent_id
        agent = Agent.get_by_key(agent_key_or_id)
        if not agent:
            agent = Agent.get_by_agent_id(agent_key_or_id)
        if not agent:
            return None, {'success': False, 'msg': 'Agent not found'}, 404

        # Check user access
        if g.current_user:
            if agent.user_key and agent.user_key != g.current_user.user_key:
                return None, {'success': False, 'msg': 'Agent not found'}, 404

        return agent, None, None

    @ns.route('/<string:agent_key>')
    @ns.param('agent_key', 'Agent Key or Agent ID')
    class AgentDetail(Resource):
        @ns.doc('get_agent')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, agent_key):
            """Get agent by key or agent_id."""
            agent, error, status = _check_agent_access(agent_key)
            if error:
                return error, status

            return {
                'success': True,
                'msg': 'Agent retrieved',
                'data': agent.to_dict()
            }

        @ns.doc('delete_agent')
        @ns.marshal_with(response_model)
        @require_auth
        def delete(self, agent_key):
            """Delete an agent. Only inactive agents can be deleted."""
            agent, error, status = _check_agent_access(agent_key)
            if error:
                return error, status

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
        @require_auth
        def delete(self):
            """Delete all inactive agents owned by the authenticated user."""
            user_key = g.current_user.user_key if g.current_user else None
            if not user_key:
                return {'success': False, 'msg': 'Authentication required'}, 401

            # Only get agents for this user
            user_agents = Agent.get_by_user_key(user_key)
            inactive_agents = [a for a in user_agents if not a.is_active]

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
        @require_auth
        def get(self, agent_id):
            """Get agent status."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

            return {
                'success': True,
                'msg': 'Agent status retrieved',
                'data': agent.to_dict()
            }

        @ns.doc('update_agent_status')
        @ns.expect(status_update)
        @ns.marshal_with(response_model)
        @require_auth
        def put(self, agent_id):
            """Update agent status."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def post(self, agent_id):
            """Update agent heartbeat. Returns unread message count including autonomous tasks."""
            from api.models import Message

            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

            try:
                agent.update_heartbeat()

                # Get unread message counts for this agent
                unread_count = Message.get_unread_count(agent_key=agent.agent_key)
                autonomous_count = Message.get_unread_autonomous_count(agent_key=agent.agent_key)

                # Record activity with message counts
                activity_service.record_agent_heartbeat(
                    actor=agent.agent_id,
                    agent_key=agent.agent_key,
                    status=agent.status.get('progress') if agent.status else None,
                    unread_messages=unread_count,
                    autonomous_tasks=autonomous_count,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                # Build response with message notification and focused mode info
                agent_data = agent.to_dict()
                agent_data['unread_messages'] = unread_count
                agent_data['autonomous_tasks'] = autonomous_count
                agent_data['recommended_heartbeat_seconds'] = 30 if agent.is_focused else 300

                # Include current milestone for MCP reminder display
                if agent.current_milestone_key:
                    agent_data['current_milestone'] = {
                        'key': agent.current_milestone_key,
                        'name': agent.current_milestone_name,
                        'status': agent.current_milestone_status,
                        'started_at': agent.current_milestone_started_at.isoformat() if agent.current_milestone_started_at else None
                    }

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
        @require_auth
        def get(self, agent_id):
            """Get agent's current focus."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def put(self, agent_id):
            """Update agent's current work focus. Send empty string to clear focus."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def get(self, agent_id):
            """Get agent's focused mode status."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def put(self, agent_id):
            """
            Set focused mode for fast heartbeats.

            When enabled, the agent signals it's actively waiting for a response.
            Heartbeat interval should be reduced (30 seconds vs 5 minutes).
            Focused mode auto-expires after duration_minutes (default 10).
            """
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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

    # Milestone model
    milestone_update = ns.model('MilestoneUpdate', {
        'milestone_key': fields.String(description='Milestone entity key (null to clear)'),
        'milestone_name': fields.String(description='Milestone name (null to clear)'),
        'milestone_status': fields.String(description='Status: started, completed, blocked (null to clear)'),
    })

    @ns.route('/<string:agent_id>/milestone')
    @ns.param('agent_id', 'Agent ID')
    class AgentMilestone(Resource):
        @ns.doc('get_milestone')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, agent_id):
            """Get agent's current milestone."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

            return {
                'success': True,
                'msg': 'Current milestone retrieved',
                'data': {
                    'agent_id': agent.agent_id,
                    'current_milestone': {
                        'key': agent.current_milestone_key,
                        'name': agent.current_milestone_name,
                        'status': agent.current_milestone_status,
                        'started_at': agent.current_milestone_started_at.isoformat() if agent.current_milestone_started_at else None
                    } if agent.current_milestone_key else None,
                    'has_active_milestone': agent.has_active_milestone
                }
            }

        @ns.doc('set_milestone')
        @ns.expect(milestone_update)
        @ns.marshal_with(response_model)
        @require_auth
        def put(self, agent_id):
            """
            Set or clear the agent's current milestone.

            Used by MCP record_milestone tool to track what the agent is working on.
            Setting milestone_key to null clears the current milestone.
            """
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

            data = request.json

            try:
                milestone_key = data.get('milestone_key')
                milestone_name = data.get('milestone_name')
                milestone_status = data.get('milestone_status')

                if milestone_key and milestone_name and milestone_status:
                    # Set milestone
                    agent.set_current_milestone(milestone_key, milestone_name, milestone_status)
                    msg = f'Milestone set: {milestone_name} ({milestone_status})'
                else:
                    # Clear milestone
                    agent.clear_current_milestone()
                    msg = 'Milestone cleared'

                return {
                    'success': True,
                    'msg': msg,
                    'data': {
                        'agent_id': agent.agent_id,
                        'current_milestone': {
                            'key': agent.current_milestone_key,
                            'name': agent.current_milestone_name,
                            'status': agent.current_milestone_status,
                            'started_at': agent.current_milestone_started_at.isoformat() if agent.current_milestone_started_at else None
                        } if agent.current_milestone_key else None,
                        'has_active_milestone': agent.has_active_milestone
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
        @require_auth
        def get(self, agent_id):
            """List checkpoints for an agent."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def post(self, agent_id):
            """Create a new checkpoint for an agent."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def get(self, agent_id, checkpoint_key):
            """Get a specific checkpoint."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def delete(self, agent_id, checkpoint_key):
            """Delete a checkpoint."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
        @require_auth
        def post(self, agent_id, checkpoint_key):
            """Restore an agent to a checkpoint state."""
            agent, error, status = _check_agent_access(agent_id)
            if error:
                return error, status

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
