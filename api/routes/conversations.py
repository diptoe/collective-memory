"""
Collective Memory Platform - Conversation Routes

Chat conversation and message operations.
"""
from flask import request, Response
from flask_restx import Api, Resource, Namespace, fields
import json

from api.models import Conversation, ChatMessage, Persona, db


def register_conversation_routes(api: Api):
    """Register conversation routes with the API."""

    ns = api.namespace(
        'conversations',
        description='Chat conversation operations',
        path='/conversations'
    )

    # Define models for OpenAPI documentation
    conversation_model = ns.model('Conversation', {
        'conversation_key': fields.String(readonly=True, description='Unique conversation identifier'),
        'persona_key': fields.String(required=True, description='Persona key'),
        'agent_id': fields.String(description='Agent ID for agent-initiated conversations'),
        'title': fields.String(description='Conversation title'),
        'summary': fields.String(description='Conversation summary'),
        'message_count': fields.Integer(readonly=True),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    conversation_create = ns.model('ConversationCreate', {
        'persona_key': fields.String(required=True, description='Persona to chat with'),
        'title': fields.String(description='Initial title'),
        'initial_message': fields.String(description='Optional first message'),
    })

    message_model = ns.model('ChatMessage', {
        'message_key': fields.String(readonly=True, description='Unique message identifier'),
        'conversation_key': fields.String(description='Parent conversation'),
        'persona_key': fields.String(description='Persona key (null for user messages)'),
        'role': fields.String(description='Role: user, assistant, system'),
        'content': fields.String(description='Message content'),
        'extra_data': fields.Raw(description='Additional metadata / extra fields'),
        'created_at': fields.DateTime(readonly=True),
    })

    message_create = ns.model('MessageCreate', {
        'content': fields.String(required=True, description='Message content'),
        'role': fields.String(description='Role (defaults to user)', default='user'),
        'extra_data': fields.Raw(description='Optional extra fields / metadata'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class ConversationList(Resource):
        @ns.doc('list_conversations')
        @ns.param('persona_key', 'Filter by persona')
        @ns.param('limit', 'Maximum results', type=int, default=20)
        @ns.marshal_with(response_model)
        def get(self):
            """List conversations."""
            persona_key = request.args.get('persona_key')
            limit = request.args.get('limit', 20, type=int)

            if persona_key:
                conversations = Conversation.get_by_persona(persona_key, limit=limit)
            else:
                conversations = Conversation.get_recent(limit=limit)

            return {
                'success': True,
                'msg': f'Found {len(conversations)} conversations',
                'data': {
                    'conversations': [c.to_dict(include_persona=True) for c in conversations]
                }
            }

        @ns.doc('create_conversation')
        @ns.expect(conversation_create)
        @ns.marshal_with(response_model, code=201)
        def post(self):
            """Create a new conversation."""
            data = request.json

            if not data.get('persona_key'):
                return {'success': False, 'msg': 'persona_key is required'}, 400

            # Verify persona exists
            persona = Persona.get_by_key(data['persona_key'])
            if not persona:
                return {'success': False, 'msg': 'Persona not found'}, 404

            conversation = Conversation(
                persona_key=data['persona_key'],
                title=data.get('title', f'Chat with {persona.name}'),
                agent_id=data.get('agent_id')
            )

            try:
                conversation.save()

                # If initial message provided, create it
                if data.get('initial_message'):
                    message = ChatMessage(
                        conversation_key=conversation.conversation_key,
                        role='user',
                        content=data['initial_message']
                    )
                    message.save()

                return {
                    'success': True,
                    'msg': 'Conversation created',
                    'data': conversation.to_dict(include_persona=True)
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:conversation_key>')
    @ns.param('conversation_key', 'Conversation identifier')
    class ConversationDetail(Resource):
        @ns.doc('get_conversation')
        @ns.param('include_messages', 'Include messages', type=bool, default=True)
        @ns.marshal_with(response_model)
        def get(self, conversation_key):
            """Get a conversation with messages."""
            include_messages = request.args.get('include_messages', 'true').lower() == 'true'

            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            return {
                'success': True,
                'msg': 'Conversation retrieved',
                'data': conversation.to_dict(
                    include_messages=include_messages,
                    include_persona=True
                )
            }

        @ns.doc('update_conversation')
        @ns.marshal_with(response_model)
        def put(self, conversation_key):
            """Update conversation metadata."""
            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            data = request.json
            conversation.update_from_dict(data)

            try:
                conversation.save()
                return {
                    'success': True,
                    'msg': 'Conversation updated',
                    'data': conversation.to_dict(include_persona=True)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_conversation')
        @ns.marshal_with(response_model)
        def delete(self, conversation_key):
            """Delete a conversation and its messages."""
            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            try:
                # Delete all messages first
                ChatMessage.query.filter_by(
                    conversation_key=conversation_key
                ).delete()

                conversation.delete()
                return {
                    'success': True,
                    'msg': 'Conversation deleted',
                    'data': None
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:conversation_key>/messages')
    @ns.param('conversation_key', 'Conversation identifier')
    class ConversationMessages(Resource):
        @ns.doc('get_messages')
        @ns.param('limit', 'Maximum messages', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        def get(self, conversation_key):
            """Get messages for a conversation."""
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            messages = conversation.get_messages(limit=limit, offset=offset)

            return {
                'success': True,
                'msg': f'Retrieved {len(messages)} messages',
                'data': {
                    'messages': [m.to_dict(include_persona=True) for m in messages],
                    'total': conversation.get_message_count()
                }
            }

        @ns.doc('send_message')
        @ns.expect(message_create)
        @ns.marshal_with(response_model, code=201)
        def post(self, conversation_key):
            """Send a message to the conversation."""
            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            data = request.json

            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Backwards compatible: accept either `extra_data` (preferred) or `metadata` (legacy)
            extra_data = data.get('extra_data') or data.get('metadata', {})

            message = ChatMessage(
                conversation_key=conversation_key,
                role=data.get('role', 'user'),
                content=data['content'],
                extra_data=extra_data
            )

            try:
                message.save()

                # Update conversation timestamp
                conversation.save()

                return {
                    'success': True,
                    'msg': 'Message sent',
                    'data': message.to_dict(include_persona=True)
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:conversation_key>/chat')
    @ns.param('conversation_key', 'Conversation identifier')
    class ConversationChat(Resource):
        @ns.doc('chat_with_persona')
        @ns.expect(message_create)
        @ns.marshal_with(response_model, code=201)
        def post(self, conversation_key):
            """
            Send a message and get AI response (non-streaming).

            This endpoint saves the user message, generates an AI response,
            and returns both messages. Use this for MCP/API integrations.
            For real-time streaming, use the /stream endpoint instead.
            """
            import asyncio
            from api.services.chat import chat_service

            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            data = request.json

            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Save user message
            user_message = ChatMessage(
                conversation_key=conversation_key,
                role='user',
                content=data['content']
            )
            user_message.save()

            persona = conversation.persona
            if not persona:
                return {'success': False, 'msg': 'Conversation has no associated persona'}, 400

            # Get conversation history for context
            messages = conversation.get_messages(limit=20)
            history = [
                {'role': m.role, 'content': m.content}
                for m in messages[:-1]  # Exclude the just-added user message
            ]

            # Generate AI response (non-streaming)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        chat_service.get_response(
                            conversation_key=conversation_key,
                            user_message=data['content'],
                            persona_key=persona.persona_key,
                            model='gemini-3-flash-preview',
                            system_prompt=persona.system_prompt or f"You are {persona.name}. {persona.role or ''}",
                            history=history,
                            inject_context=True,
                            max_tokens=4086,
                            temperature=0.7,
                        )   
                    )
                except Exception as e:
                    return {'success': False, 'msg': f'AI response failed: {str(e)}'}, 500
                finally:
                    loop.close()

                # Get the saved assistant message
                assistant_message = ChatMessage.get_by_key(result.get('message_key')) if result.get('message_key') else None

                return {
                    'success': True,
                    'msg': 'Chat response generated',
                    'data': {
                        'user_message': user_message.to_dict(),
                        'assistant_message': assistant_message.to_dict() if assistant_message else {
                            'content': result.get('content', ''),
                            'role': 'assistant'
                        },
                        'context': result.get('context'),
                        'usage': result.get('usage'),
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': f'AI response failed: {str(e)}'}, 500

    @ns.route('/<string:conversation_key>/messages/stream')
    @ns.param('conversation_key', 'Conversation identifier')
    class ConversationStream(Resource):
        @ns.doc('stream_response')
        @ns.expect(message_create)
        def post(self, conversation_key):
            """
            Send a message and stream the AI response.

            Returns Server-Sent Events (SSE) with streaming content.
            """
            import asyncio
            from api.services.chat import chat_service
            from api.utils.streaming import sse_format, sse_error, create_streaming_response

            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            data = request.json

            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Save user message
            user_message = ChatMessage(
                conversation_key=conversation_key,
                role='user',
                content=data['content']
            )
            user_message.save()

            persona = conversation.persona

            # Get conversation history for context
            messages = conversation.get_messages(limit=20)
            history = [
                {'role': m.role, 'content': m.content}
                for m in messages[:-1]  # Exclude the just-added user message
            ]

            # Capture app for use in async context
            from flask import current_app
            app = current_app._get_current_object()

            def generate_response():
                """Generator for streaming response."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    async def stream_chunks():
                        async for chunk in chat_service.stream_response(
                            conversation_key=conversation_key,
                            user_message=data['content'],
                            persona_key=persona.persona_key,
                            model='gemini-3-flash-preview',
                            system_prompt=persona.system_prompt or f"You are {persona.name}. {persona.role or ''}",
                            history=history,
                            inject_context=True,
                            max_tokens=4086,
                            temperature=data.get('temperature', 0.7),
                            app=app,
                        ):
                            yield sse_format(chunk.to_dict())

                    # Run async generator in sync context
                    async_gen = stream_chunks()
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break

                except Exception as e:
                    yield sse_error(str(e))
                finally:
                    loop.close()

            headers = create_streaming_response()
            return Response(
                generate_response(),
                mimetype='text/event-stream',
                headers=headers
            )

    @ns.route('/<string:conversation_key>/clear')
    @ns.param('conversation_key', 'Conversation identifier')
    class ConversationClear(Resource):
        @ns.doc('clear_conversation')
        @ns.marshal_with(response_model)
        def delete(self, conversation_key):
            """Remove all messages from a conversation (conversation remains)."""
            conversation = Conversation.get_by_key(conversation_key)
            if not conversation:
                return {'success': False, 'msg': 'Conversation not found'}, 404

            try:
                # Delete all messages for this conversation
                deleted = ChatMessage.query.filter_by(conversation_key=conversation_key).delete()
                db.session.commit()

                # Touch conversation updated_at (and clear summary if present)
                conversation.summary = None
                conversation.save()

                return {
                    'success': True,
                    'msg': f'Cleared {deleted} messages',
                    'data': {
                        'conversation_key': conversation_key,
                        'deleted': deleted,
                        'message_count': 0,
                    }
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500
