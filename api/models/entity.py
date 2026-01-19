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

# TYPE_CHECKING import to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from api.models.user import User

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

    # Scope columns for fine-grained visibility control
    # scope_type: 'domain', 'team', 'user', or NULL (NULL = domain-scoped for backward compatibility)
    # scope_key: team_key or user_key depending on scope_type
    scope_type = Column(String(20), nullable=True, index=True)
    scope_key = Column(String(36), nullable=True, index=True)

    # Work session tracking - links entity to the session it was created in
    work_session_key = Column(String(64), nullable=True, index=True)

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
        Index('ix_entities_scope', 'scope_type', 'scope_key'),
    )

    _default_fields = ['entity_key', 'entity_type', 'name', 'properties', 'domain_key']
    _readonly_fields = ['entity_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 3  # Added work_session_key for session tracking

    @classmethod
    def get_by_type(cls, entity_type: str, limit: int = 100) -> list['Entity']:
        """Get entities by type."""
        return cls.query.filter_by(entity_type=entity_type).limit(limit).all()

    @classmethod
    def search_by_name(
        cls,
        name_query: str,
        limit: int = 20,
        user: 'User' = None,
        domain_key: str = None
    ) -> list['Entity']:
        """
        Search entities by name (case-insensitive contains).

        Args:
            name_query: Search string
            limit: Maximum results
            user: Optional user for scope filtering
            domain_key: Optional domain filter (used if user not provided)

        Returns:
            List of matching entities
        """
        query = cls.query.filter(cls.name.ilike(f'%{name_query}%'))

        # Apply scope filtering if user provided
        if user:
            from api.services.scope import scope_service
            query = scope_service.filter_query_by_scope(query, user, cls)
        elif domain_key:
            # Fall back to domain filter if no user
            query = query.filter(cls.domain_key == domain_key)

        return query.limit(limit).all()

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
        threshold: float = None,
        user: 'User' = None,
        domain_key: str = None
    ) -> List['Entity']:
        """
        Semantic similarity search using cosine distance.

        Args:
            query_embedding: Query embedding vector (1536 dimensions)
            limit: Maximum results
            entity_type: Filter by entity type
            threshold: Optional similarity threshold (0-1, higher is more similar)
            user: Optional user for scope filtering
            domain_key: Optional domain filter (used if user not provided)

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

        # Apply scope filtering if user provided
        if user:
            from api.services.scope import scope_service
            query = scope_service.filter_query_by_scope(query, user, cls)
        elif domain_key:
            # Fall back to domain filter if no user
            query = query.filter(cls.domain_key == domain_key)

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
        keyword_weight: float = 0.3,
        user: 'User' = None,
        domain_key: str = None
    ) -> List['Entity']:
        """
        Hybrid search combining keyword and semantic search.

        Args:
            keyword: Keyword to search for in name
            query_embedding: Query embedding vector
            limit: Maximum results
            keyword_weight: Weight for keyword results (0-1)
            user: Optional user for scope filtering
            domain_key: Optional domain filter (used if user not provided)

        Returns:
            List of entities with combined ranking
        """
        if not PGVECTOR_ENABLED:
            # Fall back to keyword search only
            return cls.search_by_name(keyword, limit=limit, user=user, domain_key=domain_key)

        # Get keyword matches (with scope filtering)
        keyword_results = cls.search_by_name(keyword, limit=limit * 2, user=user, domain_key=domain_key)
        keyword_keys = {e.entity_key for e in keyword_results}

        # Get semantic matches (with scope filtering)
        semantic_results = cls.search_semantic(query_embedding, limit=limit * 2, user=user, domain_key=domain_key)

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

        # Resolve scope_name for human-readable display
        if self.scope_type and self.scope_key:
            result['scope_name'] = self._resolve_scope_name()
        else:
            result['scope_name'] = None

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

    def _resolve_scope_name(self) -> str | None:
        """Resolve the scope_key to a human-readable name."""
        if not self.scope_type or not self.scope_key:
            return None

        if self.scope_type == 'domain':
            from api.models.domain import Domain
            domain = Domain.get_by_key(self.scope_key)
            return domain.name if domain else None
        elif self.scope_type == 'team':
            from api.models.team import Team
            team = Team.get_by_key(self.scope_key)
            return team.name if team else None
        elif self.scope_type == 'user':
            from api.models.user import User
            user = User.get_by_key(self.scope_key)
            return user.display_name if user else None

        return None

    # ============================================================
    # SOURCE BRIDGE PATTERN
    # ============================================================
    # The source column can link entities to database records using
    # the format: *type*{key}
    # Examples: *project*{calm-fresh-river}, *agent*{swift-bold-lion}

    @classmethod
    def parse_source_bridge(cls, source: str) -> dict | None:
        """
        Parse source bridge format *type*{key}.

        Args:
            source: Source string to parse

        Returns:
            Dict with 'type' and 'key' if valid bridge format, None otherwise
        """
        if not source or not source.startswith('*'):
            return None
        import re
        match = re.match(r'\*(\w+)\*\{([^}]+)\}', source)
        if match:
            return {'type': match.group(1), 'key': match.group(2)}
        return None

    @staticmethod
    def create_source_bridge(record_type: str, key: str) -> str:
        """
        Create source bridge format.

        Args:
            record_type: Type of the linked record (e.g., 'project', 'agent')
            key: Key of the linked record

        Returns:
            Source bridge string in format *type*{key}
        """
        return f"*{record_type}*{{{key}}}"

    def get_linked_record(self):
        """
        Get the database record linked via source bridge.

        Returns:
            The linked record if found, None otherwise
        """
        bridge = self.parse_source_bridge(self.source)
        if not bridge:
            return None

        record_type = bridge['type']
        key = bridge['key']

        if record_type == 'project':
            from api.models.project import Project
            return Project.get_by_key(key)
        elif record_type == 'agent':
            from api.models.agent import Agent
            return Agent.get_by_key(key)
        elif record_type == 'team':
            from api.models.team import Team
            return Team.get_by_key(key)
        elif record_type == 'user':
            from api.models.user import User
            return User.get_by_key(key)
        elif record_type == 'domain':
            from api.models.domain import Domain
            return Domain.get_by_key(key)

        return None

    def has_source_bridge(self) -> bool:
        """Check if this entity has a source bridge."""
        return self.parse_source_bridge(self.source) is not None

    def get_source_bridge_type(self) -> str | None:
        """Get the type of the source bridge if present."""
        bridge = self.parse_source_bridge(self.source)
        return bridge['type'] if bridge else None
