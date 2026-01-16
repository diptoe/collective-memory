"""
Collective Memory Platform - Domain Model

Multi-tenant workspace/domain management.
"""
import re
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


# Generic email domains that shouldn't auto-create organizational domains
GENERIC_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'icloud.com', 'aol.com', 'protonmail.com', 'mail.com',
    'live.com', 'msn.com', 'me.com', 'ymail.com', 'googlemail.com',
    'fastmail.com', 'zoho.com', 'tutanota.com', 'hey.com'
}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


class Domain(BaseModel):
    """
    Domain/workspace for multi-tenancy.

    Domains can isolate:
    - Entities and relationships
    - Conversations and messages
    - Agent registrations

    Note: Multi-tenancy isolation is not yet implemented.
    This model is prepared for future use.
    """
    __tablename__ = 'domains'
    _schema_version = 1

    domain_key = Column(String(36), primary_key=True, default=get_key)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Owner
    owner_key = Column(String(36), ForeignKey('users.user_key', ondelete='SET NULL'), nullable=True, index=True)

    # Settings
    settings = Column(JSONB, default=dict)
    status = Column(String(20), default='active', nullable=False, index=True)  # active, suspended

    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    __table_args__ = (
        Index('ix_domains_owner_status', 'owner_key', 'status'),
    )

    _default_fields = ['domain_key', 'name', 'slug', 'owner_key', 'status']
    _readonly_fields = ['domain_key', 'created_at']

    @classmethod
    def _schema_migrations(cls):
        return {
            1: "Initial schema with name, slug, owner, settings"
        }

    @classmethod
    def get_by_slug(cls, slug: str) -> 'Domain | None':
        """Get domain by slug."""
        return cls.query.filter_by(slug=slug).first()

    @classmethod
    def get_for_owner(cls, owner_key: str) -> list['Domain']:
        """Get all domains owned by a user."""
        return cls.query.filter_by(owner_key=owner_key, status='active').all()

    @classmethod
    def create_for_user(cls, owner_key: str, name: str, description: str = None) -> 'Domain':
        """Create a new domain for a user."""
        slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while cls.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        domain = cls(
            name=name,
            slug=slug,
            description=description,
            owner_key=owner_key,
        )
        domain.save()
        return domain

    def suspend(self) -> None:
        """Suspend the domain."""
        self.status = 'suspended'
        self.save()

    def activate(self) -> None:
        """Activate the domain."""
        self.status = 'active'
        self.save()

    def to_dict(self) -> dict:
        """Convert domain to dictionary."""
        return {
            'domain_key': self.domain_key,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'owner_key': self.owner_key,
            'settings': self.settings or {},
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def is_generic_domain(cls, domain: str) -> bool:
        """Check if domain is a generic email provider (gmail, yahoo, etc.)."""
        return domain.lower() in GENERIC_EMAIL_DOMAINS

    @classmethod
    def get_or_create_for_email(cls, email: str) -> Optional['Domain']:
        """
        Get or create a domain for an email address.

        Returns None for generic email providers (gmail, yahoo, etc.).
        For organizational emails, creates the domain if it doesn't exist.
        """
        if '@' not in email:
            return None

        email_domain = email.split('@')[1].lower()

        if cls.is_generic_domain(email_domain):
            return None

        # Try to find existing domain by slug
        domain = cls.get_by_slug(email_domain)
        if domain:
            return domain

        # Create new domain (no owner until admin assigns)
        domain = cls(
            domain_key=get_key(),
            name=email_domain.split('.')[0].title(),  # "janison" from "janison.com.au"
            slug=email_domain,
            description=f"Auto-created for {email_domain}",
            owner_key=None,
            status='active'
        )
        db.session.add(domain)
        db.session.commit()
        return domain


def ensure_default_domain() -> 'Domain':
    """
    Ensure the default domain exists and migrate existing data to it.

    This should be called during app initialization to:
    1. Create the default domain if it doesn't exist
    2. Update all entities with NULL context_domain
    3. Update all messages with NULL context_domain
    4. Update all users with NULL domain_key

    Returns the default domain.
    """
    from api.config import CM_DEFAULT_DOMAIN
    from api.models.entity import Entity
    from api.models.message import Message
    from api.models.user import User

    # Get or create default domain
    domain = Domain.get_by_slug(CM_DEFAULT_DOMAIN)
    if not domain:
        domain = Domain(
            domain_key=get_key(),
            name=CM_DEFAULT_DOMAIN.split('.')[0].title(),  # "Janison" from "janison.com.au"
            slug=CM_DEFAULT_DOMAIN,
            description=f"Default domain for {CM_DEFAULT_DOMAIN}",
            owner_key=None,
            status='active'
        )
        db.session.add(domain)
        db.session.commit()
        print(f"[Domain] Created default domain: {CM_DEFAULT_DOMAIN} ({domain.domain_key})")

    # Migrate entities with NULL context_domain
    entity_count = Entity.query.filter(Entity.context_domain.is_(None)).update(
        {'context_domain': domain.domain_key},
        synchronize_session=False
    )
    if entity_count > 0:
        db.session.commit()
        print(f"[Domain] Migrated {entity_count} entities to default domain")

    # Migrate messages with NULL context_domain (if column exists)
    try:
        message_count = Message.query.filter(Message.context_domain.is_(None)).update(
            {'context_domain': domain.domain_key},
            synchronize_session=False
        )
        if message_count > 0:
            db.session.commit()
            print(f"[Domain] Migrated {message_count} messages to default domain")
    except Exception as e:
        # Column might not exist yet
        db.session.rollback()
        print(f"[Domain] Message migration skipped (column may not exist): {e}")

    # Migrate users with NULL domain_key
    try:
        user_count = User.query.filter(User.domain_key.is_(None)).update(
            {'domain_key': domain.domain_key},
            synchronize_session=False
        )
        if user_count > 0:
            db.session.commit()
            print(f"[Domain] Migrated {user_count} users to default domain")
    except Exception as e:
        db.session.rollback()
        print(f"[Domain] User migration skipped (column may not exist): {e}")

    return domain
