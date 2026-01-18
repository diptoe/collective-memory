"""
Collective Memory Platform - Team Model

Team structure for organizing users within domains.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Team(BaseModel):
    """
    Team within a domain.

    Teams organize users into groups with shared access to entities
    and can be used for scope-based visibility control.
    """
    __tablename__ = 'teams'
    _schema_version = 1

    team_key = Column(String(36), primary_key=True, default=get_key)
    domain_key = Column(String(36), ForeignKey('domains.domain_key'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='active', index=True)  # active, archived
    settings = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Relationships
    domain = relationship('Domain', backref='teams')

    __table_args__ = (
        Index('ix_teams_domain_slug', 'domain_key', 'slug', unique=True),
    )

    _default_fields = ['team_key', 'domain_key', 'name', 'slug', 'status']
    _readonly_fields = ['team_key', 'created_at']

    @classmethod
    def _schema_migrations(cls):
        return {
            1: "Initial schema with domain_key, name, slug, description, status, settings"
        }

    @classmethod
    def get_by_slug(cls, domain_key: str, slug: str) -> 'Team | None':
        """Get team by domain and slug."""
        return cls.query.filter_by(domain_key=domain_key, slug=slug, status='active').first()

    @classmethod
    def get_for_domain(cls, domain_key: str, include_archived: bool = False) -> list['Team']:
        """Get all teams in a domain."""
        query = cls.query.filter_by(domain_key=domain_key)
        if not include_archived:
            query = query.filter_by(status='active')
        return query.order_by(cls.name).all()

    @classmethod
    def create_team(cls, domain_key: str, name: str, slug: str = None, description: str = None) -> 'Team':
        """Create a new team."""
        import re
        if not slug:
            # Generate slug from name
            slug = re.sub(r'[^\w\s-]', '', name.lower())
            slug = re.sub(r'[\s_-]+', '-', slug)
            slug = slug.strip('-')

        # Ensure unique slug within domain
        base_slug = slug
        counter = 1
        while cls.get_by_slug(domain_key, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        team = cls(
            domain_key=domain_key,
            name=name,
            slug=slug,
            description=description,
        )
        team.save()
        return team

    def archive(self) -> None:
        """Archive the team."""
        self.status = 'archived'
        self.save()

    def activate(self) -> None:
        """Activate the team."""
        self.status = 'active'
        self.save()

    def get_members(self) -> list['TeamMembership']:
        """Get all active memberships for this team."""
        return TeamMembership.query.filter_by(team_key=self.team_key).all()

    def get_member_count(self) -> int:
        """Get count of team members."""
        return TeamMembership.query.filter_by(team_key=self.team_key).count()

    def add_member(self, user_key: str, role: str = 'member', slug: str = None) -> 'TeamMembership':
        """Add a user to the team."""
        existing = TeamMembership.query.filter_by(
            team_key=self.team_key,
            user_key=user_key
        ).first()
        if existing:
            existing.role = role
            if slug is not None:
                existing.slug = slug
            existing.save()
            return existing

        # Get user for default slug
        from api.models.user import User
        user = User.get(user_key)
        default_slug = slug or (user.initials.lower() if user and user.initials else None)

        membership = TeamMembership(
            team_key=self.team_key,
            user_key=user_key,
            role=role,
            slug=default_slug,
        )
        membership.save()
        return membership

    def remove_member(self, user_key: str) -> bool:
        """Remove a user from the team."""
        membership = TeamMembership.query.filter_by(
            team_key=self.team_key,
            user_key=user_key
        ).first()
        if membership:
            db.session.delete(membership)
            db.session.commit()
            return True
        return False

    def is_member(self, user_key: str) -> bool:
        """Check if a user is a member of this team."""
        return TeamMembership.query.filter_by(
            team_key=self.team_key,
            user_key=user_key
        ).count() > 0

    def get_member_role(self, user_key: str) -> str | None:
        """Get the role of a user in this team."""
        membership = TeamMembership.query.filter_by(
            team_key=self.team_key,
            user_key=user_key
        ).first()
        return membership.role if membership else None

    def to_dict(self, include_members: bool = False) -> dict:
        """Convert team to dictionary."""
        result = {
            'team_key': self.team_key,
            'domain_key': self.domain_key,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'status': self.status,
            'settings': self.settings or {},
            'member_count': self.get_member_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_members:
            result['members'] = [m.to_dict(include_user=True) for m in self.get_members()]

        return result


class TeamMembership(BaseModel):
    """
    Team membership linking users to teams with roles.

    Roles:
    - owner: Can manage team settings and members, delete team
    - admin: Can manage members and team settings
    - member: Can access team-scoped entities
    - viewer: Read-only access to team-scoped entities
    """
    __tablename__ = 'team_memberships'
    _schema_version = 2

    membership_key = Column(String(36), primary_key=True, default=get_key)
    team_key = Column(String(36), ForeignKey('teams.team_key', ondelete='CASCADE'), nullable=False, index=True)
    user_key = Column(String(36), ForeignKey('users.user_key', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), default='member', nullable=False)  # owner, admin, member, viewer
    slug = Column(String(10), nullable=True)  # User's preferred identifier within team (e.g., initials or nickname)
    joined_at = Column(DateTime(timezone=True), default=get_now)

    # Relationships
    team = relationship('Team', backref='memberships')
    user = relationship('User', backref='team_memberships')

    __table_args__ = (
        Index('ix_team_memberships_unique', 'team_key', 'user_key', unique=True),
    )

    _default_fields = ['membership_key', 'team_key', 'user_key', 'role', 'slug']
    _readonly_fields = ['membership_key', 'joined_at']

    @classmethod
    def _schema_migrations(cls):
        return {
            1: "Initial schema with team_key, user_key, role, joined_at",
            2: "Added slug field for custom user identifier within team"
        }

    @classmethod
    def get_user_teams(cls, user_key: str) -> list['Team']:
        """Get all teams a user is a member of."""
        memberships = cls.query.filter_by(user_key=user_key).all()
        return [m.team for m in memberships if m.team and m.team.status == 'active']

    @classmethod
    def get_user_membership(cls, user_key: str, team_key: str) -> 'TeamMembership | None':
        """Get a specific membership."""
        return cls.query.filter_by(user_key=user_key, team_key=team_key).first()

    @property
    def is_admin(self) -> bool:
        """Check if membership has admin privileges."""
        return self.role in ('owner', 'admin')

    @property
    def is_owner(self) -> bool:
        """Check if membership is owner."""
        return self.role == 'owner'

    @property
    def can_write(self) -> bool:
        """Check if membership allows write access."""
        return self.role in ('owner', 'admin', 'member')

    def set_role(self, role: str) -> None:
        """Set the membership role."""
        if role not in ('owner', 'admin', 'member', 'viewer'):
            raise ValueError(f"Invalid team role: {role}")
        self.role = role
        self.save()

    def ensure_slug(self) -> str | None:
        """Ensure slug is set, defaulting to user initials."""
        if not self.slug and self.user:
            self.slug = self.user.initials.lower() if self.user.initials else None
            if self.slug:
                self.save()
        return self.slug

    def to_dict(self, include_user: bool = False, include_team: bool = False) -> dict:
        """Convert membership to dictionary."""
        result = {
            'membership_key': self.membership_key,
            'team_key': self.team_key,
            'user_key': self.user_key,
            'role': self.role,
            'slug': self.slug,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
        }

        if include_user and self.user:
            result['user'] = {
                'user_key': self.user.user_key,
                'email': self.user.email,
                'display_name': self.user.display_name,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
            }

        if include_team and self.team:
            result['team'] = {
                'team_key': self.team.team_key,
                'name': self.team.name,
                'slug': self.team.slug,
            }

        return result
