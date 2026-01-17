"""
Collective Memory Platform - Session Model

Server-side session management for user authentication.
"""
import secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index

from api.models.base import BaseModel, db, get_key, get_now


def generate_session_token() -> str:
    """Generate a secure session token (64 hex chars = 32 bytes)."""
    return secrets.token_hex(32)


class Session(BaseModel):
    """
    User authentication session.

    Server-side sessions provide:
    - Easy revocation (just delete the row)
    - Session listing/management for users
    - No JWT expiry/refresh complexity
    """
    __tablename__ = 'sessions'
    _schema_version = 2

    # Session duration constants (in hours)
    DEFAULT_DURATION_HOURS = 24 * 7      # 7 days
    REMEMBER_ME_DURATION_HOURS = 24 * 30  # 30 days

    session_key = Column(String(36), primary_key=True, default=get_key)
    user_key = Column(String(36), ForeignKey('users.user_key', ondelete='CASCADE'), nullable=False, index=True)
    agent_key = Column(String(36), ForeignKey('agents.agent_key', ondelete='SET NULL'), nullable=True, index=True)

    # Session token (sent to client as httpOnly cookie)
    token = Column(String(64), unique=True, nullable=False, default=generate_session_token, index=True)

    # Client metadata
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length

    # Expiry and activity tracking
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), default=get_now)

    created_at = Column(DateTime(timezone=True), default=get_now)

    __table_args__ = (
        Index('ix_sessions_token_expires', 'token', 'expires_at'),
        Index('ix_sessions_user_expires', 'user_key', 'expires_at'),
    )

    _default_fields = ['session_key', 'user_key', 'agent_key', 'expires_at', 'last_activity_at']
    _readonly_fields = ['session_key', 'token', 'user_key', 'created_at']

    @classmethod
    def _schema_migrations(cls):
        return {
            1: "Initial schema with token, user_key, expiry, metadata",
            2: "Added agent_key for MCP-initiated sessions"
        }

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid (not expired)."""
        return not self.is_expired

    @property
    def device_info(self) -> str:
        """Extract device info from user agent."""
        if not self.user_agent:
            return "Unknown device"

        ua = self.user_agent.lower()
        if 'claude' in ua or 'anthropic' in ua:
            return "Claude Code"
        elif 'cursor' in ua:
            return "Cursor"
        elif 'chrome' in ua:
            return "Chrome browser"
        elif 'firefox' in ua:
            return "Firefox browser"
        elif 'safari' in ua:
            return "Safari browser"
        elif 'edge' in ua:
            return "Edge browser"
        else:
            return "Web browser"

    @classmethod
    def get_by_token(cls, token: str) -> 'Session | None':
        """Get valid (non-expired) session by token."""
        return cls.query.filter(
            cls.token == token,
            cls.expires_at > datetime.now(timezone.utc)
        ).first()

    @classmethod
    def get_user_sessions(cls, user_key: str, include_expired: bool = False) -> list['Session']:
        """Get all sessions for a user."""
        query = cls.query.filter_by(user_key=user_key)
        if not include_expired:
            query = query.filter(cls.expires_at > datetime.now(timezone.utc))
        return query.order_by(cls.last_activity_at.desc()).all()

    @classmethod
    def cleanup_duplicate_sessions(cls, user_key: str, user_agent: str = None, ip_address: str = None, keep_count: int = 1) -> int:
        """Cleanup old sessions from the same device, keeping only the most recent ones.

        Args:
            user_key: User to cleanup sessions for
            user_agent: User agent to match (if None, matches all)
            ip_address: IP address to match (if None, matches all)
            keep_count: Number of most recent sessions to keep

        Returns:
            Number of sessions deleted
        """
        query = cls.query.filter_by(user_key=user_key)
        query = query.filter(cls.expires_at > datetime.now(timezone.utc))

        # If user_agent provided, only cleanup sessions with matching device type
        if user_agent:
            # Match based on device_info (browser type)
            device_info = cls._extract_device_type(user_agent)
            if device_info:
                # Find sessions with similar user agents
                sessions = query.order_by(cls.last_activity_at.desc()).all()
                matching = [s for s in sessions if cls._extract_device_type(s.user_agent) == device_info]

                if len(matching) > keep_count:
                    to_delete = matching[keep_count:]
                    for s in to_delete:
                        db.session.delete(s)
                    db.session.commit()
                    return len(to_delete)
                return 0

        return 0

    @staticmethod
    def _extract_device_type(user_agent: str) -> str:
        """Extract device type from user agent for grouping."""
        if not user_agent:
            return 'unknown'

        ua = user_agent.lower()
        if 'claude' in ua or 'anthropic' in ua:
            return 'claude-code'
        elif 'cursor' in ua:
            return 'cursor'
        elif 'chrome' in ua:
            return 'chrome'
        elif 'firefox' in ua:
            return 'firefox'
        elif 'safari' in ua:
            return 'safari'
        elif 'edge' in ua:
            return 'edge'
        else:
            return 'browser'

    @classmethod
    def create_for_user(
        cls,
        user_key: str,
        remember_me: bool = False,
        user_agent: str = None,
        ip_address: str = None,
        agent_key: str = None,
        cleanup_old: bool = True
    ) -> 'Session':
        """Create a new session for a user.

        Args:
            user_key: The user this session belongs to
            remember_me: Use longer session duration
            user_agent: Client user agent string
            ip_address: Client IP address
            agent_key: Optional agent key for MCP-initiated sessions
            cleanup_old: If True, cleanup old sessions from same device (keep 2 most recent)
        """
        # Cleanup old sessions from same device type (keep 2 most recent)
        if cleanup_old and user_agent:
            cls.cleanup_duplicate_sessions(user_key, user_agent, ip_address, keep_count=2)

        duration_hours = cls.REMEMBER_ME_DURATION_HOURS if remember_me else cls.DEFAULT_DURATION_HOURS
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        session = cls(
            user_key=user_key,
            agent_key=agent_key,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        session.save()
        return session

    @classmethod
    def get_all_sessions(cls, include_expired: bool = False, limit: int = 100) -> list['Session']:
        """Get all sessions (for admin use)."""
        query = cls.query
        if not include_expired:
            query = query.filter(cls.expires_at > datetime.now(timezone.utc))
        return query.order_by(cls.last_activity_at.desc()).limit(limit).all()

    @classmethod
    def cleanup_expired(cls) -> int:
        """Delete all expired sessions. Returns count deleted."""
        result = cls.query.filter(cls.expires_at < datetime.now(timezone.utc)).delete()
        db.session.commit()
        return result

    @classmethod
    def revoke_all_for_user(cls, user_key: str) -> int:
        """Revoke all sessions for a user. Returns count deleted."""
        result = cls.query.filter_by(user_key=user_key).delete()
        db.session.commit()
        return result

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = get_now()
        db.session.commit()

    def extend(self, hours: int = None) -> None:
        """Extend session expiry."""
        if hours is None:
            hours = self.DEFAULT_DURATION_HOURS
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.last_activity_at = get_now()
        db.session.commit()

    def revoke(self) -> None:
        """Revoke (delete) this session."""
        self.delete()

    def to_dict(self, include_user: bool = False, include_agent: bool = False) -> dict:
        """Convert session to dictionary.

        Args:
            include_user: Include user details (email, name)
            include_agent: Include agent details (agent_id)
        """
        result = {
            'session_key': self.session_key,
            'user_key': self.user_key,
            'agent_key': self.agent_key,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_current': False,  # Set by caller if this is the current session
        }

        if include_user and self.user_key:
            from api.models.user import User
            user = User.get_by_key(self.user_key)
            if user:
                result['user'] = {
                    'email': user.email,
                    'name': user.display_name,
                }

        if include_agent and self.agent_key:
            from api.models.agent import Agent
            agent = Agent.get_by_key(self.agent_key)
            if agent:
                result['agent'] = {
                    'agent_id': agent.agent_id,
                    'client': agent.client,
                }

        return result
