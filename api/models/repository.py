"""
Collective Memory Platform - Repository Model

Dedicated model for tracking repositories (GitHub, GitLab, etc.) with many-to-many
relationship to projects.
"""
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List

from api.models.base import BaseModel, db, get_key, get_now


class Repository(BaseModel):
    """
    Repository model for tracking source code repositories.

    Repositories can be linked to multiple projects via the ProjectRepository
    junction table. This enables:
    - A project to have multiple repositories
    - A repository to belong to multiple projects (rare but possible)
    - MCP detection: git URL → Repository → linked Project(s)
    """
    __tablename__ = 'repositories'
    __schema_version__ = 1

    # Primary key
    repository_key = Column(String(50), primary_key=True, default=get_key)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Repository identification (moved from Project)
    repository_type = Column(String(50), nullable=True)  # github, gitlab, bitbucket, azure, codecommit
    repository_url = Column(String(500), nullable=False, unique=True, index=True)
    repository_owner = Column(String(255), nullable=True)  # org/user
    repository_name = Column(String(255), nullable=True)   # repo name

    # Domain ownership
    domain_key = Column(String(50), ForeignKey('domains.domain_key'), nullable=False, index=True)

    # Status
    status = Column(String(50), default='active')  # active, archived

    # Extra data (JSON)
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(db.DateTime(timezone=True), default=get_now)
    updated_at = Column(db.DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Indexes
    __table_args__ = (
        Index('ix_repositories_domain_status', 'domain_key', 'status'),
        Index('ix_repositories_owner_name', 'repository_owner', 'repository_name'),
    )

    _default_fields = [
        'repository_key', 'name', 'description',
        'repository_type', 'repository_url', 'repository_owner', 'repository_name',
        'domain_key', 'status',
        'created_at', 'updated_at'
    ]
    _readonly_fields = ['repository_key', 'created_at']

    @classmethod
    def find_by_url(cls, repository_url: str) -> Optional['Repository']:
        """Find repository by URL (normalized)."""
        if not repository_url:
            return None
        normalized = cls.normalize_url(repository_url)
        return cls.query.filter_by(repository_url=normalized).first()

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """Normalize repository URL for matching."""
        if not url:
            return url
        url = url.strip()
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        # Convert git@ to https://
        if url.startswith('git@'):
            # git@github.com:owner/repo -> https://github.com/owner/repo
            url = url.replace(':', '/', 1).replace('git@', 'https://')
        return url.lower()

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """Parse repository URL to extract type, owner, name."""
        normalized = cls.normalize_url(url)
        result = {'type': None, 'owner': None, 'name': None}
        if not normalized:
            return result

        # Detect repository type
        if 'github.com' in normalized:
            result['type'] = 'github'
        elif 'gitlab.com' in normalized:
            result['type'] = 'gitlab'
        elif 'bitbucket.org' in normalized:
            result['type'] = 'bitbucket'
        elif 'dev.azure.com' in normalized or 'visualstudio.com' in normalized:
            result['type'] = 'azure'
        elif 'codecommit' in normalized:
            result['type'] = 'codecommit'

        # Extract owner and name from path
        parts = normalized.split('/')
        if len(parts) >= 2:
            result['name'] = parts[-1]
            result['owner'] = parts[-2]

        return result

    @classmethod
    def get_by_domain(cls, domain_key: str, include_archived: bool = False) -> List['Repository']:
        """Get repositories by domain."""
        query = cls.query.filter_by(domain_key=domain_key)
        if not include_archived:
            query = query.filter_by(status='active')
        return query.order_by(cls.name).all()

    @classmethod
    def create_repository(
        cls,
        domain_key: str,
        repository_url: str,
        name: str = None,
        description: str = None,
        extra_data: dict = None
    ) -> 'Repository':
        """
        Create a new repository, auto-parsing URL.

        Args:
            domain_key: Domain the repository belongs to
            repository_url: Repository URL (will be parsed)
            name: Optional name (defaults to parsed repo name)
            description: Optional description
            extra_data: Optional extra data

        Returns:
            Created Repository instance
        """
        # Parse URL to get details
        normalized_url = cls.normalize_url(repository_url)
        parsed = cls.parse_url(repository_url)

        # Use parsed name if not provided
        if not name:
            name = parsed.get('name') or normalized_url.split('/')[-1] or 'Unknown Repository'

        repository = cls(
            domain_key=domain_key,
            name=name,
            description=description,
            repository_url=normalized_url,
            repository_type=parsed.get('type'),
            repository_owner=parsed.get('owner'),
            repository_name=parsed.get('name'),
            extra_data=extra_data
        )

        repository.save()
        return repository

    def update_url(self, repository_url: str) -> None:
        """Update repository URL and re-parse related fields."""
        if repository_url:
            self.repository_url = self.normalize_url(repository_url)
            parsed = self.parse_url(repository_url)
            self.repository_type = parsed.get('type')
            self.repository_owner = parsed.get('owner')
            self.repository_name = parsed.get('name')
        else:
            self.repository_url = None
            self.repository_type = None
            self.repository_owner = None
            self.repository_name = None

    def archive(self) -> None:
        """Archive the repository (soft delete)."""
        self.status = 'archived'
        self.save()

    def restore(self) -> None:
        """Restore an archived repository."""
        self.status = 'active'
        self.save()

    def get_projects(self) -> List:
        """Get all projects associated with this repository."""
        from api.models.project_repository import ProjectRepository
        from api.models.project import Project
        associations = ProjectRepository.get_projects_for_repository(self.repository_key)
        project_keys = [a.project_key for a in associations]
        if not project_keys:
            return []
        return Project.query.filter(Project.project_key.in_(project_keys)).all()

    def to_dict(self, include_projects: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            'repository_key': self.repository_key,
            'name': self.name,
            'description': self.description,
            'repository_type': self.repository_type,
            'repository_url': self.repository_url,
            'repository_owner': self.repository_owner,
            'repository_name': self.repository_name,
            'domain_key': self.domain_key,
            'status': self.status,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_projects:
            from api.models.project_repository import ProjectRepository
            associations = ProjectRepository.get_projects_for_repository(self.repository_key)
            result['projects'] = [a.to_dict(include_project=True) for a in associations]

        return result
