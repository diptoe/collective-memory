"""
Collective Memory Platform - Message Routes

Inter-agent message queue operations.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Message


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
        'message_type': fields.String(required=True, description='Type: question, handoff, announcement, status'),
        'content': fields.Raw(required=True, description='Message content as JSON'),
        'priority': fields.String(description='Priority: high, normal, low'),
        'read_at': fields.DateTime(readonly=True),
        'is_read': fields.Boolean(readonly=True),
        'created_at': fields.DateTime(readonly=True),
    })

    message_create = ns.model('MessageCreate', {
        'channel': fields.String(required=True, description='Channel name'),
        'from_agent': fields.String(required=True, description='Sender agent ID'),
        'to_agent': fields.String(description='Recipient agent ID (null for broadcast)'),
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
        @ns.marshal_with(response_model)
        def get(self):
            """Get all messages across all channels."""
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'

            query = Message.query

            if unread_only:
                query = query.filter(Message.read_at.is_(None))

            messages = query.order_by(Message.created_at.desc()).limit(limit).all()

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict() for m in messages]
                }
            }

        @ns.doc('post_message')
        @ns.expect(message_create)
        @ns.marshal_with(response_model, code=201)
        def post(self):
            """Post a new message to a channel."""
            data = request.json

            # Validate required fields
            if not data.get('channel'):
                return {'success': False, 'msg': 'channel is required'}, 400
            if not data.get('from_agent'):
                return {'success': False, 'msg': 'from_agent is required'}, 400
            if not data.get('message_type'):
                return {'success': False, 'msg': 'message_type is required'}, 400
            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            message = Message(
                channel=data['channel'],
                from_agent=data['from_agent'],
                to_agent=data.get('to_agent'),
                message_type=data['message_type'],
                content=data['content'],
                priority=data.get('priority', 'normal')
            )

            try:
                message.save()
                return {
                    'success': True,
                    'msg': 'Message posted',
                    'data': message.to_dict()
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:channel>')
    @ns.param('channel', 'Channel name')
    class ChannelMessages(Resource):
        @ns.doc('get_channel_messages')
        @ns.param('limit', 'Maximum messages to return', type=int, default=50)
        @ns.param('unread_only', 'Only return unread messages', type=bool, default=False)
        @ns.marshal_with(response_model)
        def get(self, channel):
            """Get messages from a channel."""
            limit = request.args.get('limit', 50, type=int)
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'

            query = Message.query.filter_by(channel=channel)

            if unread_only:
                query = query.filter(Message.read_at.is_(None))

            messages = query.order_by(Message.created_at.desc()).limit(limit).all()
            unread_count = Message.get_unread_count(channel)

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict() for m in messages],
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
        @ns.marshal_with(response_model)
        def post(self, message_key):
            """Mark a message as read."""
            message = Message.get_by_key(message_key)
            if not message:
                return {'success': False, 'msg': 'Message not found'}, 404

            try:
                message.mark_read()
                return {
                    'success': True,
                    'msg': 'Message marked as read',
                    'data': message.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
