"""
Collective Memory Platform - Model Model

AI models (LLMs) as first-class entities.
"""
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from api.models.base import BaseModel, db, get_key, get_now

if TYPE_CHECKING:
    from api.models.client import Client


class Model(BaseModel):
    """
    AI Model representing an LLM.

    Models are the actual AI systems (Claude Opus 4.5, GPT-5.2, etc.)
    separate from personas (behavioral roles) and clients (connecting platforms).
    """
    __tablename__ = 'models'
    _schema_version = 2

    __schema_updates__ = {
        2: [
            ("client_key", Column(String(50), ForeignKey('clients.client_key'), nullable=True, index=True)),
        ]
    }

    model_key = Column(String(36), primary_key=True, default=get_key)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False, index=True)  # anthropic, openai, google
    model_id = Column(String(100), nullable=False, unique=True)  # API identifier
    capabilities = Column(JSONB, default=list)  # ['vision', 'code', 'reasoning']
    context_window = Column(Integer, nullable=True)
    max_output_tokens = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='active', index=True)  # active, deprecated, disabled
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Link to client (optional - models can be used by multiple clients)
    client_key = Column(String(50), ForeignKey('clients.client_key'), nullable=True, index=True)
    client = relationship('Client', back_populates='models')

    _default_fields = [
        'model_key', 'name', 'provider', 'model_id',
        'capabilities', 'context_window', 'max_output_tokens',
        'description', 'status', 'client_key'
    ]
    _readonly_fields = ['model_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 2

    @classmethod
    def get_active(cls) -> list['Model']:
        """Get all active models."""
        return cls.query.filter_by(status='active').all()

    @classmethod
    def get_by_provider(cls, provider: str) -> list['Model']:
        """Get models by provider."""
        return cls.query.filter_by(provider=provider, status='active').all()

    @classmethod
    def get_by_model_id(cls, model_id: str) -> 'Model':
        """Get model by its API identifier."""
        return cls.query.filter_by(model_id=model_id).first()

    def archive(self) -> bool:
        """Soft delete by setting status to deprecated."""
        self.status = 'deprecated'
        return self.save()

    def disable(self) -> bool:
        """Disable the model."""
        self.status = 'disabled'
        return self.save()

    def activate(self) -> bool:
        """Reactivate a deprecated/disabled model."""
        self.status = 'active'
        return self.save()
