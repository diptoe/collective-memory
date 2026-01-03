"""
Collective Memory Platform - Message Model

Inter-agent messages for coordination and communication.
"""
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Message(BaseModel):
    """
    Inter-agent message for coordination.

    Message types: question, handoff, announcement, status
    Priority levels: high, normal, low
    """
    __tablename__ = 'messages'

    message_key = Column(String(36), primary_key=True, default=get_key)
    channel = Column(String(100), nullable=False, index=True)
    from_agent = Column(String(100), nullable=False)
    to_agent = Column(String(100), nullable=True)  # null = broadcast
    message_type = Column(String(50), nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    priority = Column(String(20), default='normal')
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_now)

    # Indexes for message retrieval
    __table_args__ = (
        Index('ix_messages_channel_created', 'channel', 'created_at'),
        Index('ix_messages_to_agent', 'to_agent'),
    )

    _default_fields = ['message_key', 'channel', 'from_agent', 'to_agent', 'message_type', 'content', 'priority']
    _readonly_fields = ['message_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def get_by_channel(cls, channel: str, limit: int = 50, since: str = None) -> list['Message']:
        """Get messages from a channel, optionally since a timestamp."""
        query = cls.query.filter_by(channel=channel)
        if since:
            from datetime import datetime
            since_dt = datetime.fromisoformat(since)
            query = query.filter(cls.created_at > since_dt)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_for_agent(cls, agent_id: str, limit: int = 50, unread_only: bool = False) -> list['Message']:
        """Get messages for a specific agent (direct or broadcast)."""
        query = cls.query.filter(
            (cls.to_agent == agent_id) | (cls.to_agent.is_(None))
        )
        if unread_only:
            query = query.filter(cls.read_at.is_(None))
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_unread_count(cls, channel: str) -> int:
        """Get count of unread messages in a channel."""
        return cls.query.filter_by(channel=channel).filter(cls.read_at.is_(None)).count()

    def mark_read(self) -> bool:
        """Mark the message as read."""
        self.read_at = get_now()
        return self.save()

    def to_dict(self, include_read_status: bool = True) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        if include_read_status:
            result['is_read'] = self.read_at is not None
        return result
