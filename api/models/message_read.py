"""
Collective Memory Platform - MessageRead Model

Tracks which agents have read which messages.
Enables per-agent read tracking for broadcast/channel messages.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint

from api.models.base import BaseModel, db, get_key, get_now


class MessageRead(BaseModel):
    """
    Tracks when an agent has read a message.

    For broadcast messages (to_agent is null), each agent creates their own
    MessageRead record when they read the message.

    For direct messages (to_agent is set), the recipient creates a record.
    """
    __tablename__ = 'message_reads'

    read_key = Column(String(36), primary_key=True, default=get_key)
    message_key = Column(String(36), ForeignKey('messages.message_key'), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), default=get_now)

    # Ensure each agent can only mark a message as read once
    __table_args__ = (
        UniqueConstraint('message_key', 'agent_id', name='uq_message_agent_read'),
    )

    _default_fields = ['read_key', 'message_key', 'agent_id', 'read_at']
    _readonly_fields = ['read_key', 'read_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def has_read(cls, message_key: str, agent_id: str) -> bool:
        """Check if an agent has read a message."""
        return cls.query.filter_by(
            message_key=message_key,
            agent_id=agent_id
        ).first() is not None

    @classmethod
    def get_read_record(cls, message_key: str, agent_id: str) -> 'MessageRead':
        """Get the read record for a message/agent combination."""
        return cls.query.filter_by(
            message_key=message_key,
            agent_id=agent_id
        ).first()

    @classmethod
    def mark_read(cls, message_key: str, agent_id: str) -> 'MessageRead':
        """Mark a message as read by an agent. Returns existing record if already read."""
        existing = cls.get_read_record(message_key, agent_id)
        if existing:
            return existing

        read_record = cls(
            message_key=message_key,
            agent_id=agent_id
        )
        read_record.save()
        return read_record

    @classmethod
    def get_readers(cls, message_key: str) -> list['MessageRead']:
        """Get all agents who have read a message."""
        return cls.query.filter_by(message_key=message_key).all()

    @classmethod
    def get_read_count(cls, message_key: str) -> int:
        """Get count of agents who have read a message."""
        return cls.query.filter_by(message_key=message_key).count()

    @classmethod
    def get_unread_messages_for_agent(cls, agent_id: str, message_keys: list[str]) -> list[str]:
        """
        Given a list of message_keys, return those the agent hasn't read.
        """
        read_keys = db.session.query(cls.message_key).filter(
            cls.agent_id == agent_id,
            cls.message_key.in_(message_keys)
        ).all()
        read_keys_set = {r[0] for r in read_keys}
        return [mk for mk in message_keys if mk not in read_keys_set]

    @classmethod
    def mark_all_read_for_agent(cls, agent_id: str, message_keys: list[str]) -> int:
        """
        Mark multiple messages as read by an agent.
        Returns count of newly marked messages.
        """
        count = 0
        for message_key in message_keys:
            if not cls.has_read(message_key, agent_id):
                cls.mark_read(message_key, agent_id)
                count += 1
        return count
