"""
Collective Memory Platform - Context Service

Provides optimized context retrieval from the knowledge graph for AI prompts.
Features in-memory caching, token limiting, and semantic search.
"""

import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Check if semantic search is available
try:
    from pgvector.sqlalchemy import Vector
    SEMANTIC_SEARCH_AVAILABLE = os.getenv("CM_ENABLE_PGVECTOR", "false").lower() in ("1", "true", "yes")
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False


@dataclass
class CacheEntry:
    """Cached context entry with TTL."""
    context: Dict[str, Any]
    created_at: datetime
    ttl_seconds: int = 300  # 5 minutes default

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)


@dataclass
class ContextResult:
    """Result from context retrieval."""
    context_text: str
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    token_count: int
    truncated: bool = False
    cache_hit: bool = False


class ContextService:
    """
    Service for retrieving and caching context from the knowledge graph.

    Provides optimized context for AI persona prompts with:
    - In-memory caching with configurable TTL
    - Token limiting to prevent context overflow
    - Entity and relationship retrieval
    - Semantic search (when pgvector is available)
    """

    def __init__(
        self,
        cache_ttl: int = 300,
        max_tokens: int = 3000,
        max_entities: int = 20,
        use_semantic_search: bool = True
    ):
        """
        Initialize context service.

        Args:
            cache_ttl: Cache time-to-live in seconds
            max_tokens: Maximum tokens for context (approximate)
            max_entities: Maximum entities to include
            use_semantic_search: Use semantic search when available
        """
        self.cache_ttl = cache_ttl
        self.max_tokens = max_tokens
        self.max_entities = max_entities
        self.use_semantic_search = use_semantic_search and SEMANTIC_SEARCH_AVAILABLE
        self._cache: Dict[str, CacheEntry] = {}
        self._embedding_service = None

    @property
    def embedding_service(self):
        """Lazy load embedding service."""
        if self._embedding_service is None:
            from api.services.embedding import embedding_service
            self._embedding_service = embedding_service
        return self._embedding_service

    def _get_cache_key(self, query: str, max_entities: int) -> str:
        """Generate cache key from query parameters."""
        key_data = f"{query}:{max_entities}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses simple word-based estimation (approximately 0.75 tokens per word).
        For production, use tiktoken or similar.
        """
        words = len(text.split())
        return int(words * 1.3)  # Rough estimate

    def _truncate_context(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        max_tokens: int
    ) -> tuple:
        """
        Truncate context to fit within token limit.

        Returns truncated entities, relationships, and truncated flag.
        """
        result_entities = []
        result_relationships = []
        current_tokens = 0
        truncated = False

        # Add entities first (most important)
        for entity in entities:
            entity_text = f"{entity.get('name', '')} ({entity.get('entity_type', '')})"
            entity_tokens = self._estimate_tokens(entity_text)

            if current_tokens + entity_tokens > max_tokens:
                truncated = True
                break

            result_entities.append(entity)
            current_tokens += entity_tokens

        # Add relationships if space remains
        for rel in relationships:
            rel_text = f"{rel.get('from_name', '')} -> {rel.get('to_name', '')}"
            rel_tokens = self._estimate_tokens(rel_text)

            if current_tokens + rel_tokens > max_tokens:
                truncated = True
                break

            result_relationships.append(rel)
            current_tokens += rel_tokens

        return result_entities, result_relationships, truncated, current_tokens

    def _format_context(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        documents: List[Dict[str, Any]] = None
    ) -> str:
        """Format entities, relationships, and documents as context text."""
        lines = []

        if entities:
            lines.append("## Known Entities")
            for entity in entities:
                name = entity.get('name', 'Unknown')
                etype = entity.get('entity_type', 'Unknown')
                props = entity.get('properties', {})

                line = f"- **{name}** ({etype})"
                if props:
                    prop_str = ", ".join(f"{k}: {v}" for k, v in list(props.items())[:3])
                    line += f": {prop_str}"
                lines.append(line)

        if relationships:
            lines.append("\n## Relationships")
            for rel in relationships:
                from_name = rel.get('from_name', 'Unknown')
                to_name = rel.get('to_name', 'Unknown')
                rel_type = rel.get('relationship_type', 'related_to')
                lines.append(f"- {from_name} → [{rel_type}] → {to_name}")

        if documents:
            lines.append("\n## Relevant Documents")
            for doc in documents:
                title = doc.get('title', 'Untitled')
                content = doc.get('content', '')
                # Truncate content for context
                if len(content) > 300:
                    content = content[:300] + "..."
                lines.append(f"### {title}")
                lines.append(content)
                lines.append("")

        return "\n".join(lines) if lines else "No relevant context found."

    def get_context(
        self,
        query: str,
        max_entities: Optional[int] = None,
        use_cache: bool = True,
        include_documents: bool = True
    ) -> ContextResult:
        """
        Get context for a query from the knowledge graph.

        Uses semantic search when available, falls back to keyword search.

        Args:
            query: The user's query text
            max_entities: Maximum entities to retrieve
            use_cache: Whether to use cached results
            include_documents: Include document results in context

        Returns:
            ContextResult with formatted context and metadata
        """
        from api.models import Entity, Relationship, Document

        max_entities = max_entities or self.max_entities

        # Check cache
        cache_key = self._get_cache_key(query, max_entities)
        if use_cache and cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for context query: {cache_key}")
                cached = entry.context
                return ContextResult(
                    context_text=cached['context_text'],
                    entities=cached['entities'],
                    relationships=cached['relationships'],
                    token_count=cached['token_count'],
                    truncated=cached['truncated'],
                    cache_hit=True
                )
            else:
                del self._cache[cache_key]

        entities = []
        documents = []

        # Try semantic search first if available
        if self.use_semantic_search:
            try:
                query_embedding = self.embedding_service.get_embedding(query)

                # Semantic entity search
                semantic_entities = Entity.search_semantic(
                    query_embedding,
                    limit=max_entities
                )
                for entity in semantic_entities:
                    entities.append({
                        'entity_key': entity.entity_key,
                        'name': entity.name,
                        'entity_type': entity.entity_type,
                        'properties': entity.properties or {}
                    })

                # Semantic document search
                if include_documents:
                    semantic_docs = Document.search_semantic(
                        query_embedding,
                        limit=3
                    )
                    for doc in semantic_docs:
                        documents.append({
                            'document_key': doc.document_key,
                            'title': doc.title,
                            'content': doc.content[:500] if doc.content else '',
                            'content_type': doc.content_type,
                        })

                logger.debug(f"Semantic search: {len(entities)} entities, {len(documents)} documents")

            except Exception as e:
                logger.warning(f"Semantic search failed, falling back to keyword: {e}")
                # Fall through to keyword search

        # Keyword search fallback
        if not entities:
            keywords = self._extract_keywords(query)
            for keyword in keywords[:5]:  # Limit keyword searches
                matches = Entity.search_by_name(keyword, limit=max_entities // 2)
                for entity in matches:
                    entity_dict = {
                        'entity_key': entity.entity_key,
                        'name': entity.name,
                        'entity_type': entity.entity_type,
                        'properties': entity.properties or {}
                    }
                    if entity_dict not in entities:
                        entities.append(entity_dict)

        # Get relationships for found entities
        relationships = []
        entity_keys = [e['entity_key'] for e in entities]
        if entity_keys:
            rels = Relationship.query.filter(
                (Relationship.from_entity_key.in_(entity_keys)) |
                (Relationship.to_entity_key.in_(entity_keys))
            ).limit(50).all()

            for rel in rels:
                rel_dict = {
                    'relationship_key': rel.relationship_key,
                    'from_entity_key': rel.from_entity_key,
                    'to_entity_key': rel.to_entity_key,
                    'relationship_type': rel.relationship_type,
                    'from_name': rel.from_entity.name if rel.from_entity else 'Unknown',
                    'to_name': rel.to_entity.name if rel.to_entity else 'Unknown',
                }
                relationships.append(rel_dict)

        # Truncate to token limit
        entities, relationships, truncated, token_count = self._truncate_context(
            entities[:max_entities],
            relationships,
            self.max_tokens
        )

        # Format context (include documents)
        context_text = self._format_context(entities, relationships, documents)

        result = ContextResult(
            context_text=context_text,
            entities=entities,
            relationships=relationships,
            token_count=token_count,
            truncated=truncated,
            cache_hit=False
        )

        # Cache result
        if use_cache:
            self._cache[cache_key] = CacheEntry(
                context={
                    'context_text': context_text,
                    'entities': entities,
                    'relationships': relationships,
                    'token_count': token_count,
                    'truncated': truncated,
                },
                created_at=datetime.utcnow(),
                ttl_seconds=self.cache_ttl
            )

        return result

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query.

        Simple implementation - splits on whitespace and filters stopwords.
        For production, use spaCy or similar NLP.
        """
        stopwords = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'what', 'which', 'who', 'whom',
            'this', 'that', 'these', 'those', 'am', 'about', 'if', 'or',
            'because', 'until', 'while', 'just', 'but', 'and', 'it', 'i',
            'me', 'my', 'you', 'your', 'he', 'she', 'him', 'her', 'we', 'they',
        }

        words = query.lower().split()
        keywords = [
            word.strip('.,!?;:()[]{}"\'-')
            for word in words
            if word.lower() not in stopwords and len(word) > 2
        ]
        return keywords

    def clear_cache(self) -> int:
        """Clear all cached entries. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.utcnow()
        expired = sum(1 for e in self._cache.values() if e.is_expired())
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired,
            'active_entries': len(self._cache) - expired,
        }


# Global service instance
context_service = ContextService()
