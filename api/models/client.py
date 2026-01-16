"""
Collective Memory Platform - Client Types

Client types represent the connecting platforms (Claude Code, Claude Desktop, etc.)
with persona affinities.
"""
from enum import Enum
from typing import Dict, List


class ClientType(str, Enum):
    """
    Client types for connecting AI platforms.

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


def get_client_types() -> List[Dict]:
    """
    Get all client types with their details and persona affinities.
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
    """
    return CLIENT_PERSONA_AFFINITIES.get(client, [])


def is_valid_client(client: str) -> bool:
    """
    Check if a client type is valid.
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
