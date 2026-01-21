"""
Collective Memory Platform - Client Model and Types

Client represents connecting platforms (Claude Code, Claude Desktop, Cursor, etc.)
with optional links to the knowledge graph and related Models/Personas.
"""
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from api.models.base import BaseModel, get_now

if TYPE_CHECKING:
    from api.models.model import Model
    from api.models.persona import Persona


class ClientType(str, Enum):
    """
    Client types for connecting AI platforms.

    DEPRECATED: Use Client model for new code. This enum is kept for backward compatibility.

    These represent the software/tool that connects to Collective Memory,
    not the AI model itself.
    """
    CLAUDE_CODE = "claude-code"        # Claude Code CLI
    CLAUDE_DESKTOP = "claude-desktop"  # Claude Desktop app
    CODEX = "codex"                    # OpenAI Codex
    GEMINI_CLI = "gemini-cli"          # Google Gemini CLI
    CURSOR = "cursor"                  # Cursor IDE


# Client → Persona Affinities
# These are soft suggestions, not hard restrictions
CLIENT_PERSONA_AFFINITIES: Dict[str, List[str]] = {
    ClientType.CLAUDE_DESKTOP.value: [
        'consultant',
        'ux-designer',
        'architect',
    ],
    ClientType.CLAUDE_CODE.value: [
        'frontend-code',
        'backend-code',
        'full-stack',
        'cm-developer',
    ],
    ClientType.CODEX.value: [
        'frontend-code',
        'backend-code',
        'full-stack',
        'cm-developer',
    ],
    ClientType.GEMINI_CLI.value: [
        'cloud-expert',
        'data-scientist',
        'architect',
        'cm-developer',
    ],
    ClientType.CURSOR.value: [
        'frontend-code',
        'backend-code',
        'full-stack',
        'cm-developer',
    ],
}


# Default clients to seed
DEFAULT_CLIENTS = [
    {
        'client_key': 'client-claude-code',
        'name': 'Claude Code',
        'description': "Anthropic's Claude Code CLI tool for terminal-based development",
        'publisher': 'Anthropic',
        'extra_data': {
            'suggested_personas': ['frontend-code', 'backend-code', 'full-stack', 'cm-developer'],
        }
    },
    {
        'client_key': 'client-claude-desktop',
        'name': 'Claude Desktop',
        'description': "Anthropic's Claude Desktop app and claude.ai web client for general AI assistance",
        'publisher': 'Anthropic',
        'extra_data': {
            'suggested_personas': ['consultant', 'ux-designer', 'architect'],
        }
    },
    {
        'client_key': 'client-cursor',
        'name': 'Cursor',
        'description': 'Cursor AI-powered IDE',
        'publisher': 'Cursor Inc',
        'extra_data': {
            'suggested_personas': ['frontend-code', 'backend-code', 'full-stack', 'cm-developer'],
        }
    },
    {
        'client_key': 'client-codex',
        'name': 'Codex',
        'description': "OpenAI's Codex platform for code generation and assistance",
        'publisher': 'OpenAI',
        'extra_data': {
            'suggested_personas': ['frontend-code', 'backend-code', 'full-stack', 'cm-developer'],
        }
    },
    {
        'client_key': 'client-gemini-cli',
        'name': 'Gemini CLI',
        'description': "Google's Gemini CLI tool for terminal-based development",
        'publisher': 'Google',
        'extra_data': {
            'suggested_personas': ['cloud-expert', 'data-scientist', 'architect', 'cm-developer'],
        }
    },
    {
        'client_key': 'client-vscode',
        'name': 'VS Code',
        'description': "Microsoft's Visual Studio Code with AI extensions",
        'publisher': 'Microsoft',
        'extra_data': {
            'suggested_personas': ['frontend-code', 'backend-code', 'full-stack'],
        }
    },
]


