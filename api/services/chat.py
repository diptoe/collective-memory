"""
Collective Memory Platform - Chat Service

Orchestrates AI persona chat with streaming responses.
Integrates providers and context injection.
"""

import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional, List
from dataclasses import dataclass

from api.providers import get_provider, StreamChunk, Message
from api.services.context import context_service, ContextResult

logger = logging.getLogger(__name__)


@dataclass
class ChatStreamChunk:
    """Represents a chunk of chat stream output."""
    type: str  # 'content', 'context', 'done', 'error'
    content: str = ""
    done: bool = False
    message_key: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'type': self.type,
            'content': self.content,
            'done': self.done,
        }
        if self.message_key:
            result['message_key'] = self.message_key
        if self.context:
            result['context'] = self.context
        if self.usage:
            result['usage'] = self.usage
        return result


class ChatService:
    """
    Service for handling AI persona chat with streaming.

    Orchestrates:
    - Context retrieval from knowledge graph
    - AI provider selection based on model
    - Streaming responses
    - Message persistence
    """

    def __init__(self):
        self.context_service = context_service

    def _build_system_prompt(
        self,
        persona_prompt: str,
        context: ContextResult
    ) -> str:
        """
        Build system prompt with injected context.

        Args:
            persona_prompt: The persona's base system prompt
            context: Retrieved context from knowledge graph

        Returns:
            Complete system prompt with context
        """
        parts = [persona_prompt]

        if context.context_text and context.context_text != "No relevant context found.":
            parts.append("\n\n## Knowledge Graph Context")
            parts.append(context.context_text)

            if context.truncated:
                parts.append("\n*Note: Context was truncated to fit token limits.*")

        return "\n".join(parts)

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Message]:
        """Convert message dictionaries to Message objects."""
        return [
            Message(
                role=msg.get('role', 'user'),
                content=msg.get('content', '')
            )
            for msg in messages
        ]

    async def stream_response(
        self,
        conversation_key: str,
        user_message: str,
        persona_key: str,
        model: str,
        system_prompt: str,
        history: List[Dict[str, Any]] = None,
        inject_context: bool = True,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        app=None,  # Flask app for database context
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """
        Stream a response from the AI persona.

        Args:
            conversation_key: Key of the conversation
            user_message: The user's message
            persona_key: Key of the persona
            model: Model identifier (e.g., 'claude-3-sonnet')
            system_prompt: Persona's system prompt
            history: Previous messages in conversation
            inject_context: Whether to inject knowledge graph context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            ChatStreamChunk objects
        """
        from api.models import ChatMessage
        from api.models import db

        history = history or []

        # Get context from knowledge graph (within app context if provided)
        context = None
        if inject_context:
            try:
                if app:
                    with app.app_context():
                        context = self.context_service.get_context(user_message)
                else:
                    context = self.context_service.get_context(user_message)

                yield ChatStreamChunk(
                    type='context',
                    context={
                        'entity_count': len(context.entities),
                        'relationship_count': len(context.relationships),
                        'token_count': context.token_count,
                        'truncated': context.truncated,
                        'cache_hit': context.cache_hit,
                    }
                )
            except Exception as e:
                logger.warning(f"Context retrieval failed: {e}")
                context = ContextResult(
                    context_text="",
                    entities=[],
                    relationships=[],
                    token_count=0
                )

        # Build system prompt with context
        full_system_prompt = self._build_system_prompt(
            system_prompt,
            context
        ) if context else system_prompt

        # Convert history to Message objects
        messages = self._convert_messages(history)

        # Add current user message
        messages.append(Message(role='user', content=user_message))

        # Get provider for model
        try:
            provider = get_provider(model)
            logger.info(f"Using provider '{provider.name}' for model '{model}'")
        except ValueError as e:
            logger.error(f"Provider error: {e}")
            yield ChatStreamChunk(
                type='error',
                content=str(e),
                done=True
            )
            return

        # Stream response
        full_content = ""
        usage = None

        try:
            async for chunk in provider.stream_completion(
                messages=messages,
                model=model,
                system_prompt=full_system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            ):
                if chunk.content:
                    full_content += chunk.content
                    yield ChatStreamChunk(
                        type='content',
                        content=chunk.content,
                        done=False
                    )

                if chunk.done:
                    usage = chunk.usage

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield ChatStreamChunk(
                type='error',
                content=f"AI response error: {str(e)}",
                done=True
            )
            return

        # Save assistant message to database (within app context)
        message_key = None
        try:
            if app:
                with app.app_context():
                    assistant_message = ChatMessage(
                        conversation_key=conversation_key,
                        role='assistant',
                        content=full_content,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(assistant_message)
                    db.session.commit()
                    message_key = assistant_message.message_key
            else:
                # Fallback if no app provided (shouldn't happen in normal use)
                assistant_message = ChatMessage(
                    conversation_key=conversation_key,
                    role='assistant',
                    content=full_content,
                    created_at=datetime.utcnow()
                )
                db.session.add(assistant_message)
                db.session.commit()
                message_key = assistant_message.message_key

            yield ChatStreamChunk(
                type='done',
                content='',
                done=True,
                message_key=message_key,
                usage=usage
            )

        except Exception as e:
            logger.error(f"Message save error: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
            yield ChatStreamChunk(
                type='error',
                content=f"Failed to save message: {str(e)}",
                done=True
            )

    async def get_response(
        self,
        conversation_key: str,
        user_message: str,
        persona_key: str,
        model: str,
        system_prompt: str,
        history: List[Dict[str, Any]] = None,
        inject_context: bool = True,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Get a complete (non-streaming) response.

        Returns the full response after accumulating all chunks.
        """
        content = ""
        message_key = None
        usage = None
        context_info = None

        async for chunk in self.stream_response(
            conversation_key=conversation_key,
            user_message=user_message,
            persona_key=persona_key,
            model=model,
            system_prompt=system_prompt,
            history=history,
            inject_context=inject_context,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            if chunk.type == 'content':
                content += chunk.content
            elif chunk.type == 'context':
                context_info = chunk.context
            elif chunk.type == 'done':
                message_key = chunk.message_key
                usage = chunk.usage
            elif chunk.type == 'error':
                raise Exception(chunk.content)

        return {
            'content': content,
            'message_key': message_key,
            'usage': usage,
            'context': context_info,
        }


# Global service instance
chat_service = ChatService()
