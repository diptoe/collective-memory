"""
Collective Memory Platform - Agent Checkpoint Model

Checkpoint and state persistence for agents.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from api.models.base import BaseModel, db, get_key, get_now


class AgentCheckpoint(BaseModel):
    """
    Agent checkpoint for state persistence.

    Stores agent state at a point in time for recovery and debugging.
    """
    __tablename__ = 'agent_checkpoints'

    checkpoint_key = Column(String(36), primary_key=True, default=get_key)
    agent_key = Column(String(36), ForeignKey('agents.agent_key'), nullable=False, index=True)
    checkpoint_type = Column(String(50), nullable=False, default='manual')  # 'auto', 'manual', 'error', 'milestone'
    name = Column(String(200))
    description = Column(Text)
    state_data = Column(JSONB, default=dict)  # Full agent state snapshot
    conversation_keys = Column(JSONB, default=list)  # Associated conversations
    extra_data = Column(JSONB, default=dict)  # Additional context
    created_at = Column(DateTime(timezone=True), default=get_now)

    # Relationships
    agent = relationship('Agent', backref='checkpoints')

    _default_fields = ['checkpoint_key', 'agent_key', 'checkpoint_type', 'name', 'description', 'created_at']
    _readonly_fields = ['checkpoint_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def get_by_agent(cls, agent_key: str, limit: int = 10, checkpoint_type: str = None) -> list['AgentCheckpoint']:
        """Get checkpoints for an agent."""
        query = cls.query.filter_by(agent_key=agent_key)
        if checkpoint_type:
            query = query.filter_by(checkpoint_type=checkpoint_type)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_latest(cls, agent_key: str) -> 'AgentCheckpoint':
        """Get the most recent checkpoint for an agent."""
        return cls.query.filter_by(agent_key=agent_key).order_by(cls.created_at.desc()).first()

    @classmethod
    def create_checkpoint(
        cls,
        agent_key: str,
        checkpoint_type: str = 'manual',
        name: str = None,
        description: str = None,
        state_data: dict = None,
        conversation_keys: list = None,
        extra_data: dict = None,
    ) -> 'AgentCheckpoint':
        """Create a new checkpoint for an agent."""
        checkpoint = cls(
            agent_key=agent_key,
            checkpoint_type=checkpoint_type,
            name=name or f"{checkpoint_type.capitalize()} checkpoint",
            description=description,
            state_data=state_data or {},
            conversation_keys=conversation_keys or [],
            extra_data=extra_data or {},
        )
        checkpoint.save()
        return checkpoint

    @classmethod
    def cleanup_old_checkpoints(cls, agent_key: str, keep_count: int = 20) -> int:
        """Remove old checkpoints, keeping only the most recent ones."""
        # Get checkpoint keys to keep
        keep_checkpoints = cls.query.filter_by(agent_key=agent_key)\
            .order_by(cls.created_at.desc())\
            .limit(keep_count)\
            .with_entities(cls.checkpoint_key)\
            .all()
        keep_keys = [c[0] for c in keep_checkpoints]

        # Delete others
        if keep_keys:
            deleted = cls.query.filter(
                cls.agent_key == agent_key,
                ~cls.checkpoint_key.in_(keep_keys)
            ).delete(synchronize_session=False)
            db.session.commit()
            return deleted
        return 0

    def to_dict(self, include_state: bool = False) -> dict:
        """Convert to dictionary."""
        result = {
            'checkpoint_key': self.checkpoint_key,
            'agent_key': self.agent_key,
            'checkpoint_type': self.checkpoint_type,
            'name': self.name,
            'description': self.description,
            'conversation_keys': self.conversation_keys,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_state:
            result['state_data'] = self.state_data
        return result
