"""
Collective Memory Platform - Agent Model

Agent registration and status tracking.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Agent(BaseModel):
    """
    Registered agent in the collaboration system.

    An agent represents a running instance with:
    - Identity (agent_id)
    - Client type (claude-code, claude-desktop, etc.)
    - Model (the LLM being used)
    - Persona (behavioral role)
    - Focus (current work description)
    """
    __tablename__ = 'agents'

    agent_key = Column(String(36), primary_key=True, default=get_key)
    agent_id = Column(String(100), unique=True, nullable=False, index=True)

    # Link to owning user (agents belong to users, users belong to domains)
    user_key = Column(String(36), ForeignKey('users.user_key'), nullable=True, index=True)

    # Client type (claude-code, claude-desktop, codex, gemini-cli)
    client = Column(String(50), nullable=True, index=True)

    # Foreign keys to Model and Persona (nullable for backward compatibility)
    model_key = Column(String(36), ForeignKey('models.model_key'), nullable=True)
    persona_key = Column(String(36), ForeignKey('personas.persona_key'), nullable=True)

    # Current work focus
    focus = Column(Text, nullable=True)
    focus_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Focused mode - agent actively waiting for response (fast heartbeats)
    focused_mode = Column(Boolean, default=False)
    focused_mode_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Legacy field - deprecated, use persona_key instead
    role = Column(String(100), nullable=True)

    capabilities = Column(JSONB, default=list)
    status = Column(JSONB, default=dict)
    last_heartbeat = Column(DateTime(timezone=True), default=get_now)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    _default_fields = [
        'agent_key', 'agent_id', 'user_key', 'client', 'model_key', 'persona_key',
        'focus', 'focused_mode', 'role', 'capabilities', 'status'
    ]
    _readonly_fields = ['agent_key', 'created_at']

    # Focused mode default duration (10 minutes)
    FOCUSED_MODE_DURATION_MINUTES = 10

    @classmethod
    def current_schema_version(cls) -> int:
        return 4  # Bumped for user_key field

    @classmethod
    def migrate(cls) -> bool:
        """
        Migrate existing Agent records to link to a user.

        All existing agents without a user_key are linked to the first admin user.
        This allows domain-based access control to work retroactively.
        """
        from api.models.user import User

        migrated = False
        # Only migrate records that have NULL user_key
        records = cls.query.filter(cls.user_key.is_(None)).all()

        if not records:
            return False

        # Find the first admin user to assign orphaned agents to
        admin_user = User.query.filter_by(is_admin=True).order_by(User.created_at.asc()).first()

        if not admin_user:
            # No admin user exists yet, can't migrate
            return False

        for r in records:
            r.user_key = admin_user.user_key
            db.session.add(r)
            migrated = True

        if migrated:
            db.session.commit()

        return migrated

    @classmethod
    def get_by_agent_id(cls, agent_id: str) -> 'Agent':
        """Get agent by agent_id."""
        return cls.query.filter_by(agent_id=agent_id).first()

    @classmethod
    def get_active_agents(cls, timeout_minutes: int = 15) -> list['Agent']:
        """Get agents that have sent a heartbeat within timeout period."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        return cls.query.filter(cls.last_heartbeat > cutoff).all()

    @classmethod
    def get_by_role(cls, role: str) -> list['Agent']:
        """Get agents by role (legacy - use get_by_persona_key)."""
        return cls.query.filter_by(role=role).all()

    @classmethod
    def get_by_client(cls, client: str) -> list['Agent']:
        """Get agents by client type."""
        return cls.query.filter_by(client=client).all()

    @classmethod
    def get_by_persona_key(cls, persona_key: str) -> list['Agent']:
        """Get agents by persona."""
        return cls.query.filter_by(persona_key=persona_key).all()

    @classmethod
    def get_by_model_key(cls, model_key: str) -> list['Agent']:
        """Get agents by model."""
        return cls.query.filter_by(model_key=model_key).all()

    @classmethod
    def get_by_user_key(cls, user_key: str) -> list['Agent']:
        """Get agents owned by a specific user."""
        return cls.query.filter_by(user_key=user_key).all()

    @classmethod
    def get_active_by_user(cls, user_key: str, timeout_minutes: int = 15) -> list['Agent']:
        """Get active agents for a specific user."""
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        return cls.query.filter(
            cls.user_key == user_key,
            cls.last_heartbeat > cutoff
        ).all()

    def update_heartbeat(self) -> bool:
        """Update the agent's heartbeat timestamp."""
        self.last_heartbeat = get_now()
        return self.save()

    def update_status(self, status: dict) -> bool:
        """Update the agent's status."""
        self.status = status
        self.last_heartbeat = get_now()
        return self.save()

    def update_focus(self, focus: str | None) -> bool:
        """Update the agent's current work focus. Pass None to clear."""
        self.focus = focus
        self.focus_updated_at = get_now()
        self.last_heartbeat = get_now()
        return self.save()

    def set_focused_mode(self, enabled: bool, duration_minutes: int = None) -> bool:
        """
        Set focused mode for fast heartbeats.

        When enabled, the agent signals it's actively waiting for a response
        and should use faster heartbeat intervals (e.g., 30 seconds vs 5 minutes).

        Args:
            enabled: True to enable focused mode, False to disable
            duration_minutes: How long focused mode should last (default 10 min)
        """
        self.focused_mode = enabled
        if enabled:
            duration = duration_minutes or self.FOCUSED_MODE_DURATION_MINUTES
            self.focused_mode_expires_at = get_now() + timedelta(minutes=duration)
        else:
            self.focused_mode_expires_at = None
        self.last_heartbeat = get_now()
        return self.save()

    @property
    def is_focused(self) -> bool:
        """Check if agent is in focused mode (and mode hasn't expired)."""
        if not self.focused_mode:
            return False
        if self.focused_mode_expires_at:
            return get_now() < self.focused_mode_expires_at
        return True

    @property
    def is_active(self) -> bool:
        """Check if agent is considered active (heartbeat within 15 minutes)."""
        if not self.last_heartbeat:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        return self.last_heartbeat > cutoff

    def to_dict(self, include_active_status: bool = True, expand_relations: bool = True) -> dict:
        """Convert to dictionary.

        Args:
            include_active_status: Include is_active computed field
            expand_relations: Expand model_key and persona_key to full objects
        """
        result = super().to_dict()
        if include_active_status:
            result['is_active'] = self.is_active
            result['is_focused'] = self.is_focused

        # Expand model and persona to full objects for UI
        if expand_relations:
            if self.model_key:
                from api.models import Model
                model = Model.get_by_key(self.model_key)
                if model:
                    result['model'] = {
                        'model_key': model.model_key,
                        'name': model.name,
                        'provider': model.provider,
                        'model_id': model.model_id,
                    }

            if self.persona_key:
                from api.models import Persona
                persona = Persona.get_by_key(self.persona_key)
                if persona:
                    result['persona'] = {
                        'persona_key': persona.persona_key,
                        'name': persona.name,
                        'role': persona.role,
                        'color': persona.color,
                    }

        return result
