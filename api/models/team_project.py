"""
Collective Memory Platform - TeamProject Junction Model

Links teams to projects with role-based associations.
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from typing import Optional, List

from api.models.base import BaseModel, db, get_key, get_now


class TeamProject(BaseModel):
    """
    Junction table linking teams to projects.

    Supports role-based associations:
    - owner: Primary team responsible for the project
    - contributor: Team that contributes to the project
    - viewer: Team with read-only access
    """
    __tablename__ = 'team_projects'
    __schema_version__ = 1

    # Primary key
    team_project_key = Column(String(50), primary_key=True, default=get_key)

    # Foreign keys
    team_key = Column(String(50), ForeignKey('teams.team_key'), nullable=False, index=True)
    project_key = Column(String(50), ForeignKey('projects.project_key'), nullable=False, index=True)

    # Role
    role = Column(String(50), default='contributor')  # owner, contributor, viewer

    # Timestamps
    created_at = Column(db.DateTime(timezone=True), default=get_now)
    updated_at = Column(db.DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Ensure unique team-project combinations
    __table_args__ = (
        UniqueConstraint('team_key', 'project_key', name='uq_team_project'),
    )

    _default_fields = ['team_project_key', 'team_key', 'project_key', 'role', 'created_at']
    _readonly_fields = ['team_project_key', 'created_at']

    @classmethod
    def get_teams_for_project(cls, project_key: str) -> List['TeamProject']:
        """Get all team associations for a project."""
        return cls.query.filter_by(project_key=project_key).all()

    @classmethod
    def get_projects_for_team(cls, team_key: str) -> List['TeamProject']:
        """Get all project associations for a team."""
        return cls.query.filter_by(team_key=team_key).all()

    @classmethod
    def get_association(cls, team_key: str, project_key: str) -> Optional['TeamProject']:
        """Get the association between a team and project."""
        return cls.query.filter_by(team_key=team_key, project_key=project_key).first()

    @classmethod
    def create_association(
        cls,
        team_key: str,
        project_key: str,
        role: str = 'contributor'
    ) -> 'TeamProject':
        """
        Create a new team-project association.

        Args:
            team_key: Team key
            project_key: Project key
            role: Role (owner, contributor, viewer)

        Returns:
            Created TeamProject instance

        Raises:
            ValueError: If association already exists or invalid role
        """
        if role not in ('owner', 'contributor', 'viewer'):
            raise ValueError(f"Invalid role: {role}. Must be owner, contributor, or viewer.")

        # Check if association already exists
        existing = cls.get_association(team_key, project_key)
        if existing:
            raise ValueError(f"Association already exists between team {team_key} and project {project_key}")

        association = cls(
            team_key=team_key,
            project_key=project_key,
            role=role
        )
        association.save()
        return association

    @classmethod
    def get_owner_team(cls, project_key: str) -> Optional['TeamProject']:
        """Get the owner team association for a project."""
        return cls.query.filter_by(project_key=project_key, role='owner').first()

    def to_dict(self, include_team: bool = False, include_project: bool = False) -> dict:
        """Convert to dictionary for API response."""
        result = {
            'team_project_key': self.team_project_key,
            'team_key': self.team_key,
            'project_key': self.project_key,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_team:
            from api.models.team import Team
            team = Team.get_by_key(self.team_key)
            result['team'] = team.to_dict() if team else None

        if include_project:
            from api.models.project import Project
            project = Project.get_by_key(self.project_key)
            result['project'] = project.to_dict() if project else None

        return result
