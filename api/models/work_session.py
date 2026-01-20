"""
Collective Memory Platform - Work Session Model

Tracks focused work periods on projects, linking entities and messages
created during a session for context, audit trails, and analytics.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class WorkSession(BaseModel):
    """
    Work session for tracking focused work periods on projects.

    Sessions automatically close after 1 hour of inactivity.
    Entities and messages created during a session are linked via work_session_key.
    """
    __tablename__ = 'work_sessions'

    _schema_version = 2  # Bumped for agent_id column
    _readonly_fields = ['session_key', 'created_at', 'started_at']

    # Schema updates for auto-migration
    __schema_updates__ = {
        2: [
            ("agent_id", Column(String(100), nullable=True, index=True)),
        ]
    }

    # Primary key
    session_key = Column(String(64), primary_key=True, default=get_key)

    # User and context
    user_key = Column(String(64), ForeignKey('users.user_key'), nullable=False, index=True)
    project_key = Column(String(64), nullable=False, index=True)  # Project entity key
    team_key = Column(String(64), nullable=True, index=True)
    domain_key = Column(String(64), nullable=True, index=True)

    # Agent that started/owns the session (nullable for human-initiated sessions)
    # Uses agent_id (not agent_key) so records remain meaningful even if agent is deleted/recreated
    agent_id = Column(String(100), nullable=True, index=True)

    # Session details
    name = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default='active')  # active|closed|expired

    # Timestamps
    started_at = Column(DateTime(timezone=True), default=get_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), default=get_now)
    auto_close_at = Column(DateTime(timezone=True), nullable=True)

    # Closure details
    closed_by = Column(String(20), nullable=True)  # user|agent|system
    summary = Column(Text, nullable=True)

    # Flexible properties
    properties = Column(JSONB, default=dict)

    # Standard timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_work_sessions_user_status', 'user_key', 'status'),
        Index('ix_work_sessions_project_status', 'project_key', 'status'),
        Index('ix_work_sessions_auto_close', 'auto_close_at', 'status'),
    )

    # Auto-close timeout in hours
    AUTO_CLOSE_HOURS = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set auto_close_at on creation
        if self.auto_close_at is None:
            self._update_auto_close()

    def _update_auto_close(self):
        """Update auto_close_at based on current activity time."""
        now = get_now()
        self.last_activity_at = now
        self.auto_close_at = now + timedelta(hours=self.AUTO_CLOSE_HOURS)

    def update_activity(self) -> None:
        """
        Update activity timestamp and recalculate auto_close_at.
        Call this when any action is performed in the session.
        """
        if self.status != 'active':
            return
        self._update_auto_close()
        self.updated_at = get_now()

    def close(self, closed_by: str = 'user', summary: Optional[str] = None) -> None:
        """
        Close the session.

        Args:
            closed_by: Who/what closed the session (user, agent, system)
            summary: Optional summary of work done in the session
        """
        now = get_now()
        self.status = 'closed'
        self.ended_at = now
        self.closed_by = closed_by
        if summary:
            self.summary = summary
        self.updated_at = now

    def expire(self) -> None:
        """Mark the session as expired (called by system for auto-close)."""
        now = get_now()
        self.status = 'expired'
        self.ended_at = now
        self.closed_by = 'system'
        self.updated_at = now

    def extend(self, hours: float = 1.0) -> None:
        """
        Extend the auto_close_at time.

        Args:
            hours: Number of hours to extend from now
        """
        if self.status != 'active':
            return
        now = get_now()
        self.auto_close_at = now + timedelta(hours=hours)
        self.last_activity_at = now
        self.updated_at = now

    def is_expired(self) -> bool:
        """Check if the session has passed its auto_close_at time."""
        if self.status != 'active':
            return False
        if self.auto_close_at is None:
            return False
        return get_now() > self.auto_close_at

    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until auto-close, or None if not active."""
        if self.status != 'active' or self.auto_close_at is None:
            return None
        remaining = self.auto_close_at - get_now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    @classmethod
    def get_active_for_user(cls, user_key: str, project_key: Optional[str] = None) -> Optional['WorkSession']:
        """
        Find an active session for a user, optionally filtered by project.

        Args:
            user_key: The user's key
            project_key: Optional project to filter by

        Returns:
            Active WorkSession or None
        """
        query = cls.query.filter_by(user_key=user_key, status='active')
        if project_key:
            query = query.filter_by(project_key=project_key)
        return query.order_by(cls.started_at.desc()).first()

    @classmethod
    def get_expired_sessions(cls) -> List['WorkSession']:
        """Get all sessions that have passed their auto_close_at time."""
        now = get_now()
        return cls.query.filter(
            cls.status == 'active',
            cls.auto_close_at <= now
        ).all()

    @classmethod
    def close_expired_sessions(cls) -> int:
        """
        Close all expired sessions.

        Returns:
            Number of sessions closed
        """
        sessions = cls.get_expired_sessions()
        count = 0
        for session in sessions:
            session.expire()
            session.save()
            count += 1
        return count

    def to_dict(self, include_relationships: bool = False, include_project: bool = True, include_agent: bool = True) -> dict:
        """Convert to dictionary for API response."""
        result = {
            'session_key': self.session_key,
            'user_key': self.user_key,
            'agent_id': self.agent_id,
            'project_key': self.project_key,
            'team_key': self.team_key,
            'domain_key': self.domain_key,
            'name': self.name,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'auto_close_at': self.auto_close_at.isoformat() if self.auto_close_at else None,
            'closed_by': self.closed_by,
            'summary': self.summary,
            'properties': self.properties or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add computed fields
        remaining = self.time_remaining()
        if remaining is not None:
            result['time_remaining_seconds'] = int(remaining.total_seconds())

        # Include enriched project data
        if include_project and self.project_key:
            result['project'] = self._get_project_info()

        # Include enriched agent data
        if include_agent and self.agent_id:
            result['agent'] = self._get_agent_info()

        return result

    def _get_project_info(self) -> Optional[dict]:
        """Get enriched project information."""
        from api.models.project import Project

        # First try to find in Project table (new style)
        project = Project.query.get(self.project_key)
        if project:
            return {
                'project_key': project.project_key,
                'name': project.name,
                'description': project.description,
                'repository_type': project.repository_type,
                'repository_url': project.repository_url,
                'repository_owner': project.repository_owner,
                'repository_name': project.repository_name,
            }

        # Fall back to Entity (old style - project_key is an entity_key)
        from api.models.entity import Entity
        entity = Entity.get_by_key(self.project_key)
        if entity:
            props = entity.properties or {}
            return {
                'entity_key': entity.entity_key,
                'name': entity.name,
                'description': props.get('description'),
                # Try to extract repo info from entity properties
                'repository_url': props.get('repository_url'),
                'repository_owner': props.get('repository_owner'),
                'repository_name': props.get('repository_name'),
            }

        return None

    def _get_agent_info(self) -> Optional[dict]:
        """Get enriched agent information."""
        from api.models.agent import Agent
        from api.models.persona import Persona
        from api.models.model import Model

        agent = Agent.query.filter_by(agent_id=self.agent_id).first()
        if not agent:
            return None

        result = {
            'agent_id': agent.agent_id,
            'agent_key': agent.agent_key,
            'client': agent.client,
            'user_key': agent.user_key,
            'user_name': agent.user_name,
            'user_initials': agent.user_initials,
        }

        # Get persona name
        if agent.persona_key:
            persona = Persona.query.get(agent.persona_key)
            if persona:
                result['persona_name'] = persona.name
                result['persona_role'] = persona.role

        # Get model name
        if agent.model_key:
            model = Model.query.get(agent.model_key)
            if model:
                result['model_name'] = model.name
                result['model_id'] = model.model_id

        return result
