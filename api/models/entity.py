"""
Collective Memory Platform - Entity Model

Knowledge graph entities representing concepts, people, projects, etc.
"""

import os
from sqlalchemy import Column, String, Float, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

from api.models.base import BaseModel, db, get_key, get_now

# Enable pgvector-backed VECTOR columns only when the DB extension is available.
PGVECTOR_ENABLED = (
    PGVECTOR_AVAILABLE
    and os.getenv("CM_ENABLE_PGVECTOR", "false").lower() in ("1", "true", "yes")
)


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
    domain_key = Column(String(100), nullable=True, index=True)
    confidence = Column(Float, default=1.0)
    source = Column(String(100), nullable=True)

    # Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    if PGVECTOR_ENABLED:
        embedding = Column(Vector(1536), nullable=True)
    else:
        embedding = Column(Text, nullable=True)  # Fallback for dev / DB without pgvector extension

    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_entities_type_domain', 'entity_type', 'domain_key'),
        Index('ix_entities_name_search', 'name'),
    )

    _default_fields = ['entity_key', 'entity_type', 'name', 'properties', 'domain_key']
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
    def get_by_domain(cls, domain_key: str, limit: int = 100) -> list['Entity']:
        """Get entities by domain."""
        return cls.query.filter_by(domain_key=domain_key).limit(limit).all()

    @classmethod
    def search_semantic(
        cls,
        query_embedding: List[float],
        limit: int = 10,
        entity_type: str = None,
        threshold: float = None
    ) -> List['Entity']:
        """
        Semantic similarity search using cosine distance.

        Args:
            query_embedding: Query embedding vector (1536 dimensions)
            limit: Maximum results
            entity_type: Filter by entity type
            threshold: Optional similarity threshold (0-1, higher is more similar)

        Returns:
            List of entities ordered by similarity
        """
        if not PGVECTOR_ENABLED:
            raise RuntimeError(
                "pgvector semantic search disabled. "
                "Enable with CM_ENABLE_PGVECTOR=true and ensure the Postgres pgvector extension is installed."
            )

        query = cls.query.filter(cls.embedding.isnot(None))

        if entity_type:
            query = query.filter(cls.entity_type == entity_type)

        # Order by cosine distance (smaller = more similar)
        query = query.order_by(
            cls.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        return query.all()

    @classmethod
    def search_hybrid(
        cls,
        keyword: str,
        query_embedding: List[float],
        limit: int = 10,
        keyword_weight: float = 0.3
    ) -> List['Entity']:
        """
        Hybrid search combining keyword and semantic search.

        Args:
            keyword: Keyword to search for in name
            query_embedding: Query embedding vector
            limit: Maximum results
            keyword_weight: Weight for keyword results (0-1)

        Returns:
            List of entities with combined ranking
        """
        if not PGVECTOR_ENABLED:
            # Fall back to keyword search only
            return cls.search_by_name(keyword, limit=limit)

        # Get keyword matches
        keyword_results = cls.search_by_name(keyword, limit=limit * 2)
        keyword_keys = {e.entity_key for e in keyword_results}

        # Get semantic matches
        semantic_results = cls.search_semantic(query_embedding, limit=limit * 2)

        # Combine results with simple fusion
        seen = set()
        combined = []

        # Add keyword matches first (weighted higher)
        for entity in keyword_results:
            if entity.entity_key not in seen:
                combined.append(entity)
                seen.add(entity.entity_key)

        # Add semantic matches
        for entity in semantic_results:
            if entity.entity_key not in seen:
                combined.append(entity)
                seen.add(entity.entity_key)

        return combined[:limit]

    def set_embedding(self, embedding: List[float]) -> None:
        """
        Set the embedding vector.

        Args:
            embedding: List of floats (1536 dimensions)
        """
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must be 1536 dimensions, got {len(embedding)}")
        self.embedding = embedding

    def generate_embedding(self, embedding_service=None) -> List[float]:
        """
        Generate and set embedding from entity name and properties.

        Args:
            embedding_service: Optional EmbeddingService instance

        Returns:
            The generated embedding
        """
        if embedding_service is None:
            from api.services import embedding_service

        # Build text representation
        parts = [self.name, f"({self.entity_type})"]
        if self.properties:
            for key, value in self.properties.items():
                if isinstance(value, str) and len(value) < 200:
                    parts.append(f"{key}: {value}")

        text = " ".join(parts)
        embedding = embedding_service.get_embedding(text)
        self.set_embedding(embedding)
        return embedding

    def to_dict(self, include_relationships: bool = False, include_embedding: bool = False) -> dict:
        """Convert to dictionary with optional relationships and embedding."""
        result = super().to_dict()

        # Add embedding info
        result['has_embedding'] = self.embedding is not None
        if not include_embedding:
            # Remove raw embedding from result (it's included by super().to_dict())
            result.pop('embedding', None)

        if include_relationships:
            from api.models.relationship import Relationship
            # Get relationships where this entity is the source or target
            outgoing = Relationship.query.filter_by(from_entity_key=self.entity_key).all()
            incoming = Relationship.query.filter_by(to_entity_key=self.entity_key).all()
            result['relationships'] = {
                'outgoing': [r.to_dict(include_entities=True) for r in outgoing],
                'incoming': [r.to_dict(include_entities=True) for r in incoming]
            }

        return result
