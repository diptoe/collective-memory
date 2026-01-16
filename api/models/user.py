"""
Collective Memory Platform - User Model

User authentication and profile management.
"""
import secrets
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


def generate_pat() -> str:
    """Generate a secure Personal Access Token (64 hex chars = 32 bytes)."""
    return secrets.token_hex(32)


class User(BaseModel):
    """
    Authenticated user in the Collective Memory platform.

    Users can:
    - Login via email/password
    - Use PAT for MCP/API authentication
    - Have roles (admin, user)
    - Link to Entity records for knowledge graph presence
    """
    __tablename__ = 'users'
    _schema_version = 2  # Added domain_key

    user_key = Column(String(36), primary_key=True, default=get_key)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash

    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Role and status
    role = Column(String(20), default='user', nullable=False, index=True)  # admin, user
    status = Column(String(20), default='active', nullable=False, index=True)  # active, suspended, pending

    # Personal Access Token for MCP/API access
    pat = Column(String(64), unique=True, nullable=False, default=generate_pat, index=True)
    pat_created_at = Column(DateTime(timezone=True), default=get_now)

    # Metadata
    preferences = Column(JSONB, default=dict)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Optional link to Person entity in knowledge graph
    entity_key = Column(String(36), nullable=True)

    # Domain association for multi-tenancy
    domain_key = Column(String(36), ForeignKey('domains.domain_key', ondelete='SET NULL'), nullable=True, index=True)
    domain = relationship('Domain', backref='users', foreign_keys=[domain_key])

    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    __table_args__ = (
        Index('ix_users_email_status', 'email', 'status'),
        Index('ix_users_role_status', 'role', 'status'),
    )

    _default_fields = ['user_key', 'email', 'first_name', 'last_name', 'role', 'status']
    _readonly_fields = ['user_key', 'password_hash', 'pat', 'created_at']

    @classmethod
    def _schema_migrations(cls):
        return {
            1: "Initial schema with email, password, PAT, role, status",
            2: "Added domain_key for multi-tenancy"
        }

    @property
    def display_name(self) -> str:
        """Get user's display name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self) -> str:
        """Get user's initials."""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == 'active'

    @property
    def email_domain(self) -> str:
        """Extract domain from email address."""
        return self.email.split('@')[1].lower() if '@' in self.email else ''

    @classmethod
    def get_by_email(cls, email: str) -> 'User | None':
        """Get user by email address (case-insensitive)."""
        return cls.query.filter(cls.email.ilike(email)).first()

    @classmethod
    def get_by_pat(cls, pat: str) -> 'User | None':
        """Get active user by Personal Access Token."""
        return cls.query.filter_by(pat=pat, status='active').first()

    @classmethod
    def get_active(cls, limit: int = 100, offset: int = 0) -> list['User']:
        """Get all active users."""
        return cls.query.filter_by(status='active').limit(limit).offset(offset).all()

    @classmethod
    def get_admins(cls) -> list['User']:
        """Get all admin users."""
        return cls.query.filter_by(role='admin', status='active').all()

    def regenerate_pat(self) -> str:
        """Regenerate the Personal Access Token."""
        self.pat = generate_pat()
        self.pat_created_at = get_now()
        self.save()
        return self.pat

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login_at = get_now()
        db.session.commit()

    def suspend(self) -> None:
        """Suspend the user account."""
        self.status = 'suspended'
        self.save()

    def activate(self) -> None:
        """Activate the user account."""
        self.status = 'active'
        self.save()

    def set_role(self, role: str) -> None:
        """Set user role (admin or user)."""
        if role not in ('admin', 'user'):
            raise ValueError(f"Invalid role: {role}")
        self.role = role
        self.save()

    def to_dict(self, include_pat: bool = False) -> dict:
        """
        Convert user to dictionary.

        Args:
            include_pat: Include PAT in response (only for authenticated user viewing their own data)
        """
        result = {
            'user_key': self.user_key,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'initials': self.initials,
            'role': self.role,
            'status': self.status,
            'preferences': self.preferences or {},
            'entity_key': self.entity_key,
            'domain_key': self.domain_key,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_pat:
            result['pat'] = self.pat
            result['pat_created_at'] = self.pat_created_at.isoformat() if self.pat_created_at else None

        return result
