"""
Collective Memory Platform - Message Model

Inter-agent and user messages for coordination and communication.

Scope types define message visibility and routing:
- broadcast-domain: Visible to all agents and users in the domain
- broadcast-team: Visible to all agents and users in a specific team
- agent-agent: Direct message between two specific agents
- agent-user: Message from an agent to a specific user
- user-agent: Message from a user to a specific agent
- user-agents: Message from a user to all agents linked to them
- agent-agents: Message from an agent to all agents linked to a user

Threading:
- reply_to_key links to the parent message (null for top-level messages)

Read tracking is handled per-agent via the MessageRead table.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


# Valid scope values
VALID_SCOPES = [
    'broadcast-domain',   # Broadcast to everyone in domain
    'broadcast-team',     # Broadcast to everyone in team (requires team_key)
    'agent-agent',        # Direct message between two agents
    'agent-user',         # Agent sending to user
    'user-agent',         # User sending to agent
    'user-agents',        # User sending to all their linked agents
    'agent-agents',       # Agent sending to all agents linked to a user
]


class Message(BaseModel):
    """
    Inter-agent and user message for coordination.

    Message types: status, announcement, request, task, message, acknowledged, waiting, resumed
    Priority levels: normal, high, urgent

    Keys:
    - from_key: user_key or agent_key of the sender
    - to_key: user_key or agent_key of recipient (null for broadcasts)
    - user_key: For user-agents/agent-agents scopes, the user whose agents receive the message

    Scope determines visibility:
    - broadcast-domain: All in domain see it
    - broadcast-team: All in team_key see it
    - agent-agent: Only from_key and to_key see it
    - agent-user: Only from_key (agent) and to_key (user) see it
    - user-agent: Only from_key (user) and to_key (agent) see it
    - user-agents: from_key (user) and all agents linked to user_key
    - agent-agents: from_key (agent) and all agents linked to user_key

    Threading:
    - reply_to_key links to parent message for threaded conversations
    - Top-level messages have reply_to_key = null

    Read tracking:
    - Each agent tracks their own read status via MessageRead
    - Legacy read_at field kept for backward compatibility
    """
    __tablename__ = 'messages'

    message_key = Column(String(36), primary_key=True, default=get_key)
    channel = Column(String(100), nullable=False, index=True)
    from_key = Column(String(36), nullable=False, index=True)  # user_key or agent_key
    from_name = Column(String(200), nullable=True)  # Display name of sender (denormalized for readability)
    to_key = Column(String(36), nullable=True, index=True)  # user_key or agent_key (null for broadcasts)
    to_name = Column(String(200), nullable=True)  # Display name of recipient (denormalized for readability)
    user_key = Column(String(36), nullable=True, index=True)  # For user-agents/agent-agents scopes
    scope = Column(String(36), nullable=False, default='broadcast-domain', index=True)
    reply_to_key = Column(String(36), ForeignKey('messages.message_key'), nullable=True, index=True)
    message_type = Column(String(50), nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    priority = Column(String(20), default='normal')
    autonomous = Column(Boolean, default=False, index=True)  # Task requiring autonomous action
    confirmed = Column(Boolean, default=False)  # Operator confirmed task completion
    confirmed_by = Column(String(100), nullable=True)  # Agent/human who confirmed
    confirmed_at = Column(DateTime(timezone=True), nullable=True)  # When confirmed
    entity_keys = Column(JSONB, default=list)  # Linked entity keys for knowledge graph connection
    domain_key = Column(String(36), nullable=True, index=True)  # Domain for multi-tenancy isolation
    team_key = Column(String(36), nullable=True, index=True)  # Team scope (required for broadcast-team)
    read_at = Column(DateTime(timezone=True), nullable=True)  # Legacy - use MessageRead
    created_at = Column(DateTime(timezone=True), default=get_now)

    # Indexes for message retrieval
    __table_args__ = (
        Index('ix_messages_channel_created', 'channel', 'created_at'),
        Index('ix_messages_reply_to', 'reply_to_key'),
        Index('ix_messages_scope', 'scope'),
    )

    _default_fields = [
        'message_key', 'channel', 'from_key', 'from_name', 'to_key', 'to_name',
        'user_key', 'scope', 'reply_to_key', 'message_type', 'content', 'priority',
        'autonomous', 'confirmed', 'confirmed_by', 'confirmed_at', 'entity_keys',
        'domain_key', 'team_key'
    ]
    _readonly_fields = ['message_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 11  # Added from_name, to_name for display purposes

    @classmethod
    def resolve_name(cls, key: str) -> str:
        """
        Resolve a user_key or agent_key to a display name.

        Looks up in both User and Agent tables to find the name.
        Returns the key itself if no name is found.
        """
        if not key:
            return None

        # Try User table first
        from api.models.user import User
        user = User.query.filter_by(user_key=key).first()
        if user:
            return user.display_name

        # Try Agent table
        from api.models.agent import Agent
        agent = Agent.query.filter_by(agent_key=key).first()
        if agent:
            # Prefer persona name, then agent_id
            return agent.persona or agent.agent_id

        # Return key as fallback
        return key

    @classmethod
    def validate_scope(cls, scope: str, to_key: str = None, team_key: str = None, user_key: str = None) -> tuple[bool, str]:
        """
        Validate scope value and required fields.

        Returns:
            (is_valid, error_message)
        """
        if scope not in VALID_SCOPES:
            return False, f"Invalid scope: {scope}. Valid values: {VALID_SCOPES}"

        if scope == 'broadcast-team' and not team_key:
            return False, "broadcast-team scope requires team_key"

        if scope in ('agent-agent', 'agent-user', 'user-agent') and not to_key:
            return False, f"{scope} scope requires to_key"

        if scope in ('user-agents', 'agent-agents') and not user_key:
            return False, f"{scope} scope requires user_key"

        return True, None

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
    def get_for_agent(
        cls,
        agent_key: str,
        user_key: str = None,
        limit: int = 50,
        unread_only: bool = False,
        team_keys: list[str] = None,
        team_key_filter: str = None,
        domain_key: str = None
    ) -> list['Message']:
        """
        Get messages visible to a specific agent.

        An agent can see messages where:
        - scope=broadcast-domain and same domain_key
        - scope=broadcast-team and team_key in agent's team_keys
        - scope=agent-agent and (from_key=agent_key or to_key=agent_key)
        - scope=agent-user and from_key=agent_key
        - scope=user-agent and to_key=agent_key
        - scope=user-agents and user_key matches agent's linked user
        - scope=agent-agents and user_key matches agent's linked user

        Args:
            agent_key: The agent's key
            user_key: The user_key linked to this agent (for user-agents/agent-agents)
            limit: Maximum messages to return
            unread_only: Only return unread messages
            team_keys: List of team_keys the agent can access
            team_key_filter: Filter to a specific team only
            domain_key: The agent's domain_key
        """
        from api.models.message_read import MessageRead
        from sqlalchemy import or_, and_

        conditions = []

        # broadcast-domain: visible to all in domain
        if domain_key:
            conditions.append(
                and_(
                    cls.scope == 'broadcast-domain',
                    cls.domain_key == domain_key
                )
            )

        # broadcast-team: visible to team members
        if team_keys:
            if team_key_filter:
                # Filter to specific team
                conditions.append(
                    and_(
                        cls.scope == 'broadcast-team',
                        cls.team_key == team_key_filter
                    )
                )
            else:
                # All teams agent belongs to
                conditions.append(
                    and_(
                        cls.scope == 'broadcast-team',
                        cls.team_key.in_(team_keys)
                    )
                )

        # agent-agent: direct messages involving this agent
        conditions.append(
            and_(
                cls.scope == 'agent-agent',
                or_(cls.from_key == agent_key, cls.to_key == agent_key)
            )
        )

        # agent-user: messages from this agent to a user (agent sees their own)
        conditions.append(
            and_(
                cls.scope == 'agent-user',
                cls.from_key == agent_key
            )
        )

        # user-agent: messages from a user to this agent
        conditions.append(
            and_(
                cls.scope == 'user-agent',
                cls.to_key == agent_key
            )
        )

        # user-agents: messages from user to all their agents
        if user_key:
            conditions.append(
                and_(
                    cls.scope == 'user-agents',
                    cls.user_key == user_key
                )
            )

        # agent-agents: messages from agent to all agents of a user
        if user_key:
            conditions.append(
                and_(
                    cls.scope == 'agent-agents',
                    cls.user_key == user_key
                )
            )

        query = cls.query.filter(or_(*conditions))

        if unread_only:
            # Subquery to find messages this agent has read
            read_subquery = db.session.query(MessageRead.message_key).filter(
                MessageRead.reader_key == agent_key
            ).scalar_subquery()
            query = query.filter(~cls.message_key.in_(read_subquery))

        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_for_user(
        cls,
        user_key: str,
        limit: int = 50,
        unread_only: bool = False,
        team_keys: list[str] = None,
        team_key_filter: str = None,
        domain_key: str = None
    ) -> list['Message']:
        """
        Get messages visible to a specific user.

        A user can see messages where:
        - scope=broadcast-domain and same domain_key
        - scope=broadcast-team and team_key in user's team_keys
        - scope=agent-user and to_key=user_key
        - scope=user-agent and from_key=user_key
        - scope=user-agents and from_key=user_key or user_key matches

        Args:
            user_key: The user's key
            limit: Maximum messages to return
            unread_only: Only return unread messages (uses user_key for read tracking)
            team_keys: List of team_keys the user can access
            team_key_filter: Filter to a specific team only
            domain_key: The user's domain_key
        """
        from api.models.message_read import MessageRead
        from sqlalchemy import or_, and_

        conditions = []

        # broadcast-domain: visible to all in domain
        if domain_key:
            conditions.append(
                and_(
                    cls.scope == 'broadcast-domain',
                    cls.domain_key == domain_key
                )
            )

        # broadcast-team: visible to team members
        if team_keys:
            if team_key_filter:
                conditions.append(
                    and_(
                        cls.scope == 'broadcast-team',
                        cls.team_key == team_key_filter
                    )
                )
            else:
                conditions.append(
                    and_(
                        cls.scope == 'broadcast-team',
                        cls.team_key.in_(team_keys)
                    )
                )

        # agent-user: messages from an agent to this user
        conditions.append(
            and_(
                cls.scope == 'agent-user',
                cls.to_key == user_key
            )
        )

        # user-agent: messages from this user (user sees their own)
        conditions.append(
            and_(
                cls.scope == 'user-agent',
                cls.from_key == user_key
            )
        )

        # user-agents: messages from this user to their agents
        conditions.append(
            and_(
                cls.scope == 'user-agents',
                or_(cls.from_key == user_key, cls.user_key == user_key)
            )
        )

        query = cls.query.filter(or_(*conditions))

        if unread_only:
            # Use user_key for read tracking
            read_subquery = db.session.query(MessageRead.message_key).filter(
                MessageRead.reader_key == user_key  # Users use their user_key as agent_id
            ).scalar_subquery()
            query = query.filter(~cls.message_key.in_(read_subquery))

        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_unread_count(cls, agent_key: str = None, channel: str = None, domain_key: str = None) -> int:
        """
        Get count of unread messages for an agent.

        Args:
            agent_key: Count unread for this specific agent (required)
            channel: Filter by channel (optional)
            domain_key: The agent's domain_key
        """
        from api.models.message_read import MessageRead

        if not agent_key:
            return 0

        # Get messages visible to this agent
        query = cls.query.filter(cls.domain_key == domain_key) if domain_key else cls.query

        if channel:
            query = query.filter(cls.channel == channel)

        # Exclude messages they've read
        read_subquery = db.session.query(MessageRead.message_key).filter(
            MessageRead.reader_key == agent_key
        ).scalar_subquery()
        query = query.filter(~cls.message_key.in_(read_subquery))

        return query.count()

    @classmethod
    def get_unread_autonomous_count(
        cls,
        agent_key: str,
        user_key: str = None,
        team_keys: list[str] = None,
        domain_key: str = None
    ) -> int:
        """
        Get count of unread autonomous messages for an agent.

        Args:
            agent_key: The agent's key
            user_key: The user_key linked to this agent
            team_keys: List of team_keys the agent can access
            domain_key: The agent's domain_key
        """
        from api.models.message_read import MessageRead
        from sqlalchemy import or_, and_

        conditions = []

        # Only autonomous messages
        base_filter = cls.autonomous == True

        # Build visibility conditions (same as get_for_agent)
        if domain_key:
            conditions.append(
                and_(cls.scope == 'broadcast-domain', cls.domain_key == domain_key)
            )

        if team_keys:
            conditions.append(
                and_(cls.scope == 'broadcast-team', cls.team_key.in_(team_keys))
            )

        conditions.append(
            and_(cls.scope == 'agent-agent', or_(cls.from_key == agent_key, cls.to_key == agent_key))
        )
        conditions.append(
            and_(cls.scope == 'user-agent', cls.to_key == agent_key)
        )

        if user_key:
            conditions.append(
                and_(cls.scope == 'user-agents', cls.user_key == user_key)
            )
            conditions.append(
                and_(cls.scope == 'agent-agents', cls.user_key == user_key)
            )

        query = cls.query.filter(base_filter, or_(*conditions))

        # Exclude messages they've read
        read_subquery = db.session.query(MessageRead.message_key).filter(
            MessageRead.reader_key == agent_key
        ).scalar_subquery()
        query = query.filter(~cls.message_key.in_(read_subquery))

        return query.count()

    def mark_read(self, reader_key: str = None) -> bool:
        """
        Mark the message as read.

        Args:
            reader_key: The agent_key or user_key marking it read (required)
        """
        from api.models.message_read import MessageRead

        if reader_key:
            MessageRead.mark_read(self.message_key, reader_key)
            return True
        else:
            # Legacy behavior - mark globally
            self.read_at = get_now()
            return self.save()

    def confirm(self, confirmed_by: str) -> bool:
        """
        Confirm task completion on this message.

        Args:
            confirmed_by: agent_key or user_key who confirmed
        """
        self.confirmed = True
        self.confirmed_by = confirmed_by
        self.confirmed_at = get_now()
        return self.save()

    def unconfirm(self) -> bool:
        """Remove confirmation from this message."""
        self.confirmed = False
        self.confirmed_by = None
        self.confirmed_at = None
        return self.save()

    def is_read_by(self, reader_key: str) -> bool:
        """Check if a specific agent or user has read this message."""
        from api.models.message_read import MessageRead
        return MessageRead.has_read(self.message_key, reader_key)

    def get_readers(self) -> list[str]:
        """Get list of keys who have read this message."""
        from api.models.message_read import MessageRead
        reads = MessageRead.get_readers(self.message_key)
        return [r.reader_key for r in reads]

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
        """
        thread = cls.get_thread(message_key)
        if not thread:
            return []

        entity_keys = set()

        root = thread.get('root')
        if root and root.entity_keys:
            entity_keys.update(root.entity_keys)

        def collect_from_replies(replies):
            for item in replies:
                msg = item.get('message')
                if msg and msg.entity_keys:
                    entity_keys.update(msg.entity_keys)
                collect_from_replies(item.get('replies', []))

        collect_from_replies(thread.get('replies', []))
        return list(entity_keys)

    def to_dict(self, include_read_status: bool = True, for_reader: str = None, include_readers: bool = False, include_thread_info: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_read_status: Include is_read field
            for_reader: Check read status for this specific agent/user key
            include_readers: Include list of keys who have read this message
            include_thread_info: Include reply_count and has_parent indicators
        """
        result = super().to_dict()
        if include_read_status:
            if for_reader:
                result['is_read'] = self.is_read_by(for_reader)
            else:
                # Legacy: use read_at field
                result['is_read'] = self.read_at is not None

        if include_readers:
            from api.models.message_read import MessageRead
            reads = MessageRead.get_readers(self.message_key)
            result['readers'] = [{'reader_key': r.reader_key, 'read_at': r.read_at.isoformat() if r.read_at else None} for r in reads]
            result['read_count'] = len(reads)

        if include_thread_info:
            result['reply_count'] = self.get_reply_count()
            result['has_parent'] = self.reply_to_key is not None

        return result
