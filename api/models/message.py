"""
Collective Memory Platform - Message Model

Inter-agent messages for coordination and communication.

Message delivery modes:
- Direct: to_agent is set to a specific agent_id
- Broadcast: to_agent is null (visible to all agents in channel)

Threading:
- reply_to_key links to the parent message (null for top-level messages)

Read tracking is handled per-agent via the MessageRead table.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Message(BaseModel):
    """
    Inter-agent message for coordination.

    Message types: status, announcement, request, task, message
    Priority levels: normal, high, urgent

    Threading:
    - reply_to_key links to parent message for threaded conversations
    - Top-level messages have reply_to_key = null

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
    reply_to_key = Column(String(36), ForeignKey('messages.message_key'), nullable=True, index=True)
    message_type = Column(String(50), nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    priority = Column(String(20), default='normal')
    autonomous = Column(Boolean, default=False, index=True)  # Task requiring autonomous action
    confirmed = Column(Boolean, default=False)  # Operator confirmed task completion
    confirmed_by = Column(String(100), nullable=True)  # Agent/human who confirmed
    confirmed_at = Column(DateTime(timezone=True), nullable=True)  # When confirmed
    entity_keys = Column(JSONB, default=list)  # Linked entity keys for knowledge graph connection
    context_domain = Column(String(36), nullable=True, index=True)  # Domain for multi-tenancy isolation
    read_at = Column(DateTime(timezone=True), nullable=True)  # Legacy - use MessageRead
    created_at = Column(DateTime(timezone=True), default=get_now)

    # Indexes for message retrieval
    __table_args__ = (
        Index('ix_messages_channel_created', 'channel', 'created_at'),
        Index('ix_messages_to_agent', 'to_agent'),
        Index('ix_messages_reply_to', 'reply_to_key'),
    )

    _default_fields = ['message_key', 'channel', 'from_agent', 'to_agent', 'reply_to_key', 'message_type', 'content', 'priority', 'autonomous', 'confirmed', 'confirmed_by', 'confirmed_at', 'entity_keys', 'context_domain']
    _readonly_fields = ['message_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 7  # Bumped for context_domain field

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

    @classmethod
    def get_unread_autonomous_count(cls, agent_id: str) -> int:
        """
        Get count of unread autonomous messages for an agent.

        These are high-priority tasks that require the agent to act autonomously
        and reply when complete.
        """
        from api.models.message_read import MessageRead

        query = cls.query.filter(
            cls.autonomous == True,
            (cls.to_agent == agent_id) | (cls.to_agent.is_(None))
        )

        # Exclude messages they've read
        read_subquery = db.session.query(MessageRead.message_key).filter(
            MessageRead.agent_id == agent_id
        ).scalar_subquery()
        query = query.filter(~cls.message_key.in_(read_subquery))

        return query.count()

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

    def confirm(self, confirmed_by: str) -> bool:
        """
        Confirm task completion on this message.

        Used by operators to explicitly confirm that an autonomous task
        has been completed satisfactorily.

        Args:
            confirmed_by: Agent ID or human name who confirmed
        """
        self.confirmed = True
        self.confirmed_by = confirmed_by
        self.confirmed_at = get_now()
        return self.save()

    def unconfirm(self) -> bool:
        """
        Remove confirmation from this message.

        Used when an operator realizes more work is needed after confirming.
        """
        self.confirmed = False
        self.confirmed_by = None
        self.confirmed_at = None
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

    def get_parent(self) -> 'Message':
        """Get the parent message this is replying to."""
        if not self.reply_to_key:
            return None
        return Message.get_by_key(self.reply_to_key)

    def get_replies(self, limit: int = 50) -> list['Message']:
        """Get direct replies to this message."""
        return Message.query.filter_by(reply_to_key=self.message_key)\
            .order_by(Message.created_at.asc()).limit(limit).all()

    def get_reply_count(self) -> int:
        """Get count of replies to this message."""
        return Message.query.filter_by(reply_to_key=self.message_key).count()

    @classmethod
    def get_thread(cls, message_key: str) -> dict:
        """
        Get a full thread starting from a message.
        Returns the root message and all descendants.
        """
        # Find root of thread
        msg = cls.get_by_key(message_key)
        if not msg:
            return None

        # Walk up to find root
        root = msg
        while root.reply_to_key:
            parent = root.get_parent()
            if parent:
                root = parent
            else:
                break

        # Build thread from root
        return {
            'root': root,
            'replies': cls._get_nested_replies(root.message_key)
        }

    @classmethod
    def _get_nested_replies(cls, message_key: str, depth: int = 0, max_depth: int = 10) -> list:
        """Recursively get nested replies."""
        if depth >= max_depth:
            return []

        replies = cls.query.filter_by(reply_to_key=message_key)\
            .order_by(cls.created_at.asc()).all()

        result = []
        for reply in replies:
            result.append({
                'message': reply,
                'replies': cls._get_nested_replies(reply.message_key, depth + 1, max_depth)
            })
        return result

    @classmethod
    def get_thread_entity_keys(cls, message_key: str) -> list[str]:
        """
        Get all unique entity keys linked across a thread.
        Aggregates entity_keys from root message and all replies.
        """
        thread = cls.get_thread(message_key)
        if not thread:
            return []

        entity_keys = set()

        # Add from root
        root = thread.get('root')
        if root and root.entity_keys:
            entity_keys.update(root.entity_keys)

        # Recursively collect from replies
        def collect_from_replies(replies):
            for item in replies:
                msg = item.get('message')
                if msg and msg.entity_keys:
                    entity_keys.update(msg.entity_keys)
                collect_from_replies(item.get('replies', []))

        collect_from_replies(thread.get('replies', []))
        return list(entity_keys)

    def to_dict(self, include_read_status: bool = True, for_agent: str = None, include_readers: bool = False, include_thread_info: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_read_status: Include is_read field
            for_agent: Check read status for this specific agent
            include_readers: Include list of agents who have read this message
            include_thread_info: Include reply_count and has_parent indicators
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

        if include_thread_info:
            result['reply_count'] = self.get_reply_count()
            result['has_parent'] = self.reply_to_key is not None

        return result
