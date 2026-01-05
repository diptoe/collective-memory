"""
Collective Memory Platform - Services

Business logic services for AI chat, context retrieval, embeddings, NER, checkpointing, and seeding.
"""

from .context import ContextService, context_service
from .chat import ChatService, chat_service
from .checkpoint import CheckpointService, checkpoint_service
from .embedding import EmbeddingService, embedding_service
from .ner import NERService, ner_service
from .document_processor import DocumentProcessor, document_processor
from .seeding import SeedingService, seeding_service, seed_all
from .github import GitHubService, get_github_service, github_service
from .activity import ActivityService, activity_service

__all__ = [
    'ContextService',
    'context_service',
    'ChatService',
    'chat_service',
    'CheckpointService',
    'checkpoint_service',
    'EmbeddingService',
    'embedding_service',
    'NERService',
    'ner_service',
    'DocumentProcessor',
    'document_processor',
    'SeedingService',
    'seeding_service',
    'seed_all',
    'GitHubService',
    'get_github_service',
    'github_service',
    'ActivityService',
    'activity_service',
]
