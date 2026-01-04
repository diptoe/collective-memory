"""
Collective Memory Platform - Persona Model

Behavioral personas for AI agents (decoupled from models).
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Persona(BaseModel):
    """
    AI persona representing a behavioral role.

    Personas define personality, system prompts, and capabilities.
    They are decoupled from Models (the LLM) and Clients (the platform).
    """
    __tablename__ = 'personas'

    persona_key = Column(String(36), primary_key=True, default=get_key)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False, unique=True, index=True)  # Unique identifier
    system_prompt = Column(Text, nullable=True)
    personality = Column(JSONB, default=dict)
    capabilities = Column(JSONB, default=list)
    suggested_clients = Column(JSONB, default=list)  # ['claude-code', 'codex']
    avatar_url = Column(String(500), nullable=True)
    color = Column(String(20), default='#d97757')
    status = Column(String(20), default='active', index=True)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    _default_fields = [
        'persona_key', 'name', 'role', 'system_prompt', 'personality',
        'capabilities', 'suggested_clients', 'color', 'status'
    ]
    _readonly_fields = ['persona_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 2  # Bumped for schema change

    @classmethod
    def get_active(cls) -> list['Persona']:
        """Get all active personas."""
        return cls.query.filter_by(status='active').all()

    @classmethod
    def get_by_role(cls, role: str) -> list['Persona']:
        """Get personas by role."""
        return cls.query.filter_by(role=role, status='active').all()

    @classmethod
    def get_by_client(cls, client: str) -> list['Persona']:
        """Get personas suggested for a specific client type."""
        # Uses PostgreSQL JSONB contains operator
        return cls.query.filter(
            cls.suggested_clients.contains([client]),
            cls.status == 'active'
        ).all()

    def archive(self) -> bool:
        """Soft delete by setting status to archived."""
        self.status = 'archived'
        return self.save()

    def activate(self) -> bool:
        """Reactivate an archived persona."""
        self.status = 'active'
        return self.save()

    def to_dict(self, include_system_prompt: bool = False) -> dict:
        """Convert to dictionary, optionally excluding system prompt."""
        result = super().to_dict()
        if not include_system_prompt:
            result.pop('system_prompt', None)
        return result
