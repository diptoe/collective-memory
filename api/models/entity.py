"""
Collective Memory Platform - Entity Model

Knowledge graph entities representing concepts, people, projects, etc.
"""
from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from api.models.base import BaseModel, db, get_key, get_now


class Entity(BaseModel):
    """
    Knowledge graph entity.

    Entity types: Person, Project, Technology, Document, Organization, Concept
    """
    __tablename__ = 'entities'

    entity_key = Column(String(36), primary_key=True, default=get_key)
    entity_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    properties = Column(JSONB, default=dict)
    context_domain = Column(String(100), nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_entities_type_domain', 'entity_type', 'context_domain'),
        Index('ix_entities_name_search', 'name'),
    )

    _default_fields = ['entity_key', 'entity_type', 'name', 'properties', 'context_domain']
    _readonly_fields = ['entity_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def get_by_type(cls, entity_type: str, limit: int = 100) -> list['Entity']:
        """Get entities by type."""
        return cls.query.filter_by(entity_type=entity_type).limit(limit).all()

    @classmethod
    def search_by_name(cls, name_query: str, limit: int = 20) -> list['Entity']:
        """Search entities by name (case-insensitive contains)."""
        return cls.query.filter(
            cls.name.ilike(f'%{name_query}%')
        ).limit(limit).all()

    @classmethod
    def get_by_domain(cls, context_domain: str, limit: int = 100) -> list['Entity']:
        """Get entities by context domain."""
        return cls.query.filter_by(context_domain=context_domain).limit(limit).all()

    def to_dict(self, include_relationships: bool = False) -> dict:
        """Convert to dictionary with optional relationships."""
        result = super().to_dict()

        if include_relationships:
            from api.models.relationship import Relationship
            # Get relationships where this entity is the source or target
            outgoing = Relationship.query.filter_by(from_entity_key=self.entity_key).all()
            incoming = Relationship.query.filter_by(to_entity_key=self.entity_key).all()
            result['relationships'] = {
                'outgoing': [r.to_dict() for r in outgoing],
                'incoming': [r.to_dict() for r in incoming]
            }

        return result