class Client(BaseModel):
    """
    Client model representing connecting platforms (Claude Code, Cursor, etc.)

    Clients can be linked to the knowledge graph via entity_key and have
    associated Models and Personas.
    """
    __tablename__ = 'clients'
    _schema_version = 1

    _default_fields = [
        'client_key', 'name', 'description', 'publisher',
        'entity_key', 'status', 'extra_data', 'created_at', 'updated_at'
    ]

    # Primary key - uses 'client-' prefix pattern
    client_key = Column(String(50), primary_key=True)

    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    publisher = Column(String(100), nullable=True)

    # Optional link to knowledge graph entity (system scope)
    entity_key = Column(String(50), nullable=True)

    # Status: active, deprecated
    status = Column(String(20), default='active', index=True)

    # Flexible extra data (icon_url, website, suggested_personas, etc.)
    extra_data = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)

    # Relationships - will be populated when Model and Persona add their FKs
    models = relationship('Model', back_populates='client', lazy='dynamic')
    personas = relationship('Persona', back_populates='client', lazy='dynamic')

    def to_dict(self, include_counts: bool = False) -> dict:
        """Convert to dictionary, optionally including model/persona counts."""
        data = super().to_dict()

        if include_counts:
            data['models_count'] = self.models.count() if self.models else 0
            data['personas_count'] = self.personas.count() if self.personas else 0

        return data

    @classmethod
    def get_by_key(cls, client_key: str) -> Optional['Client']:
        """Get a client by its key."""
        return cls.query.filter_by(client_key=client_key).first()

    @classmethod
    def get_active(cls) -> List['Client']:
        """Get all active clients."""
        return cls.query.filter_by(status='active').all()

    @classmethod
    def get_all(cls) -> List['Client']:
        """Get all clients."""
        return cls.query.all()

    def ensure_entity(self) -> Optional[str]:
        """
        Create or update a system-scoped Entity for this Client.
        Returns the entity_key if successful.
        """
        from api.models.entity import Entity

        # Use client_key as entity_key for strong link
        entity_key = self.client_key

        existing = Entity.query.filter_by(entity_key=entity_key).first()

        if existing:
            # Update existing entity
            existing.name = self.name
            existing.entity_type = 'Client'
            existing.description = self.description
            existing.scope_type = 'system'
            existing.scope_key = None
            existing.save()
        else:
            # Create new entity
            entity = Entity(
                entity_key=entity_key,
                name=self.name,
                entity_type='Client',
                description=self.description,
                scope_type='system',
                scope_key=None,
            )
            entity.save()

        # Update our entity_key reference
        if self.entity_key != entity_key:
            self.entity_key = entity_key
            self.save()

        return entity_key

    @classmethod
    def seed_defaults(cls) -> List['Client']:
        """
        Seed default clients if they don't exist.
        Returns list of created/existing clients.
        """
        clients = []

        for client_data in DEFAULT_CLIENTS:
            existing = cls.get_by_key(client_data['client_key'])
            if existing:
                clients.append(existing)
            else:
                client = cls(**client_data)
                client.save()
                clients.append(client)

        return clients

    @classmethod
    def map_client_type_to_key(cls, client_type: str) -> str:
        """
        Map a client type string (e.g., 'claude-code') to a client_key (e.g., 'client-claude-code').
        """
        if client_type.startswith('client-'):
            return client_type
        return f'client-{client_type}'

    def get_suggested_personas(self) -> List[str]:
        """Get suggested persona roles for this client."""
        if self.extra_data and 'suggested_personas' in self.extra_data:
            return self.extra_data['suggested_personas']
        return []


# Legacy helper functions (deprecated - use Client model methods instead)

def get_client_types() -> List[Dict]:
    """
    Get all client types with their details and persona affinities.

    DEPRECATED: Use Client.get_all() for database-backed clients.
    """
    return [
        {
            'value': ct.value,
            'name': ct.name.replace('_', ' ').title(),
            'description': _get_client_description(ct),
            'suggested_personas': CLIENT_PERSONA_AFFINITIES.get(ct.value, []),
        }
        for ct in ClientType
    ]


def get_client_affinities(client: str) -> List[str]:
    """
    Get suggested personas for a specific client type.

    DEPRECATED: Use Client.get_by_key(key).get_suggested_personas().
    """
    return CLIENT_PERSONA_AFFINITIES.get(client, [])


def is_valid_client(client: str) -> bool:
    """
    Check if a client type is valid.

    DEPRECATED: Use Client.get_by_key(key) is not None.
    """
    return client in [ct.value for ct in ClientType]


def _get_client_description(client_type: ClientType) -> str:
    """Get description for a client type."""
    descriptions = {
        ClientType.CLAUDE_CODE: "Anthropic's Claude Code CLI tool for terminal-based development",
        ClientType.CLAUDE_DESKTOP: "Anthropic's Claude Desktop app and claude.ai web client for general AI assistance",
        ClientType.CODEX: "OpenAI's Codex platform for code generation and assistance",
        ClientType.GEMINI_CLI: "Google's Gemini CLI tool for terminal-based development",
        ClientType.CURSOR: "Cursor AI-powered IDE",
    }
    return descriptions.get(client_type, "Unknown client type")
