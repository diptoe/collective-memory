"""
MCP Server Configuration

Configuration settings for the Collective Memory MCP server.

Each AI agent connecting to Collective Memory must have an identity
so that contributions can be attributed and collaboration tracked.

Supports two transport modes:
- stdio: Local process communication (default, for Claude Code, Cursor, etc.)
- sse: Server-Sent Events over HTTP (for remote/hosted deployments)
"""

import os
from typing import Optional, Literal
from dataclasses import dataclass


@dataclass
class MCPConfig:
    """MCP server configuration"""

    # Server metadata
    name: str = "collective-memory"
    version: str = "1.0.0"
    description: str = "MCP server for Collective Memory knowledge graph platform"

    # Transport configuration
    # stdio: Local process communication (default)
    # sse: Server-Sent Events over HTTP for remote access
    transport: Literal["stdio", "sse"] = os.getenv("CM_MCP_TRANSPORT", "stdio")  # type: ignore
    sse_host: str = os.getenv("CM_MCP_SSE_HOST", "0.0.0.0")
    sse_port: int = int(os.getenv("CM_MCP_SSE_PORT", "8080"))

    # Agent Identity (REQUIRED for collaboration)
    # Each AI instance should have a unique agent_id and link to a persona
    agent_id: str = os.getenv("CM_AGENT_ID", "")
    persona: str = os.getenv("CM_PERSONA", "")  # Persona role: backend-code, frontend-code, architect, consultant
    agent_capabilities: str = os.getenv("CM_AGENT_CAPABILITIES", "search,create,update")

    # Client identification - the connecting platform
    # Detected from environment or explicitly set
    client: str = os.getenv("CM_CLIENT", "")  # claude-code, claude-desktop, codex, gemini-cli, cursor

    # Model identification - the LLM being used
    model_key: str = os.getenv("CM_MODEL_KEY", "")  # Model key from DB, e.g., "mod-xxx"
    model_id: str = os.getenv("CM_MODEL_ID", "")  # Model API ID, e.g., "claude-opus-4-5-20251101"

    # Current work focus
    focus: str = os.getenv("CM_FOCUS", "")  # What the agent is working on

    # Persona details (optional - used to auto-create persona if it doesn't exist)
    persona_name: str = os.getenv("CM_PERSONA_NAME", "")  # Display name, e.g., "Claude Consultant"
    persona_color: str = os.getenv("CM_PERSONA_COLOR", "#6b7280")  # UI color

    # User authentication - Personal Access Token for linking to user account
    pat: str = os.getenv("CM_PAT", "")  # Personal Access Token for user authentication

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

    @property
    def is_sse(self) -> bool:
        """Check if SSE transport is configured"""
        return self.transport == "sse"

    @property
    def sse_url(self) -> str:
        """Get SSE server URL"""
        return f"http://{self.sse_host}:{self.sse_port}"

    @property
    def detected_client(self) -> str:
        """
        Auto-detect client from environment clues if not explicitly set.

        Detection order:
        1. Explicit CM_CLIENT environment variable
        2. CLAUDE_CODE environment variable → "claude-code"
        3. CLAUDE_DESKTOP indicator → "claude-desktop"
        4. CURSOR indicator (CURSOR_VERSION, etc.) → "cursor"
        5. MCP_CLIENT environment variable (if valid)
        6. CODEX_CLI/OPENAI_CODEX → "codex"
        7. GEMINI_API/GOOGLE_GEMINI → "gemini-cli"
        8. Empty string (client must be explicitly provided)

        Valid clients: claude-code, claude-desktop, codex, gemini-cli, cursor
        """
        valid_clients = {"claude-code", "claude-desktop", "codex", "gemini-cli", "cursor"}

        if self.client:
            return self.client if self.client in valid_clients else ""

        # Claude Code detection
        if os.getenv("CLAUDE_CODE"):
            return "claude-code"

        # Claude Desktop typically runs in a specific way
        if os.getenv("CLAUDE_DESKTOP") or os.getenv("__CLAUDE_MCP_ROOT__"):
            return "claude-desktop"

        # Cursor detection
        if os.getenv("CURSOR_VERSION") or os.getenv("CURSOR_TERMINAL"):
            return "cursor"

        # Generic MCP client environment variable (validate it)
        mcp_client = os.getenv("MCP_CLIENT")
        if mcp_client and mcp_client in valid_clients:
            return mcp_client

        # Check for Codex-specific env vars
        if os.getenv("CODEX_CLI") or os.getenv("OPENAI_CODEX"):
            return "codex"

        # Check for Gemini
        if os.getenv("GEMINI_API") or os.getenv("GOOGLE_GEMINI"):
            return "gemini-cli"

        return ""

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration

        Returns:
            Tuple of (is_valid, error_message_or_warning)

        Note: Missing agent_id is now valid - dynamic self-identification is supported.
        The AI can choose its own identity at runtime based on context.
        """
        if not self.api_url:
            return False, "CM_API_URL is required"
        if self.transport not in ("stdio", "sse"):
            return False, f"Invalid transport '{self.transport}' - must be 'stdio' or 'sse'"
        if self.is_sse and (self.sse_port < 1 or self.sse_port > 65535):
            return False, f"Invalid SSE port {self.sse_port} - must be between 1 and 65535"
        if not self.agent_id:
            # This is now a valid configuration - return warning, not error
            return True, "CM_AGENT_ID not set - dynamic self-identification enabled (AI will choose its own identity)"
        return True, None


# Global config instance
config = MCPConfig()
