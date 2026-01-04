"""
Collective Memory Platform - Embedding Service

Provides OpenAI text-embedding-3-small embeddings with caching.
"""

import hashlib
import logging
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import openai

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCacheEntry:
    """Cached embedding with TTL."""
    embedding: List[float]
    created_at: datetime
    ttl_seconds: int = 3600  # 1 hour default

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)


class EmbeddingService:
    """
    OpenAI text-embedding-3-small service with caching.

    Provides:
    - Single text embedding generation
    - Batch embedding generation (more efficient)
    - In-memory caching to reduce API calls
    """

    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize embedding service.

        Args:
            cache_ttl: Cache time-to-live in seconds (default 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, EmbeddingCacheEntry] = {}
        self._client = None

    @property
    def client(self) -> openai.OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self._client = openai.OpenAI(api_key=api_key)
        return self._client

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode()).hexdigest()[:32]

    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Get embedding for a single text.

        Args:
            text: Text to embed
            use_cache: Whether to use cached results

        Returns:
            List of floats representing the embedding (1536 dimensions)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Check cache
        cache_key = self._get_cache_key(text)
        if use_cache and cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for embedding: {cache_key[:8]}...")
                return entry.embedding
            else:
                del self._cache[cache_key]

        # Generate embedding
        try:
            response = self.client.embeddings.create(
                model=self.MODEL,
                input=text,
                dimensions=self.DIMENSIONS
            )
            embedding = response.data[0].embedding

            # Cache result
            if use_cache:
                self._cache[cache_key] = EmbeddingCacheEntry(
                    embedding=embedding,
                    created_at=datetime.utcnow(),
                    ttl_seconds=self.cache_ttl
                )

            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def get_embeddings_batch(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Get embeddings for multiple texts in one API call.

        More efficient than calling get_embedding multiple times.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached results

        Returns:
            List of embeddings (each is a list of 1536 floats)
        """
        if not texts:
            return []

        results = [None] * len(texts)
        texts_to_embed = []
        text_indices = []

        # Check cache for each text
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} cannot be empty")

            cache_key = self._get_cache_key(text)
            if use_cache and cache_key in self._cache:
                entry = self._cache[cache_key]
                if not entry.is_expired():
                    results[i] = entry.embedding
                    continue
                else:
                    del self._cache[cache_key]

            texts_to_embed.append(text)
            text_indices.append(i)

        # Generate embeddings for uncached texts
        if texts_to_embed:
            try:
                response = self.client.embeddings.create(
                    model=self.MODEL,
                    input=texts_to_embed,
                    dimensions=self.DIMENSIONS
                )

                for j, embedding_data in enumerate(response.data):
                    original_index = text_indices[j]
                    embedding = embedding_data.embedding
                    results[original_index] = embedding

                    # Cache result
                    if use_cache:
                        cache_key = self._get_cache_key(texts_to_embed[j])
                        self._cache[cache_key] = EmbeddingCacheEntry(
                            embedding=embedding,
                            created_at=datetime.utcnow(),
                            ttl_seconds=self.cache_ttl
                        )

                logger.debug(f"Generated {len(texts_to_embed)} embeddings in batch")

            except Exception as e:
                logger.error(f"Error generating batch embeddings: {str(e)}")
                raise

        return results

    def clear_cache(self) -> int:
        """Clear all cached embeddings. Returns number of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        now = datetime.utcnow()
        expired = sum(1 for e in self._cache.values() if e.is_expired())
        return {
            'total_entries': len(self._cache),
            'expired_entries': expired,
            'active_entries': len(self._cache) - expired,
            'cache_ttl_seconds': self.cache_ttl,
        }


# Global service instance
embedding_service = EmbeddingService()
