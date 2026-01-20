"""
Collective Memory Platform - Project Model

Dedicated model for tracking projects/repositories with team associations.
"""
from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List

from api.models.base import BaseModel, db, get_key, get_now


class Project(BaseModel):
    """
    Project model for repository tracking.

    Projects can be linked to teams via the TeamProject junction table.
    They can also be linked to Project entities in the knowledge graph.
    """
    __tablename__ = 'projects'
    __schema_version__ = 1

    # Primary key
    project_key = Column(String(50), primary_key=True, default=get_key)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Repository info
    repository_type = Column(String(50), nullable=True)  # github, gitlab, bitbucket, azure, codecommit
    repository_url = Column(String(500), nullable=True, index=True)
    repository_owner = Column(String(255), nullable=True)  # org/user
    repository_name = Column(String(255), nullable=True)   # repo name

    # Domain ownership
    domain_key = Column(String(50), ForeignKey('domains.domain_key'), nullable=False, index=True)

    # Optional link to Project entity in knowledge graph
    entity_key = Column(String(50), nullable=True)

    # Status
    status = Column(String(50), default='active')  # active, archived

    # Extra data (JSON)
    extra_data = Column(JSONB, nullable=True)

    # Timestamps (inherited from BaseModel pattern)
    created_at = Column(db.DateTime(timezone=True), default=get_now)
    updated_at = Column(db.DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Indexes
    __table_args__ = (
        Index('ix_projects_domain_status', 'domain_key', 'status'),
        Index('ix_projects_repo_owner_name', 'repository_owner', 'repository_name'),
    )

    _default_fields = [
        'project_key', 'name', 'description',
        'repository_type', 'repository_url', 'repository_owner', 'repository_name',
        'domain_key', 'entity_key', 'status',
        'created_at', 'updated_at'
    ]
    _readonly_fields = ['project_key', 'created_at']

    @classmethod
    def find_by_repository(cls, repository_url: str) -> Optional['Project']:
        """Find project by repository URL (normalized)."""
        if not repository_url:
            return None
        normalized = cls.normalize_repository_url(repository_url)
        return cls.query.filter_by(repository_url=normalized).first()

    @classmethod
    def normalize_repository_url(cls, url: str) -> str:
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
    def parse_repository_url(cls, url: str) -> dict:
        """Parse repository URL to extract type, owner, name."""
        normalized = cls.normalize_repository_url(url)
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
    def get_by_domain(cls, domain_key: str, include_archived: bool = False) -> List['Project']:
        """Get projects by domain."""
        query = cls.query.filter_by(domain_key=domain_key)
        if not include_archived:
            query = query.filter_by(status='active')
        return query.order_by(cls.name).all()

    @classmethod
    def create_project(
        cls,
        domain_key: str,
        name: str,
        description: str = None,
        repository_url: str = None,
        entity_key: str = None,
        extra_data: dict = None
    ) -> 'Project':
        """
        Create a new project, auto-parsing repository URL.

        Args:
            domain_key: Domain the project belongs to
            name: Project name
            description: Optional description
            repository_url: Optional repository URL (will be parsed)
            entity_key: Optional link to knowledge graph entity
            extra_data: Optional extra data

        Returns:
            Created Project instance
        """
        project = cls(
            domain_key=domain_key,
            name=name,
            description=description,
            entity_key=entity_key,
            extra_data=extra_data
        )

        # Parse and set repository info
        if repository_url:
            project.repository_url = cls.normalize_repository_url(repository_url)
            parsed = cls.parse_repository_url(repository_url)
            project.repository_type = parsed.get('type')
            project.repository_owner = parsed.get('owner')
            project.repository_name = parsed.get('name')

        project.save()
        return project

    def update_repository(self, repository_url: str) -> None:
        """Update repository URL and re-parse related fields."""
        if repository_url:
            self.repository_url = self.normalize_repository_url(repository_url)
            parsed = self.parse_repository_url(repository_url)
            self.repository_type = parsed.get('type')
            self.repository_owner = parsed.get('owner')
            self.repository_name = parsed.get('name')
        else:
            self.repository_url = None
            self.repository_type = None
            self.repository_owner = None
            self.repository_name = None

    def archive(self) -> None:
        """Archive the project (soft delete)."""
        self.status = 'archived'
        self.save()

    def restore(self) -> None:
        """Restore an archived project."""
        self.status = 'active'
        self.save()

    def get_teams(self) -> List:
        """Get all teams associated with this project."""
        from api.models.team_project import TeamProject
        from api.models.team import Team
        associations = TeamProject.get_teams_for_project(self.project_key)
        team_keys = [a.team_key for a in associations]
        if not team_keys:
            return []
        return Team.query.filter(Team.team_key.in_(team_keys)).all()

    def move_to_domain(self, target_domain_key: str) -> dict:
        """
        Move this project to a different domain.

        This operation:
        1. Updates the project's domain_key
        2. Updates all linked repositories' domain_key
        3. Updates all related work_sessions' domain_key
        4. Updates all entities created in those work sessions
        5. Updates the project's linked entity (if any)
        6. Removes team associations (teams are domain-specific)
        7. Clears agent project context

        Args:
            target_domain_key: The domain key to move the project to

        Returns:
            dict with summary of changes made

        Raises:
            ValueError: If target domain doesn't exist or is same as current
        """
        from api.models.domain import Domain
        from api.models.team_project import TeamProject
        from api.models.project_repository import ProjectRepository
        from api.models.repository import Repository
        from api.models.work_session import WorkSession
        from api.models.agent import Agent
        from api.models.entity import Entity

        # Validate target domain
        if target_domain_key == self.domain_key:
            raise ValueError("Project is already in this domain")

        target_domain = Domain.get_by_key(target_domain_key)
        if not target_domain:
            raise ValueError(f"Target domain not found: {target_domain_key}")

        source_domain_key = self.domain_key
        summary = {
            'project_key': self.project_key,
            'source_domain': source_domain_key,
            'target_domain': target_domain_key,
            'repositories_moved': 0,
            'work_sessions_updated': 0,
            'entities_updated': 0,
            'team_associations_removed': 0,
            'agents_cleared': 0,
        }

        # 1. Remove team associations (teams belong to specific domains)
        team_associations = TeamProject.get_teams_for_project(self.project_key)
        for assoc in team_associations:
            assoc.delete()
            summary['team_associations_removed'] += 1

        # 2. Update linked repositories' domain_key
        repo_associations = ProjectRepository.get_repositories_for_project(self.project_key)
        for assoc in repo_associations:
            repo = Repository.get_by_key(assoc.repository_key)
            if repo and repo.domain_key == source_domain_key:
                repo.domain_key = target_domain_key
                repo.save()
                summary['repositories_moved'] += 1

        # 3. Update work sessions' domain_key and collect session keys
        work_sessions = WorkSession.query.filter_by(project_key=self.project_key).all()
        session_keys = []
        for session in work_sessions:
            session_keys.append(session.session_key)
            if session.domain_key == source_domain_key:
                session.domain_key = target_domain_key
                session.save()
                summary['work_sessions_updated'] += 1

        # 4. Update entities created in those work sessions
        if session_keys:
            entities = Entity.query.filter(
                Entity.work_session_key.in_(session_keys),
                Entity.domain_key == source_domain_key
            ).all()
            for entity in entities:
                entity.domain_key = target_domain_key
                entity.save()
                summary['entities_updated'] += 1

        # 5. Update the project's linked entity (if any)
        if self.entity_key:
            project_entity = Entity.get_by_key(self.entity_key)
            if project_entity and project_entity.domain_key == source_domain_key:
                project_entity.domain_key = target_domain_key
                project_entity.save()
                # Only count if not already counted above
                if self.entity_key not in [e.entity_key for e in entities] if session_keys else True:
                    summary['entities_updated'] += 1

        # 6. Clear agent project context
        agents = Agent.query.filter_by(project_key=self.project_key).all()
        for agent in agents:
            agent.project_key = None
            agent.save()
            summary['agents_cleared'] += 1

        # 7. Update the project itself
        self.domain_key = target_domain_key
        self.save()

        return summary

    def to_dict(self, include_teams: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            'project_key': self.project_key,
            'name': self.name,
            'description': self.description,
            'repository_type': self.repository_type,
            'repository_url': self.repository_url,
            'repository_owner': self.repository_owner,
            'repository_name': self.repository_name,
            'domain_key': self.domain_key,
            'entity_key': self.entity_key,
            'status': self.status,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_teams:
            from api.models.team_project import TeamProject
            associations = TeamProject.get_teams_for_project(self.project_key)
            result['teams'] = [a.to_dict(include_team=True) for a in associations]

        return result
