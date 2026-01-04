"""
Collective Memory Platform - Document Model

Documents with vector embeddings for semantic search.
"""

import os
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

from api.models.base import BaseModel, db, get_key, get_now

# Enable pgvector-backed VECTOR columns only when the DB extension is available.
# This avoids crashing on startup with: `type "vector" does not exist`
PGVECTOR_ENABLED = (
    PGVECTOR_AVAILABLE
    and os.getenv("CM_ENABLE_PGVECTOR", "false").lower() in ("1", "true", "yes")
)


class Document(BaseModel):
    """
    Document with vector embedding for semantic search.

    Used for storing markdown/text documents in the knowledge graph
    with associated embeddings for semantic retrieval.
    """
    __tablename__ = 'documents'

    document_key = Column(String(36), primary_key=True, default=get_key)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='markdown')

    # Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    if PGVECTOR_ENABLED:
        embedding = Column(Vector(1536), nullable=True)
    else:
        embedding = Column(Text, nullable=True)  # Fallback for dev / DB without pgvector extension

    # Metadata
    # NOTE: "metadata" is reserved by SQLAlchemy's Declarative API, so we use a different
    # Python attribute name while keeping the database column name as "metadata".
    extra_data = Column("metadata", JSONB, default=dict)
    source = Column(String(255), nullable=True)

    # Optional link to an entity
    entity_key = Column(String(36), ForeignKey('entities.entity_key'), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Relationships
    entity = relationship('Entity', backref='documents')

    # Indexes
    __table_args__ = (
        Index('ix_documents_title', 'title'),
        Index('ix_documents_content_type', 'content_type'),
        Index('ix_documents_entity_key', 'entity_key'),
    )

    _default_fields = ['document_key', 'title', 'content_type', 'extra_data', 'entity_key']
    _readonly_fields = ['document_key', 'created_at']

    @classmethod
    def current_schema_version(cls) -> int:
        return 1

    @classmethod
    def search_by_title(cls, query: str, limit: int = 20) -> list['Document']:
        """Search documents by title (case-insensitive contains)."""
        return cls.query.filter(
            cls.title.ilike(f'%{query}%')
        ).limit(limit).all()

    @classmethod
    def search_semantic(
        cls,
        query_embedding: list,
        limit: int = 10,
        content_type: str = None,
        threshold: float = None
    ) -> list['Document']:
        """
        Semantic similarity search using cosine distance.

        Args:
            query_embedding: Query embedding vector (1536 dimensions)
            limit: Maximum results
            content_type: Filter by content type
            threshold: Optional similarity threshold (0-1, higher is more similar)

        Returns:
            List of documents ordered by similarity
        """
        if not PGVECTOR_ENABLED:
            raise RuntimeError(
                "pgvector semantic search disabled. "
                "Enable with CM_ENABLE_PGVECTOR=true and ensure the Postgres pgvector extension is installed."
            )

        query = cls.query.filter(cls.embedding.isnot(None))

        if content_type:
            query = query.filter(cls.content_type == content_type)

        # Order by cosine distance (smaller = more similar)
        query = query.order_by(
            cls.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        return query.all()

    @classmethod
    def get_by_entity(cls, entity_key: str, limit: int = 50) -> list['Document']:
        """Get all documents linked to an entity."""
        return cls.query.filter_by(entity_key=entity_key).limit(limit).all()

    def to_dict(self, include_content: bool = True, include_embedding: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_content: Include full content (can be large)
            include_embedding: Include embedding vector (usually not needed)
        """
        result = {
            'document_key': self.document_key,
            'title': self.title,
            'content_type': self.content_type,
            'metadata': self.extra_data,
            'source': self.source,
            'entity_key': self.entity_key,
            'has_embedding': self.embedding is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_content:
            result['content'] = self.content
            result['content_length'] = len(self.content) if self.content else 0

        if include_embedding and self.embedding is not None:
            result['embedding'] = list(self.embedding) if hasattr(self.embedding, '__iter__') else None

        return result

    def set_embedding(self, embedding: list) -> None:
        """
        Set the embedding vector.

        Args:
            embedding: List of floats (1536 dimensions)
        """
        if len(embedding) != 1536:
            raise ValueError(f"Embedding must be 1536 dimensions, got {len(embedding)}")
        self.embedding = embedding

    def generate_embedding(self, embedding_service=None) -> list:
        """
        Generate and set embedding from content.

        Args:
            embedding_service: Optional EmbeddingService instance

        Returns:
            The generated embedding
        """
        if embedding_service is None:
            from api.services import embedding_service

        # Combine title and content for embedding
        text = f"{self.title}\n\n{self.content}"
        embedding = embedding_service.get_embedding(text)
        self.set_embedding(embedding)
        return embedding
