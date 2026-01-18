"""
Collective Memory Platform - Message Routes

Inter-agent message queue operations.

Read tracking modes:
- Per-agent: Pass agent_id to track reads per agent (recommended)
- Legacy: Uses global read_at field on Message (backward compatible)
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Message, MessageRead
from api.services.activity import activity_service
from api.services.auth import require_auth


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key for activity tracking."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


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
        description='Inter-agent message operations',
        path='/messages'
    )

    # Define models for OpenAPI documentation
    message_model = ns.model('Message', {
        'message_key': fields.String(readonly=True, description='Unique message identifier'),
        'channel': fields.String(required=True, description='Channel name'),
        'from_agent': fields.String(required=True, description='Sender agent ID'),
        'to_agent': fields.String(description='Recipient agent ID (null for broadcast)'),
        'reply_to_key': fields.String(description='Parent message key (for replies)'),
        'message_type': fields.String(required=True, description='Type: status, announcement, request, task, message'),
        'content': fields.Raw(required=True, description='Message content as JSON'),
        'priority': fields.String(description='Priority: normal, high, urgent'),
        'autonomous': fields.Boolean(description='Whether this is an autonomous task requiring action'),
        'read_at': fields.DateTime(readonly=True),
        'is_read': fields.Boolean(readonly=True),
        'reply_count': fields.Integer(readonly=True, description='Number of replies'),
        'has_parent': fields.Boolean(readonly=True, description='Whether this is a reply'),
        'created_at': fields.DateTime(readonly=True),
    })

    message_create = ns.model('MessageCreate', {
        'channel': fields.String(required=True, description='Channel name'),
        'from_agent': fields.String(description='Sender agent ID (required unless from_human is set)'),
        'from_human': fields.String(description='Human sender name (for non-agent messages)'),
        'to_agent': fields.String(description='Recipient agent ID (null for broadcast)'),
        'reply_to_key': fields.String(description='Parent message key (for replies)'),
        'message_type': fields.String(required=True, description='Message type'),
        'content': fields.Raw(required=True, description='Message content as JSON'),
        'priority': fields.String(description='Priority level', default='normal'),
        'autonomous': fields.Boolean(description='Mark as autonomous task - receiver should work on it and reply', default=False),
        'entity_keys': fields.List(fields.String(), description='Entity keys to link this message to'),
        'team_key': fields.String(description='Team key for team-scoped messages (null for domain-wide)'),
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
        @ns.param('for_agent', 'Get messages for this agent (direct + broadcasts) with per-agent read status', type=str)
        @ns.param('from_agent', 'Filter by sender agent ID only', type=str)
        @ns.param('to_agent', 'Filter by recipient agent ID only', type=str)
        @ns.param('team_key', 'Filter by specific team (null shows domain-wide only)', type=str)
        @ns.param('include_readers', 'Include list of agents who have read each message', type=bool, default=False)
        @ns.param('include_thread_info', 'Include reply_count and has_parent for each message', type=bool, default=False)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Get all messages across all channels with optional filters.
            Automatically filtered by user's domain.

            When for_agent is provided:
            - Returns messages TO this agent + all broadcasts
            - Uses per-agent read tracking for is_read status
            - unread_only uses per-agent read tracking

            When for_agent is not provided:
            - Returns all messages matching other filters
            - Uses legacy global read_at for is_read status
            """
            from datetime import datetime
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            channel = request.args.get('channel')
            since = request.args.get('since')
            entity_key = request.args.get('entity_key')
            for_agent = request.args.get('for_agent')
            from_agent = request.args.get('from_agent')
            to_agent = request.args.get('to_agent')
            team_key_filter = request.args.get('team_key')
            include_readers = request.args.get('include_readers', 'false').lower() == 'true'
            include_thread_info = request.args.get('include_thread_info', 'false').lower() == 'true'

            # Multi-tenancy: automatically use user's domain
            user_domain = get_user_domain_key()
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
                    pass  # Invalid timestamp, ignore

            # Per-agent mode: use MessageRead-aware queries
            if for_agent:
                if unread_only:
                    messages = Message.get_unread_for_agent(
                        for_agent,
                        channel=channel,
                        limit=limit,
                        team_keys=user_team_keys,
                        team_key=team_key_filter
                    )
                else:
                    messages = Message.get_for_agent(
                        for_agent,
                        limit=limit,
                        unread_only=False,
                        team_keys=user_team_keys,
                        team_key=team_key_filter
                    )
                    if channel:
                        messages = [m for m in messages if m.channel == channel]

                # Apply since filter (post-query filtering for per-agent mode)
                if since_dt:
                    messages = [m for m in messages if m.created_at and m.created_at >= since_dt]

                # Apply entity_key filter (post-query filtering for per-agent mode)
                if entity_key:
                    messages = [m for m in messages if m.entity_keys and entity_key in m.entity_keys]

                # Multi-tenancy: filter by user's domain
                if user_domain:
                    messages = [m for m in messages if m.domain_key == user_domain]

                return {
                    'success': True,
                    'msg': f'Retrieved {len(messages)} messages for {for_agent}',
                    'data': {
                        'messages': [m.to_dict(for_agent=for_agent, include_readers=include_readers, include_thread_info=include_thread_info) for m in messages]
                    }
                }

            # Legacy mode: direct query with global read_at
            from sqlalchemy import or_
            query = Message.query

            # Multi-tenancy: filter by user's domain
            if user_domain:
                query = query.filter(Message.domain_key == user_domain)

            # Team scope filtering
            if team_key_filter:
                # Filter to specific team only
                query = query.filter(Message.team_key == team_key_filter)
            elif user_team_keys:
                # Show domain-wide (team_key is null) OR messages in user's teams
                query = query.filter(
                    or_(Message.team_key.is_(None), Message.team_key.in_(user_team_keys))
                )
            # If no team_keys, show all (backward compatible for users not in teams)

            # Filter by channel
            if channel:
                query = query.filter(Message.channel == channel)

            # Filter by time
            if since_dt:
                query = query.filter(Message.created_at >= since_dt)

            # Filter by linked entity
            if entity_key:
                # JSONB array contains check
                query = query.filter(Message.entity_keys.contains([entity_key]))

            # Specific filters
            if from_agent:
                query = query.filter(Message.from_agent == from_agent)
            if to_agent:
                query = query.filter(Message.to_agent == to_agent)

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
        @require_auth
        def post(self):
            """Post a new message to a channel. Automatically assigned to user's domain."""
            data = request.json

            # Validate required fields
            if not data.get('channel'):
                return {'success': False, 'msg': 'channel is required'}, 400
            if not data.get('from_agent') and not data.get('from_human'):
                return {'success': False, 'msg': 'either from_agent or from_human is required'}, 400
            if not data.get('message_type'):
                return {'success': False, 'msg': 'message_type is required'}, 400
            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Multi-tenancy: automatically set domain from authenticated user
            user_domain = get_user_domain_key()

            # Validate reply_to_key if provided
            reply_to_key = data.get('reply_to_key')
            parent = None
            if reply_to_key:
                parent = Message.get_by_key(reply_to_key)
                if not parent:
                    return {'success': False, 'msg': f'Parent message {reply_to_key} not found'}, 404
                # Verify parent belongs to same domain
                if user_domain and parent.domain_key != user_domain:
                    return {'success': False, 'msg': f'Parent message {reply_to_key} not found'}, 404

            # Use from_human as from_agent if no agent specified (prefix with "human:")
            from_agent = data.get('from_agent')
            if not from_agent and data.get('from_human'):
                from_agent = f"human:{data['from_human']}"

            # For replies, default to_agent to parent's from_agent (reply to sender)
            to_agent = data.get('to_agent')
            if not to_agent and parent:
                to_agent = parent.from_agent

            # Handle entity_keys - merge with parent's entity_keys for replies
            entity_keys = data.get('entity_keys', []) or []
            if parent and parent.entity_keys:
                # Merge parent's entity_keys with new ones (unique)
                entity_keys = list(set(entity_keys) | set(parent.entity_keys))

            # Handle team_key - validate access or inherit from parent
            team_key = data.get('team_key')
            if parent:
                # For replies, inherit team_key from parent
                team_key = parent.team_key
            elif team_key:
                # Validate user is a member of the team
                if not user_can_access_team(team_key):
                    return {'success': False, 'msg': 'Cannot send messages to this team'}, 403

            message = Message(
                channel=data['channel'],
                from_agent=from_agent,
                user_key=get_user_key(),  # Track authenticated user
                to_agent=to_agent,
                reply_to_key=reply_to_key,
                message_type=data['message_type'],
                content=data['content'],
                priority=data.get('priority', 'normal'),
                autonomous=data.get('autonomous', False),
                entity_keys=entity_keys if entity_keys else None,
                domain_key=user_domain,  # Auto-set from user's domain
                team_key=team_key  # Team scope (null = domain-wide)
            )

            try:
                message.save()
                # Record activity
                activity_service.record_message_sent(
                    actor=from_agent,
                    message_key=message.message_key,
                    channel=message.channel,
                    recipient=message.to_agent,
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )
                return {
                    'success': True,
                    'msg': 'Message posted' + (' as reply' if reply_to_key else ''),
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
        @ns.param('team_key', 'Filter by specific team (optional)', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, channel):
            """Get messages from a channel. Filtered by user's domain and team scope."""
            from sqlalchemy import or_

            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            for_agent = request.args.get('for_agent')
            team_key = request.args.get('team_key')

            # Multi-tenancy: get user's domain and team access
            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()

            # Validate team_key access if specified
            if team_key and not user_can_access_team(team_key):
                return {'success': False, 'msg': 'Cannot access messages from this team'}, 403

            if for_agent and unread_only:
                # Per-agent unread filtering with team scope
                messages = Message.get_unread_for_agent(
                    for_agent,
                    channel=channel,
                    limit=limit,
                    team_keys=user_team_keys if not team_key else None,
                    team_key=team_key
                )
                # Filter by domain
                if user_domain:
                    messages = [m for m in messages if m.domain_key == user_domain]
                unread_count = len(messages)
            else:
                query = Message.query.filter_by(channel=channel)

                # Filter by domain
                if user_domain:
                    query = query.filter(Message.domain_key == user_domain)

                # Filter by team scope
                if team_key:
                    query = query.filter(Message.team_key == team_key)
                elif user_team_keys:
                    # Show domain-wide (team_key is null) OR messages in user's teams
                    query = query.filter(
                        or_(Message.team_key.is_(None), Message.team_key.in_(user_team_keys))
                    )

                if unread_only:
                    query = query.filter(Message.read_at.is_(None))

                messages = query.order_by(Message.created_at.desc()).limit(limit).all()
                unread_count = Message.get_unread_count(channel, agent_id=for_agent)

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict(for_agent=for_agent) for m in messages],
                    'unread_count': unread_count
                }
            }

    @ns.route('/<string:channel>/since/<string:timestamp>')
    @ns.param('channel', 'Channel name')
    @ns.param('timestamp', 'ISO8601 timestamp')
    class ChannelMessagesSince(Resource):
        @ns.doc('get_channel_messages_since')
        @ns.param('limit', 'Maximum messages to return', type=int, default=50)
        @ns.param('team_key', 'Filter by specific team (optional)', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, channel, timestamp):
            """Get messages from a channel since a timestamp. Filtered by user's domain and team scope."""
            limit = request.args.get('limit', 50, type=int)
            team_key = request.args.get('team_key')

            # Validate team_key access if specified
            if team_key and not user_can_access_team(team_key):
                return {'success': False, 'msg': 'Cannot access messages from this team'}, 403

            messages = Message.get_by_channel(channel, limit=limit, since=timestamp)

            # Multi-tenancy: filter by user's domain
            user_domain = get_user_domain_key()
            if user_domain:
                messages = [m for m in messages if m.domain_key == user_domain]

            # Filter by team scope
            user_team_keys = get_user_team_keys()
            if team_key:
                messages = [m for m in messages if m.team_key == team_key]
            elif user_team_keys:
                # Show domain-wide (team_key is null) OR messages in user's teams
                messages = [m for m in messages if m.team_key is None or m.team_key in user_team_keys]

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} new messages',
                'data': {
                    'messages': [m.to_dict() for m in messages]
                }
            }

    def _check_message_access(message, user_domain, user_team_keys):
        """Check if user has access to message based on domain and team scope."""
        # Check domain access
        if user_domain and message.domain_key != user_domain:
            return False
        # Check team access - if message is team-scoped, user must be in that team
        if message.team_key:
            if not user_team_keys or message.team_key not in user_team_keys:
                return False
        return True

    # Legacy alias for backward compatibility
    def _check_message_domain_access(message, user_domain):
        """Check if user has access to message based on domain."""
        return _check_message_access(message, user_domain, get_user_team_keys())

    @ns.route('/mark-read/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class MarkMessageRead(Resource):
        @ns.doc('mark_message_read')
        @ns.param('agent_id', 'Agent marking as read (for per-agent tracking)', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def post(self, message_key):
            """
            Mark a message as read. Must belong to user's domain.
            """
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_message_domain_access(message, user_domain):
                return {'success': False, 'msg': 'Message not found'}, 404

            agent_id = request.args.get('agent_id')

            try:
                message.mark_read(agent_id=agent_id)
                return {
                    'success': True,
                    'msg': f'Message marked as read' + (f' by {agent_id}' if agent_id else ''),
                    'data': message.to_dict(for_agent=agent_id)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/clear-all')
    class ClearAllMessages(Resource):
        @ns.doc('clear_all_messages')
        @ns.marshal_with(response_model)
        @require_auth
        def delete(self):
            """
            Delete all messages from the queue for user's domain.
            """
            from api.models import db

            # Multi-tenancy: only delete messages in user's domain
            user_domain = get_user_domain_key()

            try:
                if user_domain:
                    # Get message keys in this domain
                    domain_messages = Message.query.filter_by(domain_key=user_domain).all()
                    message_keys = [m.message_key for m in domain_messages]

                    if message_keys:
                        # Delete read tracking records for these messages
                        MessageRead.query.filter(MessageRead.message_key.in_(message_keys)).delete(synchronize_session=False)
                        # Delete messages
                        count = Message.query.filter(Message.message_key.in_(message_keys)).delete(synchronize_session=False)
                    else:
                        count = 0
                else:
                    # No domain - delete all (for backwards compatibility)
                    MessageRead.query.delete()
                    count = Message.query.delete()

                db.session.commit()

                return {
                    'success': True,
                    'msg': f'Cleared {count} messages',
                    'data': {
                        'deleted_count': count
                    }
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/mark-all-read')
    class MarkAllMessagesRead(Resource):
        @ns.doc('mark_all_messages_read')
        @ns.param('agent_id', 'Agent marking as read (required for per-agent tracking)', type=str)
        @ns.param('channel', 'Filter by channel (optional)', type=str)
        @ns.param('team_key', 'Filter by specific team (optional)', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def post(self):
            """
            Mark all unread messages as read for an agent. Filtered by user's domain and team scope.
            """
            agent_id = request.args.get('agent_id')
            channel = request.args.get('channel')
            team_key = request.args.get('team_key')

            if not agent_id:
                return {'success': False, 'msg': 'agent_id is required for per-agent read tracking'}, 400

            # Validate team_key access if specified
            if team_key and not user_can_access_team(team_key):
                return {'success': False, 'msg': 'Cannot access messages from this team'}, 403

            # Multi-tenancy: get user's domain and teams
            user_domain = get_user_domain_key()
            user_team_keys = get_user_team_keys()

            try:
                # Get unread messages for this agent with team filtering
                unread_messages = Message.get_unread_for_agent(
                    agent_id,
                    channel=channel,
                    limit=1000,
                    team_keys=user_team_keys if not team_key else None,
                    team_key=team_key
                )

                # Filter by domain
                if user_domain:
                    unread_messages = [m for m in unread_messages if m.domain_key == user_domain]

                count = len(unread_messages)

                # Mark each as read by this agent
                message_keys = [m.message_key for m in unread_messages]
                if message_keys:
                    MessageRead.mark_all_read_for_agent(agent_id, message_keys)

                filters_applied = [f"agent_id={agent_id}"]
                if channel:
                    filters_applied.append(f"channel={channel}")
                if team_key:
                    filters_applied.append(f"team_key={team_key}")
                filter_desc = f" ({', '.join(filters_applied)})"

                return {
                    'success': True,
                    'msg': f'Marked {count} messages as read{filter_desc}',
                    'data': {
                        'marked_count': count
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/confirm/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class ConfirmMessage(Resource):
        @ns.doc('confirm_message')
        @ns.param('confirmed_by', 'Agent or human confirming the task', type=str, required=True)
        @ns.marshal_with(response_model)
        @require_auth
        def post(self, message_key):
            """
            Confirm task completion on a message. Must belong to user's domain.
            """
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_message_domain_access(message, user_domain):
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
        @require_auth
        def delete(self, message_key):
            """
            Remove confirmation from a message. Must belong to user's domain.
            """
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_message_domain_access(message, user_domain):
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
        @require_auth
        def put(self, message_key):
            """
            Update entity links on a message. Must belong to user's domain.
            """
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_message_domain_access(message, user_domain):
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
        @ns.param('include_readers', 'Include list of agents who have read', type=bool, default=True)
        @ns.param('include_entities', 'Include linked entities from knowledge graph', type=bool, default=False)
        @ns.param('for_agent', 'Get per-agent read status', type=str)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self, message_key):
            """
            Get a single message with full thread context. Must belong to user's domain.
            """
            include_thread = request.args.get('include_thread', 'true').lower() == 'true'
            include_readers = request.args.get('include_readers', 'true').lower() == 'true'
            include_entities = request.args.get('include_entities', 'false').lower() == 'true'
            for_agent = request.args.get('for_agent')

            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_message_domain_access(message, user_domain):
                return {'success': False, 'msg': 'Message not found'}, 404

            result = message.to_dict(
                for_agent=for_agent,
                include_readers=include_readers,
                include_thread_info=True
            )

            if include_thread:
                # Include parent message if this is a reply
                if message.reply_to_key:
                    parent = message.get_parent()
                    if parent:
                        result['parent'] = parent.to_dict(
                            for_agent=for_agent,
                            include_readers=False,
                            include_thread_info=True
                        )

                # Include direct replies
                replies = message.get_replies(limit=100)
                result['replies'] = [
                    r.to_dict(
                        for_agent=for_agent,
                        include_readers=False,
                        include_thread_info=True
                    ) for r in replies
                ]

            # Include linked entities from across the thread
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
        @require_auth
        def delete(self, message_key):
            """
            Delete a message and all its replies. Must belong to user's domain.
            """
            from api.models import db

            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            # Multi-tenancy: verify domain access
            user_domain = get_user_domain_key()
            if not _check_message_domain_access(message, user_domain):
                return {'success': False, 'msg': 'Message not found'}, 404

            def collect_thread_keys(msg_key: str, keys: set):
                """Recursively collect all message keys in a thread."""
                keys.add(msg_key)
                replies = Message.query.filter_by(reply_to_key=msg_key).all()
                for reply in replies:
                    collect_thread_keys(reply.message_key, keys)

            try:
                # Collect all message keys in the thread
                thread_keys = set()
                collect_thread_keys(message_key, thread_keys)

                # Delete read tracking records for all messages in thread
                MessageRead.query.filter(MessageRead.message_key.in_(thread_keys)).delete(synchronize_session=False)

                # Delete all messages in thread
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
