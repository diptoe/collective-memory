"""
Collective Memory Platform - Conversation Model

Chat conversations with personas.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from api.models.base import BaseModel, db, get_key, get_now


class Conversation(BaseModel):
    """
    A conversation session with a persona.

    Contains metadata about the conversation and links to chat messages.
    """
    __tablename__ = 'conversations'

    conversation_key = Column(String(36), primary_key=True, default=get_key)
    persona_key = Column(String(36), ForeignKey('personas.persona_key'), nullable=False, index=True)
    agent_id = Column(String(100), nullable=True)  # For agent-initiated conversations
    title = Column(String(255), nullable=True)  # Auto-generated or user-set
    summary = Column(Text, nullable=True)
    extracted_entities = Column(JSONB, default=list)
    extra_data = Column(JSONB, default=dict)  # renamed from 'metadata' which is reserved
    domain_key = Column(String(36), nullable=True, index=True)  # domain for multi-tenancy
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Relationship to Persona
    persona = relationship('Persona', backref='conversations')

    _default_fields = ['conversation_key', 'persona_key', 'title', 'summary', 'extracted_entities', 'domain_key']
    _readonly_fields = ['conversation_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 2

    @classmethod
    def migrate(cls) -> bool:
        """
        Migrate existing Conversation records to include domain_key.

        For conversations created before multi-tenancy, attempts to set domain_key
        based on the agent's owning user's domain. User-initiated conversations without
        an agent remain without a domain until manually assigned.
        """
        from api.models.agent import Agent
        from api.models.user import User

        migrated = False
        # Only migrate records that have NULL domain_key
        records = cls.query.filter(cls.domain_key.is_(None)).all()

        for r in records:
            # Try to get domain from the agent -> user -> domain
            if r.agent_id:
                agent = Agent.query.filter_by(agent_id=r.agent_id).first()
                if agent and agent.user_key:
                    user = User.query.get(agent.user_key)
                    if user and user.domain_key:
                        r.domain_key = user.domain_key
                        db.session.add(r)
                        migrated = True

        if migrated:
            db.session.commit()

        return migrated

    @classmethod
    def get_by_persona(cls, persona_key: str, limit: int = 50, domain_key: str = None) -> list['Conversation']:
        """Get conversations for a specific persona."""
        query = cls.query.filter_by(persona_key=persona_key)
        if domain_key:
            query = query.filter(cls.domain_key == domain_key)
        return query.order_by(cls.updated_at.desc()).limit(limit).all()

    @classmethod
    def get_recent(cls, limit: int = 20, domain_key: str = None) -> list['Conversation']:
        """Get most recent conversations across all personas."""
        query = cls.query
        if domain_key:
            query = query.filter(cls.domain_key == domain_key)
        return query.order_by(cls.updated_at.desc()).limit(limit).all()

    def get_messages(self, limit: int = 100, offset: int = 0) -> list:
        """Get messages for this conversation."""
        from api.models.chat_message import ChatMessage
        return ChatMessage.query.filter_by(
            conversation_key=self.conversation_key
        ).order_by(ChatMessage.created_at.asc()).limit(limit).offset(offset).all()

    def get_message_count(self) -> int:
        """Get total number of messages in conversation."""
        from api.models.chat_message import ChatMessage
        return ChatMessage.query.filter_by(
            conversation_key=self.conversation_key
        ).count()

    def to_dict(self, include_messages: bool = False, include_persona: bool = False) -> dict:
        """Convert to dictionary with optional includes."""
        result = super().to_dict()
        result['message_count'] = self.get_message_count()

        if include_persona and self.persona:
            result['persona'] = self.persona.to_dict()

        if include_messages:
            result['messages'] = [m.to_dict() for m in self.get_messages()]

        return result
