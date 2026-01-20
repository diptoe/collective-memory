"""
Collective Memory Platform - ProjectRepository Junction Model

Links projects to repositories, enabling many-to-many relationships.
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from typing import Optional, List

from api.models.base import BaseModel, db, get_key, get_now


class ProjectRepository(BaseModel):
    """
    Junction table linking projects to repositories.

    Enables:
    - A project to have multiple repositories
    - A repository to belong to multiple projects
    """
    __tablename__ = 'project_repositories'
    __schema_version__ = 1

    # Primary key
    project_repository_key = Column(String(50), primary_key=True, default=get_key)

    # Foreign keys
    project_key = Column(String(50), ForeignKey('projects.project_key'), nullable=False, index=True)
    repository_key = Column(String(50), ForeignKey('repositories.repository_key'), nullable=False, index=True)

    # Timestamps
    created_at = Column(db.DateTime(timezone=True), default=get_now)
    updated_at = Column(db.DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Ensure unique project-repository combinations
    __table_args__ = (
        UniqueConstraint('project_key', 'repository_key', name='uq_project_repository'),
    )

    _default_fields = ['project_repository_key', 'project_key', 'repository_key', 'created_at']
    _readonly_fields = ['project_repository_key', 'created_at']

    @classmethod
    def get_repositories_for_project(cls, project_key: str) -> List['ProjectRepository']:
        """Get all repository associations for a project."""
        return cls.query.filter_by(project_key=project_key).all()

    @classmethod
    def get_projects_for_repository(cls, repository_key: str) -> List['ProjectRepository']:
        """Get all project associations for a repository."""
        return cls.query.filter_by(repository_key=repository_key).all()

    @classmethod
    def get_association(cls, project_key: str, repository_key: str) -> Optional['ProjectRepository']:
        """Get the association between a project and repository."""
        return cls.query.filter_by(project_key=project_key, repository_key=repository_key).first()

    @classmethod
    def create_association(
        cls,
        project_key: str,
        repository_key: str
    ) -> 'ProjectRepository':
        """
        Create a new project-repository association.

        Args:
            project_key: Project key
            repository_key: Repository key

        Returns:
            Created ProjectRepository instance

        Raises:
            ValueError: If association already exists
        """
        # Check if association already exists
        existing = cls.get_association(project_key, repository_key)
        if existing:
            raise ValueError(f"Association already exists between project {project_key} and repository {repository_key}")

        association = cls(
            project_key=project_key,
            repository_key=repository_key
        )
        association.save()
        return association

    def to_dict(self, include_project: bool = False, include_repository: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            'project_repository_key': self.project_repository_key,
            'project_key': self.project_key,
            'repository_key': self.repository_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_project:
            from api.models.project import Project
            project = Project.get_by_key(self.project_key)
            result['project'] = project.to_dict() if project else None

        if include_repository:
            from api.models.repository import Repository
            repository = Repository.get_by_key(self.repository_key)
            result['repository'] = repository.to_dict() if repository else None

        return result
