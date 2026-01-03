"""
Collective Memory Platform - ChatMessage Model

Individual messages within a conversation.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from api.models.base import BaseModel, db, get_key, get_now


class ChatMessage(BaseModel):
    """
    A single message within a conversation.

    Roles: user, assistant, system
    """
    __tablename__ = 'chat_messages'

    message_key = Column(String(36), primary_key=True, default=get_key)
    conversation_key = Column(String(36), ForeignKey('conversations.conversation_key'), nullable=False, index=True)
    persona_key = Column(String(36), ForeignKey('personas.persona_key'), nullable=True)  # null = human message
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    extra_data = Column(JSONB, default=dict)  # tokens used, model response metadata - renamed from 'metadata'
    created_at = Column(DateTime(timezone=True), default=get_now)

    # Relationships
    conversation = relationship('Conversation', backref='messages')
    persona = relationship('Persona', backref='chat_messages')

    # Index for message retrieval
    __table_args__ = (
        Index('ix_chat_messages_conversation_created', 'conversation_key', 'created_at'),
    )

    _default_fields = ['message_key', 'conversation_key', 'role', 'content']
    _readonly_fields = ['message_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def get_by_conversation(cls, conversation_key: str, limit: int = 100, offset: int = 0) -> list['ChatMessage']:
        """Get messages for a conversation."""
        return cls.query.filter_by(
            conversation_key=conversation_key
        ).order_by(cls.created_at.asc()).limit(limit).offset(offset).all()

    @classmethod
    def get_latest(cls, conversation_key: str, count: int = 10) -> list['ChatMessage']:
        """Get the latest N messages for a conversation."""
        messages = cls.query.filter_by(
            conversation_key=conversation_key
        ).order_by(cls.created_at.desc()).limit(count).all()
        return list(reversed(messages))

    def to_dict(self, include_persona: bool = False) -> dict:
        """Convert to dictionary with optional persona details."""
        result = super().to_dict()

        if include_persona and self.persona:
            result['persona'] = {
                'name': self.persona.name,
                'color': self.persona.color,
                'avatar_url': self.persona.avatar_url
            }

        return result
