"""
Collective Memory Platform - Relationship Model

Relationships between knowledge graph entities.
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from api.models.base import BaseModel, db, get_key, get_now


class Relationship(BaseModel):
    """
    Relationship between two entities in the knowledge graph.

    Relationship types: WORKS_ON, USES_TECHNOLOGY, DEPENDS_ON, COLLABORATES_WITH, etc.
    """
    __tablename__ = 'relationships'

    relationship_key = Column(String(36), primary_key=True, default=get_key)
    from_entity_key = Column(String(36), ForeignKey('entities.entity_key'), nullable=False, index=True)
    to_entity_key = Column(String(36), ForeignKey('entities.entity_key'), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)
    properties = Column(JSONB, default=dict)
    confidence = Column(Float, default=1.0)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Relationships to Entity model
    from_entity = relationship('Entity', foreign_keys=[from_entity_key], backref='outgoing_relationships')
    to_entity = relationship('Entity', foreign_keys=[to_entity_key], backref='incoming_relationships')

    # Indexes for graph traversal
    __table_args__ = (
        Index('ix_relationships_from_to', 'from_entity_key', 'to_entity_key'),
        Index('ix_relationships_type', 'relationship_type'),
    )

    _default_fields = ['relationship_key', 'from_entity_key', 'to_entity_key', 'relationship_type', 'properties']
    _readonly_fields = ['relationship_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def get_by_entity(cls, entity_key: str) -> list['Relationship']:
        """Get all relationships involving an entity (as source or target)."""
        return cls.query.filter(
            (cls.from_entity_key == entity_key) | (cls.to_entity_key == entity_key)
        ).all()

    @classmethod
    def get_by_type(cls, relationship_type: str, limit: int = 100) -> list['Relationship']:
        """Get relationships by type."""
        return cls.query.filter_by(relationship_type=relationship_type).limit(limit).all()

    @classmethod
    def get_path(cls, from_key: str, to_key: str, max_hops: int = 3) -> list[list['Relationship']]:
        """
        Find paths between two entities.

        Returns list of paths, where each path is a list of relationships.
        Simple BFS implementation for now.
        """
        # TODO: Implement proper graph traversal
        # For Phase 1, just return direct relationships
        direct = cls.query.filter_by(
            from_entity_key=from_key,
            to_entity_key=to_key
        ).all()
        return [[r] for r in direct] if direct else []

    def to_dict(self, include_entities: bool = False) -> dict:
        """Convert to dictionary with optional entity details."""
        result = super().to_dict()

        if include_entities:
            if self.from_entity:
                result['from_entity'] = {
                    'entity_key': self.from_entity.entity_key,
                    'name': self.from_entity.name,
                    'entity_type': self.from_entity.entity_type
                }
            if self.to_entity:
                result['to_entity'] = {
                    'entity_key': self.to_entity.entity_key,
                    'name': self.to_entity.name,
                    'entity_type': self.to_entity.entity_type
                }

        return result
