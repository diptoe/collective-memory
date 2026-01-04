"""
MCP Server Configuration

Configuration settings for the Collective Memory MCP server.

Each AI agent connecting to Collective Memory must have an identity
so that contributions can be attributed and collaboration tracked.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class MCPConfig:
    """MCP server configuration"""

    # Server metadata
    name: str = "collective-memory"
    version: str = "1.0.0"
    description: str = "MCP server for Collective Memory knowledge graph platform"

    # Agent Identity (REQUIRED for collaboration)
    # Each AI instance should have a unique agent_id and link to a persona
    agent_id: str = os.getenv("CM_AGENT_ID", "")
    persona: str = os.getenv("CM_PERSONA", "")  # Persona role: backend-code, frontend-code, architect, consultant
    agent_capabilities: str = os.getenv("CM_AGENT_CAPABILITIES", "search,create,update")

    # Persona details (optional - used to auto-create persona if it doesn't exist)
    persona_name: str = os.getenv("CM_PERSONA_NAME", "")  # Display name, e.g., "Claude Consultant"
    persona_model: str = os.getenv("CM_PERSONA_MODEL", "")  # Model ID, e.g., "claude-opus-4-5"
    persona_color: str = os.getenv("CM_PERSONA_COLOR", "#6b7280")  # UI color

    # API configuration
    api_url: str = os.getenv("CM_API_URL", "http://localhost:5001")
    api_base_path: str = "/api"

    # Server settings
    timeout: int = int(os.getenv("CM_MCP_TIMEOUT", "30"))
    debug: bool = os.getenv("CM_MCP_DEBUG", "false").lower() == "true"

    @property
    def api_endpoint(self) -> str:
        """Get full API endpoint URL"""
        return f"{self.api_url}{self.api_base_path}"

    @property
    def server_name(self) -> str:
        """Get server name"""
        if "localhost" in self.api_url or "127.0.0.1" in self.api_url:
            return f"{self.name}-local"
        return self.name

    @property
    def environment_display(self) -> str:
        """Get human-readable environment name"""
        if "localhost" in self.api_url or "127.0.0.1" in self.api_url:
            return "Local Development"
        return "Production"

    @property
    def capabilities_list(self) -> list[str]:
        """Get capabilities as a list"""
        return [c.strip() for c in self.agent_capabilities.split(",") if c.strip()]

    @property
    def has_identity(self) -> bool:
        """Check if agent identity is configured"""
        return bool(self.agent_id)

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.api_url:
            return False, "CM_API_URL is required"
        if not self.agent_id:
            return False, "CM_AGENT_ID is required - each AI needs a unique identity for collaboration"
        return True, None


# Global config instance
config = MCPConfig()
