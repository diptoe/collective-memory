"""
Collective Memory Platform - Persona Model

AI model personas for chat interactions.
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Persona(BaseModel):
    """
    AI persona representing a model/terminal instance.

    Each persona has a distinct personality, role, and capabilities.
    """
    __tablename__ = 'personas'

    persona_key = Column(String(36), primary_key=True, default=get_key)
    name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False, index=True)
    system_prompt = Column(Text, nullable=True)
    personality = Column(JSONB, default=dict)
    capabilities = Column(JSONB, default=list)
    avatar_url = Column(String(500), nullable=True)
    color = Column(String(20), default='#d97757')
    status = Column(String(20), default='active', index=True)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    _default_fields = ['persona_key', 'name', 'model', 'role', 'system_prompt', 'personality', 'capabilities', 'color', 'status']
    _readonly_fields = ['persona_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def get_active(cls) -> list['Persona']:
        """Get all active personas."""
        return cls.query.filter_by(status='active').all()

    @classmethod
    def get_by_role(cls, role: str) -> list['Persona']:
        """Get personas by role."""
        return cls.query.filter_by(role=role, status='active').all()

    @classmethod
    def get_by_model(cls, model: str) -> list['Persona']:
        """Get personas by model type."""
        return cls.query.filter_by(model=model, status='active').all()

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
