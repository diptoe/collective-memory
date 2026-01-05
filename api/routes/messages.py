"""
Collective Memory Platform - Message Routes

Inter-agent message queue operations.

Read tracking modes:
- Per-agent: Pass agent_id to track reads per agent (recommended)
- Legacy: Uses global read_at field on Message (backward compatible)
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Message, MessageRead


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
        @ns.param('for_agent', 'Get messages for this agent (direct + broadcasts) with per-agent read status', type=str)
        @ns.param('from_agent', 'Filter by sender agent ID only', type=str)
        @ns.param('to_agent', 'Filter by recipient agent ID only', type=str)
        @ns.param('include_readers', 'Include list of agents who have read each message', type=bool, default=False)
        @ns.param('include_thread_info', 'Include reply_count and has_parent for each message', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self):
            """
            Get all messages across all channels with optional filters.

            When for_agent is provided:
            - Returns messages TO this agent + all broadcasts
            - Uses per-agent read tracking for is_read status
            - unread_only uses per-agent read tracking

            When for_agent is not provided:
            - Returns all messages matching other filters
            - Uses legacy global read_at for is_read status
            """
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            channel = request.args.get('channel')
            for_agent = request.args.get('for_agent')
            from_agent = request.args.get('from_agent')
            to_agent = request.args.get('to_agent')
            include_readers = request.args.get('include_readers', 'false').lower() == 'true'
            include_thread_info = request.args.get('include_thread_info', 'false').lower() == 'true'

            # Per-agent mode: use MessageRead-aware queries
            if for_agent:
                if unread_only:
                    messages = Message.get_unread_for_agent(for_agent, channel=channel, limit=limit)
                else:
                    messages = Message.get_for_agent(for_agent, limit=limit, unread_only=False)
                    if channel:
                        messages = [m for m in messages if m.channel == channel]

                return {
                    'success': True,
                    'msg': f'Retrieved {len(messages)} messages for {for_agent}',
                    'data': {
                        'messages': [m.to_dict(for_agent=for_agent, include_readers=include_readers, include_thread_info=include_thread_info) for m in messages]
                    }
                }

            # Legacy mode: direct query with global read_at
            query = Message.query

            # Filter by channel
            if channel:
                query = query.filter(Message.channel == channel)

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
        def post(self):
            """Post a new message to a channel. Can be from an agent or a human. Can be a reply to another message."""
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

            # Validate reply_to_key if provided
            reply_to_key = data.get('reply_to_key')
            if reply_to_key:
                parent = Message.get_by_key(reply_to_key)
                if not parent:
                    return {'success': False, 'msg': f'Parent message {reply_to_key} not found'}, 404

            # Use from_human as from_agent if no agent specified (prefix with "human:")
            from_agent = data.get('from_agent')
            if not from_agent and data.get('from_human'):
                from_agent = f"human:{data['from_human']}"

            message = Message(
                channel=data['channel'],
                from_agent=from_agent,
                to_agent=data.get('to_agent'),
                reply_to_key=reply_to_key,
                message_type=data['message_type'],
                content=data['content'],
                priority=data.get('priority', 'normal')
            )

            try:
                message.save()
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
        @ns.marshal_with(response_model)
        def get(self, channel):
            """Get messages from a channel with optional per-agent read tracking."""
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            for_agent = request.args.get('for_agent')

            if for_agent and unread_only:
                # Per-agent unread filtering
                messages = Message.get_unread_for_agent(for_agent, channel=channel, limit=limit)
                unread_count = len(messages)
            else:
                query = Message.query.filter_by(channel=channel)

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
        @ns.marshal_with(response_model)
        def get(self, channel, timestamp):
            """Get messages from a channel since a timestamp."""
            limit = request.args.get('limit', 50, type=int)

            messages = Message.get_by_channel(channel, limit=limit, since=timestamp)

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} new messages',
                'data': {
                    'messages': [m.to_dict() for m in messages]
                }
            }

    @ns.route('/mark-read/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class MarkMessageRead(Resource):
        @ns.doc('mark_message_read')
        @ns.param('agent_id', 'Agent marking as read (for per-agent tracking)', type=str)
        @ns.marshal_with(response_model)
        def post(self, message_key):
            """
            Mark a message as read.

            If agent_id is provided, creates a per-agent read record (MessageRead).
            If agent_id is not provided, uses legacy global read_at field.
            """
            message = Message.get_by_key(message_key)
            if not message:
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
        def delete(self):
            """
            Delete all messages from the queue.

            This is a destructive operation that removes all messages
            and their read tracking records.
            """
            from api.models import db

            try:
                # Delete all read tracking records first
                MessageRead.query.delete()

                # Delete all messages
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
        @ns.marshal_with(response_model)
        def post(self):
            """
            Mark all unread messages as read for an agent.

            Requires agent_id to use per-agent read tracking.
            Marks all messages visible to this agent (direct + broadcasts) as read.
            """
            agent_id = request.args.get('agent_id')
            channel = request.args.get('channel')

            if not agent_id:
                return {'success': False, 'msg': 'agent_id is required for per-agent read tracking'}, 400

            try:
                # Get unread messages for this agent
                unread_messages = Message.get_unread_for_agent(agent_id, channel=channel, limit=1000)
                count = len(unread_messages)

                # Mark each as read by this agent
                message_keys = [m.message_key for m in unread_messages]
                if message_keys:
                    MessageRead.mark_all_read_for_agent(agent_id, message_keys)

                filters_applied = [f"agent_id={agent_id}"]
                if channel:
                    filters_applied.append(f"channel={channel}")
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

    @ns.route('/detail/<string:message_key>')
    @ns.param('message_key', 'Message identifier')
    class MessageDetail(Resource):
        @ns.doc('get_message_detail')
        @ns.param('include_thread', 'Include parent and replies', type=bool, default=True)
        @ns.param('include_readers', 'Include list of agents who have read', type=bool, default=True)
        @ns.param('for_agent', 'Get per-agent read status', type=str)
        @ns.marshal_with(response_model)
        def get(self, message_key):
            """
            Get a single message with full thread context.

            Returns the message along with its parent (if reply) and direct replies.
            """
            include_thread = request.args.get('include_thread', 'true').lower() == 'true'
            include_readers = request.args.get('include_readers', 'true').lower() == 'true'
            for_agent = request.args.get('for_agent')

            message = Message.get_by_key(message_key)
            if not message:
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

            return {
                'success': True,
                'msg': 'Message retrieved',
                'data': result
            }
