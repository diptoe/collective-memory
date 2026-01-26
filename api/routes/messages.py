"""
Collective Memory Platform - Message Routes

Inter-agent and user message queue operations.

Scope types define message visibility and routing:
- broadcast-domain: Visible to all agents and users in the domain
- broadcast-team: Visible to all agents and users in a specific team
- agent-agent: Direct message between two specific agents
- agent-user: Message from an agent to a specific user
- user-agent: Message from a user to a specific agent
- user-agents: Message from a user to all agents linked to them
- agent-agents: Message from an agent to all agents linked to a user

Read tracking modes:
- Per-reader: Pass reader_key to track reads per agent/user (recommended)
- Legacy: Uses global read_at field on Message (backward compatible)
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Message, MessageRead
from api.models.message import VALID_SCOPES
from api.services.activity import activity_service
from api.services.auth import require_auth, require_auth_strict, require_write_access


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


def is_user_key(key: str) -> bool:
    """
    Check if a key belongs to a User (vs an Agent).

    Args:
        key: The key to check

    Returns:
        True if the key is a user_key, False otherwise
    """
    if not key:
        return False
    from api.models.user import User
    return User.query.filter_by(user_key=key).first() is not None


def is_agent_key(key: str) -> bool:
    """
    Check if a key belongs to an Agent (vs a User).

    Args:
        key: The key to check

    Returns:
        True if the key is an agent_key, False otherwise
    """
    if not key:
        return False
    from api.models.agent import Agent
    return Agent.query.filter_by(agent_key=key).first() is not None


def get_user_team_keys() -> list[str]:
    """Get list of team_keys the current user is a member of."""
    if hasattr(g, 'current_user') and g.current_user:
        teams = g.current_user.get_teams()
        return [t.team_key for t in teams]
    return []


def user_can_access_team(team_key: str) -> bool:
    """Check if current user is a member of the given team."""
    if not team_key:
        return True  # Null team_key = domain-wide, allowed
    return team_key in get_user_team_keys()


def register_message_routes(api: Api):
    """Register message routes with the API."""

    ns = api.namespace(
        'messages',
        description='Inter-agent and user message operations',
        path='/messages'
    )

    # Define models for OpenAPI documentation
    message_model = ns.model('Message', {
        'message_key': fields.String(readonly=True, description='Unique message identifier'),
        'channel': fields.String(required=True, description='Channel name'),
        'from_key': fields.String(required=True, description='Sender key (agent_key or user_key)'),
        'to_key': fields.String(description='Recipient key (agent_key or user_key, null for broadcasts)'),
        'user_key': fields.String(description='User key for user-agents/agent-agents scopes'),
        'scope': fields.String(required=True, description='Message scope: broadcast-domain, broadcast-team, agent-agent, agent-user, user-agent, user-agents, agent-agents'),
        'reply_to_key': fields.String(description='Parent message key (for replies)'),
        'message_type': fields.String(required=True, description='Type: status, announcement, request, task, message, acknowledged, waiting, resumed'),
        'content': fields.Raw(required=True, description='Message content as JSON'),
        'priority': fields.String(description='Priority: normal, high, urgent'),
        'autonomous': fields.Boolean(description='Whether this is an autonomous task requiring action'),
        'team_key': fields.String(description='Team key (required for broadcast-team scope)'),
        'read_at': fields.DateTime(readonly=True),
        'is_read': fields.Boolean(readonly=True),
        'reply_count': fields.Integer(readonly=True, description='Number of replies'),
        'has_parent': fields.Boolean(readonly=True, description='Whether this is a reply'),
        'created_at': fields.DateTime(readonly=True),
    })

    message_create = ns.model('MessageCreate', {
        'channel': fields.String(required=True, description='Channel name'),
        'from_key': fields.String(description='Sender key (agent_key or user_key)'),
        'to_key': fields.String(description='Recipient key (null for broadcasts)'),
        'scope': fields.String(description='Message scope (auto-detected if not provided)'),
        'reply_to_key': fields.String(description='Parent message key (for replies)'),
        'message_type': fields.String(required=True, description='Message type'),
        'content': fields.Raw(required=True, description='Message content as JSON'),
        'priority': fields.String(description='Priority level', default='normal'),
        'autonomous': fields.Boolean(description='Mark as autonomous task', default=False),
        'entity_keys': fields.List(fields.String(), description='Entity keys to link this message to'),
        'team_key': fields.String(description='Team key for broadcast-team scope'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class MessageList(Resource):
        @ns.doc('list_all_messages')
        @ns.param('limit', 'Maximum messages to return', type=int, default=50)
        @ns.param('unread_only', 'Only return unread messages', type=bool, default=False)
        @ns.param('channel', 'Filter by channel name', type=str)
        @ns.param('since', 'Only return messages created after this ISO8601 timestamp', type=str)
        @ns.param('entity_key', 'Filter messages linked to this entity', type=str)
        @ns.param('for_agent', 'Get messages for this agent_key with per-agent read status', type=str)
        @ns.param('for_user', 'Get messages for this user_key', type=str)
        @ns.param('from_key', 'Filter by sender key', type=str)
        @ns.param('to_key', 'Filter by recipient key', type=str)
        @ns.param('scope', 'Filter by scope type', type=str)
        @ns.param('team_key', 'Filter by specific team', type=str)
        @ns.param('include_readers', 'Include list of readers', type=bool, default=False)
        @ns.param('include_thread_info', 'Include reply_count and has_parent', type=bool, default=False)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Get messages with optional filters.
            Automatically filtered by user's domain.

            When for_agent is provided:
            - Returns messages visible to this agent based on scope rules
            - Uses per-agent read tracking for is_read status

            When for_user is provided:
            - Returns messages visible to this user based on scope rules
            """
            from datetime import datetime
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            channel = request.args.get('channel')
            since = request.args.get('since')
            entity_key = request.args.get('entity_key')
            for_agent = request.args.get('for_agent')
            for_user = request.args.get('for_user')
            from_key_filter = request.args.get('from_key')
            to_key_filter = request.args.get('to_key')
            scope_filter = request.args.get('scope')
            team_key_filter = request.args.get('team_key')
            include_readers = request.args.get('include_readers', 'false').lower() == 'true'
            include_thread_info = request.args.get('include_thread_info', 'false').lower() == 'true'

            # Multi-tenancy: automatically use user's domain
            user_domain = get_user_domain_key()
            user_key = get_user_key()
            user_team_keys = get_user_team_keys()

            # Validate team access if specific team requested
            if team_key_filter and not user_can_access_team(team_key_filter):
                return {'success': False, 'msg': 'Access denied to this team'}, 403

            # Parse since timestamp if provided
            since_dt = None
            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                except ValueError:
                    pass

            # Agent-specific mode
            if for_agent:
                messages = Message.get_for_agent(
                    agent_key=for_agent,
                    user_key=user_key,  # For user-agents/agent-agents visibility
                    limit=limit,
                    unread_only=unread_only,
                    team_keys=user_team_keys,
                    team_key_filter=team_key_filter,
                    domain_key=user_domain
                )

                # Apply additional filters
                if channel:
                    messages = [m for m in messages if m.channel == channel]
                if since_dt:
                    messages = [m for m in messages if m.created_at and m.created_at >= since_dt]
                if entity_key:
                    messages = [m for m in messages if m.entity_keys and entity_key in m.entity_keys]

                return {
                    'success': True,
                    'msg': f'Retrieved {len(messages)} messages for agent {for_agent}',
                    'data': {
                        'messages': [m.to_dict(for_reader=for_agent, include_readers=include_readers, include_thread_info=include_thread_info) for m in messages]
                    }
                }

            # User-specific mode
            if for_user:
                messages = Message.get_for_user(
                    user_key=for_user,
                    limit=limit,
                    unread_only=unread_only,
                    team_keys=user_team_keys,
                    team_key_filter=team_key_filter,
                    domain_key=user_domain
                )

                # Apply additional filters
                if channel:
                    messages = [m for m in messages if m.channel == channel]
                if since_dt:
                    messages = [m for m in messages if m.created_at and m.created_at >= since_dt]
                if entity_key:
                    messages = [m for m in messages if m.entity_keys and entity_key in m.entity_keys]

                return {
                    'success': True,
                    'msg': f'Retrieved {len(messages)} messages for user {for_user}',
                    'data': {
                        'messages': [m.to_dict(for_reader=for_user, include_readers=include_readers, include_thread_info=include_thread_info) for m in messages]
                    }
                }

            # General query mode
            from sqlalchemy import or_
            query = Message.query

            # Multi-tenancy: filter by user's domain
            if user_domain:
                query = query.filter(Message.domain_key == user_domain)

            # Scope filtering - only show messages user should see
            if scope_filter:
                query = query.filter(Message.scope == scope_filter)

            # Team filtering
            if team_key_filter == '':
                # Empty string = domain-wide broadcasts only
                query = query.filter(Message.scope == 'broadcast-domain')
            elif team_key_filter:
                query = query.filter(Message.team_key == team_key_filter)

            # Channel filter
            if channel:
                query = query.filter(Message.channel == channel)

            # Time filter
            if since_dt:
                query = query.filter(Message.created_at >= since_dt)

            # Entity filter
            if entity_key:
                query = query.filter(Message.entity_keys.contains([entity_key]))

            # Specific filters
            if from_key_filter:
                query = query.filter(Message.from_key == from_key_filter)
            if to_key_filter:
                query = query.filter(Message.to_key == to_key_filter)

            if unread_only:
                query = query.filter(Message.read_at.is_(None))

            messages = query.order_by(Message.created_at.desc()).limit(limit).all()

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict(include_readers=include_readers, include_thread_info=include_thread_info) for m in messages]
                }
            }

        @ns.doc('post_message')
        @ns.expect(message_create)
        @ns.marshal_with(response_model, code=201)
        @require_write_access
        def post(self):
            """
            Post a new message. Requires write access. Automatically assigned to user's domain.

            Scope auto-detection:
            - If to_key is set and looks like agent_key: agent-agent or user-agent
            - If to_key is set and looks like user_key: agent-user
            - If team_key is set without to_key: broadcast-team
            - Otherwise: broadcast-domain
            """
            data = request.json

            # Validate required fields
            if not data.get('channel'):
                return {'success': False, 'msg': 'channel is required'}, 400
            if not data.get('from_key'):
                return {'success': False, 'msg': 'from_key is required'}, 400
            if not data.get('message_type'):
                return {'success': False, 'msg': 'message_type is required'}, 400
            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Multi-tenancy
            user_domain = get_user_domain_key()
            current_user_key = get_user_key()

            from_key = data.get('from_key')
            to_key = data.get('to_key')
            team_key = data.get('team_key')
            scope = data.get('scope')
            msg_user_key = data.get('user_key')  # For user-agents/agent-agents

            # Validate reply_to_key if provided
            reply_to_key = data.get('reply_to_key')
            parent = None
            if reply_to_key:
                parent = Message.get_by_key(reply_to_key)
                if not parent:
                    return {'success': False, 'msg': f'Parent message {reply_to_key} not found'}, 404
                if user_domain and parent.domain_key != user_domain:
                    return {'success': False, 'msg': f'Parent message {reply_to_key} not found'}, 404
                # Inherit team_key from parent for replies
                team_key = parent.team_key

            # Auto-detect scope if not provided
            if not scope:
                if to_key:
                    # Determine scope based on sender/recipient types
                    from_is_user = is_user_key(from_key)
                    to_is_user = is_user_key(to_key)

                    if from_is_user and not to_is_user:
                        scope = 'user-agent'
                    elif not from_is_user and to_is_user:
                        scope = 'agent-user'
                    else:
                        scope = 'agent-agent'
                elif team_key:
                    scope = 'broadcast-team'
                else:
                    scope = 'broadcast-domain'

            # Validate scope
            is_valid, error = Message.validate_scope(scope, to_key, team_key, msg_user_key)
            if not is_valid:
                return {'success': False, 'msg': error}, 400

            # Validate team access for broadcast-team
            if scope == 'broadcast-team' and not user_can_access_team(team_key):
                return {'success': False, 'msg': 'Cannot send messages to this team'}, 403

            # Handle entity_keys - merge with parent's for replies
            entity_keys = data.get('entity_keys', []) or []
            if parent and parent.entity_keys:
                entity_keys = list(set(entity_keys) | set(parent.entity_keys))

            # Resolve display names for readability
            from_name = Message.resolve_name(from_key)
            to_name = Message.resolve_name(to_key) if to_key else None

            message = Message(
                channel=data['channel'],
                from_key=from_key,
                from_name=from_name,
                to_key=to_key,
                to_name=to_name,
                user_key=msg_user_key or current_user_key,  # Track user context
                scope=scope,
                reply_to_key=reply_to_key,
                message_type=data['message_type'],
                content=data['content'],
                priority=data.get('priority', 'normal'),
                autonomous=data.get('autonomous', False),
                entity_keys=entity_keys if entity_keys else None,
                domain_key=user_domain,
                team_key=team_key
            )

            try:
                message.save()
                activity_service.record_message_sent(
                    actor=from_key,
                    message_key=message.message_key,
                    channel=message.channel,
                    recipient=message.to_key,
                    domain_key=user_domain,
                    user_key=current_user_key
                )
                return {
                    'success': True,
                    'msg': f'Message posted (scope: {scope})' + (' as reply' if reply_to_key else ''),
                    'data': message.to_dict(include_thread_info=True)
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:channel>')
    @ns.param('channel', 'Channel name')
    class ChannelMessages(Resource):
        @ns.doc('get_channel_messages')
        @ns.param('limit', 'Maximum messages to return', type=int, default=50)
        @ns.param('unread_only', 'Only return unread messages', type=bool, default=False)
        @ns.param('for_agent', 'Get per-agent read status for this agent', type=str)
        @ns.param('team_key', 'Filter by specific team', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, channel):
            """Get messages from a channel. Filtered by user's domain."""
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            for_agent = request.args.get('for_agent')
            team_key_filter = request.args.get('team_key')

            user_domain = get_user_domain_key()
            user_key = get_user_key()
            user_team_keys = get_user_team_keys()

            if team_key_filter and not user_can_access_team(team_key_filter):
                return {'success': False, 'msg': 'Cannot access messages from this team'}, 403

            if for_agent:
                messages = Message.get_for_agent(
                    agent_key=for_agent,
                    user_key=user_key,
                    limit=limit,
                    unread_only=unread_only,
                    team_keys=user_team_keys,
                    team_key_filter=team_key_filter,
                    domain_key=user_domain
                )
                messages = [m for m in messages if m.channel == channel]
            else:
                query = Message.query.filter_by(channel=channel)

                if user_domain:
                    query = query.filter(Message.domain_key == user_domain)

                if team_key_filter == '':
                    query = query.filter(Message.scope == 'broadcast-domain')
                elif team_key_filter:
                    query = query.filter(Message.team_key == team_key_filter)

                if unread_only:
                    query = query.filter(Message.read_at.is_(None))

                messages = query.order_by(Message.created_at.desc()).limit(limit).all()

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict(for_reader=for_agent) for m in messages]
                }
            }

    @ns.route('/<string:channel>/since/<string:timestamp>')
    @ns.param('channel', 'Channel name')
    @ns.param('timestamp', 'ISO8601 timestamp')
    class ChannelMessagesSince(Resource):
        @ns.doc('get_channel_messages_since')
        @ns.param('limit', 'Maximum messages to return', type=int, default=50)
        @ns.param('team_key', 'Filter by specific team', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, channel, timestamp):
            """Get messages from a channel since a timestamp."""
            limit = request.args.get('limit', 50, type=int)
            team_key_filter = request.args.get('team_key')

            if team_key_filter and not user_can_access_team(team_key_filter):
                return {'success': False, 'msg': 'Cannot access messages from this team'}, 403

            messages = Message.get_by_channel(channel, limit=limit, since=timestamp)

            user_domain = get_user_domain_key()
            if user_domain:
                messages = [m for m in messages if m.domain_key == user_domain]

            if team_key_filter == '':
                messages = [m for m in messages if m.scope == 'broadcast-domain']
            elif team_key_filter:
                messages = [m for m in messages if m.team_key == team_key_filter]

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} new messages',
                'data': {
                    'messages': [m.to_dict() for m in messages]
                }
            }

    def _check_message_access(message, user_domain, user_team_keys):
        """Check if user has access to message based on domain and team scope."""
        if user_domain and message.domain_key != user_domain:
            return False
        if message.team_key:
            if not user_team_keys or message.team_key not in user_team_keys:
                return False
        return True

    @ns.route('/mark-read/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class MarkMessageRead(Resource):
        @ns.doc('mark_message_read')
        @ns.param('reader_key', 'Key of agent/user marking as read', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def post(self, message_key):
            """Mark a message as read."""
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()
            if not _check_message_access(message, user_domain, user_team_keys):
                return {'success': False, 'msg': 'Message not found'}, 404

            reader_key = request.args.get('reader_key')

            try:
                message.mark_read(reader_key=reader_key)
                return {
                    'success': True,
                    'msg': f'Message marked as read' + (f' by {reader_key}' if reader_key else ''),
                    'data': message.to_dict(for_reader=reader_key)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/clear-all')
    class ClearAllMessages(Resource):
        @ns.doc('clear_all_messages')
        @ns.marshal_with(response_model)
        @require_write_access
        def delete(self):
            """Delete all messages for user's domain. Requires write access."""
            from api.models import db

            user_domain = get_user_domain_key()

            try:
                if user_domain:
                    domain_messages = Message.query.filter_by(domain_key=user_domain).all()
                    message_keys = [m.message_key for m in domain_messages]

                    if message_keys:
                        MessageRead.query.filter(MessageRead.message_key.in_(message_keys)).delete(synchronize_session=False)
                        count = Message.query.filter(Message.message_key.in_(message_keys)).delete(synchronize_session=False)
                    else:
                        count = 0
                else:
                    MessageRead.query.delete()
                    count = Message.query.delete()

                db.session.commit()

                return {
                    'success': True,
                    'msg': f'Cleared {count} messages',
                    'data': {'deleted_count': count}
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/mark-all-read')
    class MarkAllMessagesRead(Resource):
        @ns.doc('mark_all_messages_read')
        @ns.param('reader_key', 'Key of agent/user marking as read (required)', type=str)
        @ns.param('channel', 'Filter by channel', type=str)
        @ns.param('team_key', 'Filter by specific team', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def post(self):
            """Mark all unread messages as read for an agent/user."""
            reader_key = request.args.get('reader_key')
            channel = request.args.get('channel')
            team_key_filter = request.args.get('team_key')

            if not reader_key:
                return {'success': False, 'msg': 'reader_key is required'}, 400

            if team_key_filter and not user_can_access_team(team_key_filter):
                return {'success': False, 'msg': 'Cannot access messages from this team'}, 403

            user_domain = get_user_domain_key()
            user_key = get_user_key()
            user_team_keys = get_user_team_keys()

            try:
                # Determine if reader is user or agent by database lookup
                if is_user_key(reader_key):
                    unread_messages = Message.get_for_user(
                        user_key=reader_key,
                        limit=1000,
                        unread_only=True,
                        team_keys=user_team_keys if not team_key_filter else None,
                        team_key_filter=team_key_filter,
                        domain_key=user_domain
                    )
                else:
                    unread_messages = Message.get_for_agent(
                        agent_key=reader_key,
                        user_key=user_key,
                        limit=1000,
                        unread_only=True,
                        team_keys=user_team_keys if not team_key_filter else None,
                        team_key_filter=team_key_filter,
                        domain_key=user_domain
                    )

                if channel:
                    unread_messages = [m for m in unread_messages if m.channel == channel]

                count = len(unread_messages)
                message_keys = [m.message_key for m in unread_messages]
                if message_keys:
                    MessageRead.mark_all_read_for_reader(reader_key, message_keys)

                return {
                    'success': True,
                    'msg': f'Marked {count} messages as read',
                    'data': {'marked_count': count}
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/confirm/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class ConfirmMessage(Resource):
        @ns.doc('confirm_message')
        @ns.param('confirmed_by', 'Key of agent/user confirming', type=str, required=True)
        @ns.marshal_with(response_model)
        @require_write_access
        def post(self, message_key):
            """Confirm task completion on a message. Requires write access."""
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()
            if not _check_message_access(message, user_domain, user_team_keys):
                return {'success': False, 'msg': 'Message not found'}, 404

            confirmed_by = request.args.get('confirmed_by')
            if not confirmed_by:
                return {'success': False, 'msg': 'confirmed_by is required'}, 400

            try:
                message.confirm(confirmed_by)
                return {
                    'success': True,
                    'msg': f'Message confirmed by {confirmed_by}',
                    'data': message.to_dict(include_thread_info=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('unconfirm_message')
        @ns.marshal_with(response_model)
        @require_write_access
        def delete(self, message_key):
            """Remove confirmation from a message. Requires write access."""
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()
            if not _check_message_access(message, user_domain, user_team_keys):
                return {'success': False, 'msg': 'Message not found'}, 404

            try:
                message.unconfirm()
                return {
                    'success': True,
                    'msg': 'Confirmation removed',
                    'data': message.to_dict(include_thread_info=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    entity_links_model = ns.model('EntityLinks', {
        'entity_keys': fields.List(fields.String(), required=True, description='Entity keys to link'),
        'mode': fields.String(description='Link mode: add (default), replace, or remove'),
    })

    @ns.route('/detail/<string:message_key>/entities')
    @ns.param('message_key', 'Message identifier')
    class MessageEntityLinks(Resource):
        @ns.doc('update_message_entity_links')
        @ns.expect(entity_links_model)
        @ns.marshal_with(response_model)
        @require_write_access
        def put(self, message_key):
            """Update entity links on a message. Requires write access."""
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()
            if not _check_message_access(message, user_domain, user_team_keys):
                return {'success': False, 'msg': 'Message not found'}, 404

            data = request.json
            entity_keys = data.get('entity_keys', [])
            mode = data.get('mode', 'add')

            if not entity_keys and mode != 'replace':
                return {'success': False, 'msg': 'entity_keys is required'}, 400

            if mode not in ('add', 'replace', 'remove'):
                return {'success': False, 'msg': 'mode must be add, replace, or remove'}, 400

            try:
                current_keys = set(message.entity_keys or [])

                if mode == 'add':
                    new_keys = current_keys | set(entity_keys)
                elif mode == 'replace':
                    new_keys = set(entity_keys)
                elif mode == 'remove':
                    new_keys = current_keys - set(entity_keys)

                message.entity_keys = list(new_keys) if new_keys else None
                message.save()

                return {
                    'success': True,
                    'msg': f'Entity links updated ({mode})',
                    'data': message.to_dict(include_thread_info=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/detail/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class MessageDetail(Resource):
        @ns.doc('get_message_detail')
        @ns.param('include_thread', 'Include parent and replies', type=bool, default=True)
        @ns.param('include_readers', 'Include list of readers', type=bool, default=True)
        @ns.param('include_entities', 'Include linked entities', type=bool, default=False)
        @ns.param('for_reader', 'Get per-reader read status', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, message_key):
            """Get a single message with full thread context."""
            include_thread = request.args.get('include_thread', 'true').lower() == 'true'
            include_readers = request.args.get('include_readers', 'true').lower() == 'true'
            include_entities = request.args.get('include_entities', 'false').lower() == 'true'
            for_reader = request.args.get('for_reader')

            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()
            if not _check_message_access(message, user_domain, user_team_keys):
                return {'success': False, 'msg': 'Message not found'}, 404

            result = message.to_dict(
                for_reader=for_reader,
                include_readers=include_readers,
                include_thread_info=True
            )

            if include_thread:
                if message.reply_to_key:
                    parent = message.get_parent()
                    if parent:
                        result['parent'] = parent.to_dict(
                            for_reader=for_reader,
                            include_readers=False,
                            include_thread_info=True
                        )

                replies = message.get_replies(limit=100)
                result['replies'] = [
                    r.to_dict(
                        for_reader=for_reader,
                        include_readers=False,
                        include_thread_info=True
                    ) for r in replies
                ]

            if include_entities:
                from api.models import Entity
                thread_entity_keys = Message.get_thread_entity_keys(message_key)
                if thread_entity_keys:
                    entities = Entity.query.filter(Entity.entity_key.in_(thread_entity_keys)).all()
                    result['linked_entities'] = [e.to_dict() for e in entities]
                else:
                    result['linked_entities'] = []

            return {
                'success': True,
                'msg': 'Message retrieved',
                'data': result
            }

        @ns.doc('delete_message_thread')
        @ns.marshal_with(response_model)
        @require_write_access
        def delete(self, message_key):
            """Delete a message and all its replies. Requires write access."""
            from api.models import db

            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()
            if not _check_message_access(message, user_domain, user_team_keys):
                return {'success': False, 'msg': 'Message not found'}, 404

            def collect_thread_keys(msg_key: str, keys: set):
                keys.add(msg_key)
                replies = Message.query.filter_by(reply_to_key=msg_key).all()
                for reply in replies:
                    collect_thread_keys(reply.message_key, keys)

            try:
                thread_keys = set()
                collect_thread_keys(message_key, thread_keys)

                MessageRead.query.filter(MessageRead.message_key.in_(thread_keys)).delete(synchronize_session=False)
                Message.query.filter(Message.message_key.in_(thread_keys)).delete(synchronize_session=False)

                db.session.commit()

                return {
                    'success': True,
                    'msg': f'Deleted thread with {len(thread_keys)} message(s)',
                    'data': {
                        'deleted_count': len(thread_keys),
                        'deleted_keys': list(thread_keys)
                    }
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500
