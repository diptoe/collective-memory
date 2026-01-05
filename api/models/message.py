"""
Collective Memory Platform - Message Model

Inter-agent messages for coordination and communication.

Message delivery modes:
- Direct: to_agent is set to a specific agent_id
- Broadcast: to_agent is null (visible to all agents in channel)

Read tracking is handled per-agent via the MessageRead table.
"""
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Message(BaseModel):
    """
    Inter-agent message for coordination.

    Message types: question, handoff, announcement, status
    Priority levels: high, normal, low

    Read tracking:
    - For broadcasts: each agent has their own read status via MessageRead
    - For direct messages: recipient tracks via MessageRead
    - Legacy read_at field kept for backward compatibility
    """
    __tablename__ = 'messages'

    message_key = Column(String(36), primary_key=True, default=get_key)
    channel = Column(String(100), nullable=False, index=True)
    from_agent = Column(String(100), nullable=False)
    to_agent = Column(String(100), nullable=True)  # null = broadcast to channel
    message_type = Column(String(50), nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    priority = Column(String(20), default='normal')
    read_at = Column(DateTime(timezone=True), nullable=True)  # Legacy - use MessageRead
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
        return 2  # Bumped for MessageRead integration

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
        """
        Get messages for a specific agent.
        Includes direct messages TO this agent and all broadcasts (to_agent is null).
        """
        from api.models.message_read import MessageRead

        query = cls.query.filter(
            (cls.to_agent == agent_id) | (cls.to_agent.is_(None))
        )

        if unread_only:
            # Subquery to find messages this agent has read
            read_subquery = db.session.query(MessageRead.message_key).filter(
                MessageRead.agent_id == agent_id
            ).scalar_subquery()
            query = query.filter(~cls.message_key.in_(read_subquery))

        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_unread_count(cls, channel: str = None, agent_id: str = None) -> int:
        """
        Get count of unread messages.

        Args:
            channel: Filter by channel (optional)
            agent_id: Count unread for this specific agent (required for accurate count)
        """
        from api.models.message_read import MessageRead

        query = cls.query

        if channel:
            query = query.filter(cls.channel == channel)

        if agent_id:
            # Messages this agent should see (direct to them or broadcast)
            query = query.filter(
                (cls.to_agent == agent_id) | (cls.to_agent.is_(None))
            )
            # Exclude messages they've read
            read_subquery = db.session.query(MessageRead.message_key).filter(
                MessageRead.agent_id == agent_id
            ).scalar_subquery()
            query = query.filter(~cls.message_key.in_(read_subquery))
        else:
            # Legacy: count messages with no read_at (less accurate for broadcasts)
            query = query.filter(cls.read_at.is_(None))

        return query.count()

    @classmethod
    def get_unread_for_agent(cls, agent_id: str, channel: str = None, limit: int = 50) -> list['Message']:
        """Get unread messages for an agent, optionally filtered by channel."""
        from api.models.message_read import MessageRead

        query = cls.query.filter(
            (cls.to_agent == agent_id) | (cls.to_agent.is_(None))
        )

        if channel:
            query = query.filter(cls.channel == channel)

        # Exclude messages they've read
        read_subquery = db.session.query(MessageRead.message_key).filter(
            MessageRead.agent_id == agent_id
        ).scalar_subquery()
        query = query.filter(~cls.message_key.in_(read_subquery))

        return query.order_by(cls.created_at.desc()).limit(limit).all()

    def mark_read(self, agent_id: str = None) -> bool:
        """
        Mark the message as read.

        Args:
            agent_id: The agent marking it read (required for proper tracking)
        """
        from api.models.message_read import MessageRead

        if agent_id:
            MessageRead.mark_read(self.message_key, agent_id)
            return True
        else:
            # Legacy behavior - mark globally
            self.read_at = get_now()
            return self.save()

    def is_read_by(self, agent_id: str) -> bool:
        """Check if a specific agent has read this message."""
        from api.models.message_read import MessageRead
        return MessageRead.has_read(self.message_key, agent_id)

    def get_readers(self) -> list[str]:
        """Get list of agent_ids who have read this message."""
        from api.models.message_read import MessageRead
        reads = MessageRead.get_readers(self.message_key)
        return [r.agent_id for r in reads]

    def to_dict(self, include_read_status: bool = True, for_agent: str = None, include_readers: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_read_status: Include is_read field
            for_agent: Check read status for this specific agent
            include_readers: Include list of agents who have read this message
        """
        result = super().to_dict()
        if include_read_status:
            if for_agent:
                result['is_read'] = self.is_read_by(for_agent)
            else:
                # Legacy: use read_at field
                result['is_read'] = self.read_at is not None

        if include_readers:
            from api.models.message_read import MessageRead
            reads = MessageRead.get_readers(self.message_key)
            result['readers'] = [{'agent_id': r.agent_id, 'read_at': r.read_at.isoformat() if r.read_at else None} for r in reads]
            result['read_count'] = len(reads)

        return result
