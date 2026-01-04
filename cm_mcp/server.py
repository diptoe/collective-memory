"""
Collective Memory MCP Server

MCP server for Collective Memory knowledge graph platform.
Uses MCP Python SDK 1.1.1 with stdio transport for Claude Desktop.
"""

import asyncio
import sys
from mcp.server import Server
import mcp.types as types
import mcp.server.stdio

from .config import config

# Import all tool functions
from .tools import (
    # Entity tools
    search_entities,
    get_entity,
    create_entity,
    update_entity,
    search_entities_semantic,
    extract_entities_from_text,
    # Relationship tools
    list_relationships,
    create_relationship,
    # Context tools
    get_context,
    get_entity_context,
    # Persona tools
    list_personas,
    chat_with_persona,
    # Agent collaboration tools
    list_agents,
    get_my_identity,
    update_my_identity,
    # Message queue tools
    send_message,
    get_messages,
    mark_message_read,
)


# Server instructions for Claude
SERVER_INSTRUCTIONS = """
Collective Memory MCP Server - Knowledge Graph Integration

This MCP server provides access to the Collective Memory knowledge graph platform,
enabling you to search, create, and connect entities in a shared knowledge graph.

## Available Tools (18 total)

### ENTITY OPERATIONS (6 tools)
- search_entities: Keyword search by name or type
- search_entities_semantic: Natural language semantic search
- get_entity: Get detailed entity information
- create_entity: Create new entities (Person, Project, Technology, etc.)
- update_entity: Update entity properties or type
- extract_entities_from_text: NER extraction from text

### RELATIONSHIP OPERATIONS (2 tools)
- list_relationships: View connections between entities
- create_relationship: Link entities (WORKS_ON, KNOWS, USES, CREATED, etc.)

### CONTEXT/RAG OPERATIONS (2 tools)
- get_context: Get relevant context for a query (primary RAG tool)
- get_entity_context: Get all relationships around an entity

### AI PERSONA OPERATIONS (2 tools)
- list_personas: See available AI personas
- chat_with_persona: Chat with a specific persona (appears in Chat UI)

### AGENT COLLABORATION (3 tools)
- list_agents: See who else is collaborating
- get_my_identity: Check your current identity
- update_my_identity: Change your agent ID or persona

### MESSAGE QUEUE (3 tools) - Use for inter-agent communication
- send_message: Send messages to other agents/humans (appears in Messages UI)
- get_messages: Read messages from a channel
- mark_message_read: Mark a message as read

## Recommended Workflow
1. Check your identity: get_my_identity
2. Search before creating: search_entities or search_entities_semantic
3. Get context: get_context for background knowledge
4. Create and connect: create_entity, create_relationship
5. Switch roles as needed: update_my_identity

All operations are attributed to your agent identity.
"""


def get_server_instructions() -> str:
    """Generate server instructions with environment context"""
    env_info = f"\nENVIRONMENT: Connected to {config.environment_display} ({config.api_url})\n"
    return SERVER_INSTRUCTIONS + env_info


# Create server
server = Server(name=config.name)

# Session state - initialized with agent identity on startup
_session_state = {
    "agent_id": None,
    "agent_key": None,
    "persona": None,        # Persona role: backend-code, frontend-code, architect
    "persona_key": None,    # Resolved persona key from API
    "persona_name": None,   # Display name
    "registered": False,
}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        # ============================================================
        # ENTITY TOOLS - Create, search, and manage knowledge graph entities
        # ============================================================
        types.Tool(
            name="search_entities",
            description="""Search for entities in the knowledge graph by name or type.

USE THIS WHEN: You need to find existing entities before creating new ones, or explore what's in the knowledge graph.

EXAMPLES:
- Search by name: {"query": "React"}
- Search by type: {"entity_type": "Technology"}
- Combined: {"query": "dashboard", "entity_type": "Project"}

RETURNS: List of matching entities with keys, names, types, and properties.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query - matches entity names (partial match supported)"},
                    "entity_type": {"type": "string", "description": "Filter by type: Person, Project, Technology, Organization, Document, Concept, or any custom type"},
                    "limit": {"type": "integer", "description": "Maximum results to return (default 10)", "default": 10}
                }
            }
        ),
        types.Tool(
            name="get_entity",
            description="""Get detailed information about a specific entity by its key.

USE THIS WHEN: You have an entity_key and need full details including all properties and metadata.

EXAMPLE: {"entity_key": "ent-abc123"}

RETURNS: Complete entity data including name, type, properties, source attribution, and timestamps.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_key": {"type": "string", "description": "The unique entity key (e.g., 'ent-abc123')"}
                },
                "required": ["entity_key"]
            }
        ),
        types.Tool(
            name="create_entity",
            description="""Create a new entity in the knowledge graph. Your agent ID is automatically recorded as the source.

USE THIS WHEN: You've confirmed an entity doesn't already exist (use search_entities first!) and need to add new knowledge.

COMMON TYPES:
- Person: Team members, contacts, stakeholders
- Project: Products, initiatives, applications
- Technology: Languages, frameworks, tools, libraries
- Organization: Companies, teams, departments
- Document: Notes, specs, references
- Concept: Ideas, patterns, methodologies

EXAMPLES:
- {"name": "React Dashboard", "entity_type": "Project", "properties": {"status": "active", "tech_stack": ["React", "TypeScript"]}}
- {"name": "Sarah Chen", "entity_type": "Person", "properties": {"role": "Tech Lead", "team": "Platform"}}

RETURNS: The created entity with its assigned entity_key.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name - should be clear and unique"},
                    "entity_type": {"type": "string", "description": "Type: Person, Project, Technology, Organization, Document, Concept, or custom"},
                    "properties": {"type": "object", "description": "Additional properties as key-value pairs (flexible schema)"}
                },
                "required": ["name", "entity_type"]
            }
        ),
        types.Tool(
            name="update_entity",
            description="""Update an existing entity's name, type, or properties.

USE THIS WHEN: You need to correct, enrich, or modify existing entity data.

EXAMPLES:
- Update name: {"entity_key": "ent-abc123", "name": "React Dashboard v2"}
- Change type: {"entity_key": "ent-abc123", "entity_type": "Application"}
- Add properties: {"entity_key": "ent-abc123", "properties": {"status": "completed"}}

NOTE: Properties are merged, not replaced. To remove a property, set it to null.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_key": {"type": "string", "description": "The entity key to update"},
                    "name": {"type": "string", "description": "New name (optional)"},
                    "entity_type": {"type": "string", "description": "New type (optional)"},
                    "properties": {"type": "object", "description": "Properties to add/update (merged with existing)"}
                },
                "required": ["entity_key"]
            }
        ),
        types.Tool(
            name="search_entities_semantic",
            description="""Semantic search using natural language. Finds entities by meaning, not just keywords.

USE THIS WHEN: Keyword search isn't finding what you need, or you want conceptually related entities.

HOW IT WORKS: Converts your query to a vector embedding and finds entities with similar embeddings.

EXAMPLES:
- {"query": "tools for building user interfaces"} → finds React, Vue, Angular
- {"query": "people who work on authentication"} → finds team members related to auth
- {"query": "frontend frameworks"} → finds UI-related technologies

RETURNS: Entities ranked by semantic similarity with confidence scores.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language description of what you're looking for"},
                    "entity_type": {"type": "string", "description": "Optionally filter results by type"},
                    "limit": {"type": "integer", "description": "Maximum results (default 10)", "default": 10}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="extract_entities_from_text",
            description="""Extract named entities from text using NER (Named Entity Recognition).

USE THIS WHEN: Processing meeting notes, documentation, or any text that mentions people, companies, or technologies.

EXAMPLES:
- {"text": "Sarah from Acme Corp discussed the React migration with our team"}
  → Extracts: Sarah (Person), Acme Corp (Organization), React (Technology)

- {"text": "The new dashboard uses PostgreSQL and Redis", "auto_create": true}
  → Extracts AND creates entities for PostgreSQL and Redis

RETURNS: List of extracted entities with their types. If auto_create=true, also returns created entity keys.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze for entity mentions"},
                    "auto_create": {"type": "boolean", "description": "If true, automatically create entities that don't exist (default false)", "default": False}
                },
                "required": ["text"]
            }
        ),

        # ============================================================
        # RELATIONSHIP TOOLS - Connect entities in the knowledge graph
        # ============================================================
        types.Tool(
            name="list_relationships",
            description="""List relationships in the knowledge graph, optionally filtered by entity.

USE THIS WHEN: You want to understand how entities are connected, or explore the graph structure.

EXAMPLES:
- All relationships: {}
- For specific entity: {"entity_key": "ent-abc123"}

COMMON RELATIONSHIP TYPES:
- WORKS_ON: Person → Project
- KNOWS: Person → Person
- USES: Project/Person → Technology
- CREATED: Person/Agent → Any
- BELONGS_TO: Entity → Organization
- RELATED_TO: Generic relationship

RETURNS: Relationships with from/to entity keys, types, and properties.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_key": {"type": "string", "description": "Show only relationships involving this entity"},
                    "limit": {"type": "integer", "description": "Maximum results (default 20)", "default": 20}
                }
            }
        ),
        types.Tool(
            name="create_relationship",
            description="""Create a relationship between two entities. Your agent ID is recorded as the creator.

USE THIS WHEN: You discover a connection between entities that should be captured in the graph.

RELATIONSHIP TYPES:
- WORKS_ON: Person works on Project
- KNOWS: Person knows Person
- USES: Project/Person uses Technology
- CREATED: Person/Agent created Project/Document
- BELONGS_TO: Entity belongs to Organization
- RELATED_TO: General relationship (use when others don't fit)

EXAMPLES:
- {"from_entity_key": "ent-sarah", "to_entity_key": "ent-dashboard", "relationship_type": "WORKS_ON", "properties": {"role": "Tech Lead"}}
- {"from_entity_key": "ent-dashboard", "to_entity_key": "ent-react", "relationship_type": "USES"}

RETURNS: The created relationship with its assigned relationship_key.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_entity_key": {"type": "string", "description": "Source entity key (the 'from' side)"},
                    "to_entity_key": {"type": "string", "description": "Target entity key (the 'to' side)"},
                    "relationship_type": {"type": "string", "description": "WORKS_ON, KNOWS, USES, CREATED, BELONGS_TO, RELATED_TO, or custom"},
                    "properties": {"type": "object", "description": "Additional properties for the relationship"}
                },
                "required": ["from_entity_key", "to_entity_key", "relationship_type"]
            }
        ),

        # ============================================================
        # CONTEXT/RAG TOOLS - Get relevant context from the knowledge graph
        # ============================================================
        types.Tool(
            name="get_context",
            description="""Get relevant context from the knowledge graph for answering a question or completing a task.

USE THIS WHEN: You need background knowledge from the graph to inform your response. This is the primary RAG tool.

HOW IT WORKS: Searches for relevant entities and their relationships, returning a structured context package.

EXAMPLES:
- {"query": "What technologies does the dashboard project use?"}
- {"query": "Who is working on authentication?", "max_entities": 10}

RETURNS: Relevant entities, their relationships, and a formatted context summary.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The question or topic you need context for"},
                    "max_entities": {"type": "integer", "description": "Maximum entities to include (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_entity_context",
            description="""Get detailed context around a specific entity, including all its relationships.

USE THIS WHEN: You have a specific entity and want to understand its full context - what it's connected to.

EXAMPLES:
- {"entity_key": "ent-sarah"} → Sarah's projects, technologies, colleagues
- {"entity_key": "ent-dashboard", "depth": 2} → Dashboard's tech stack AND what uses those technologies

RETURNS: The entity, all related entities, and the relationships connecting them.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_key": {"type": "string", "description": "The entity to get context for"},
                    "depth": {"type": "integer", "description": "How many relationship hops to follow (1=direct, 2=includes neighbors' neighbors)", "default": 1}
                },
                "required": ["entity_key"]
            }
        ),

        # ============================================================
        # PERSONA TOOLS - Interact with AI personas
        # ============================================================
        types.Tool(
            name="list_personas",
            description="""List all available AI personas in the Collective Memory.

USE THIS WHEN: You want to see what AI personas are available and their specializations.

PERSONAS are specialized AI roles with distinct:
- System prompts and personalities
- Model configurations
- Domain expertise

RETURNS: All personas with their names, roles, models, and capabilities.""",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="chat_with_persona",
            description="""Send a message to a specific AI persona and get a response.

USE THIS WHEN: You want to consult with a specialized AI persona (e.g., ask the architect about system design).

EXAMPLES:
- {"persona_key": "per-architect", "message": "What's the best approach for scaling our auth system?"}
- {"persona_key": "per-backend", "message": "Review this API design", "conversation_key": "conv-123"}

RETURNS: The persona's response and conversation context.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "persona_key": {"type": "string", "description": "The persona to chat with (from list_personas)"},
                    "message": {"type": "string", "description": "Your message to the persona"},
                    "conversation_key": {"type": "string", "description": "Continue an existing conversation (omit to start new)"}
                },
                "required": ["persona_key", "message"]
            }
        ),

        # ============================================================
        # AGENT COLLABORATION TOOLS - Manage your identity and see collaborators
        # ============================================================
        types.Tool(
            name="list_agents",
            description="""List all AI agents connected to the Collective Memory.

USE THIS WHEN: You want to see who else is collaborating - other Claude instances, different personas, etc.

EXAMPLES:
- {"active_only": true} → Only agents with recent heartbeats
- {"active_only": false} → All registered agents

RETURNS: Agents with their IDs, roles, capabilities, and active status.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {"type": "boolean", "description": "Only show active agents (heartbeat within 15 min)", "default": True}
                }
            }
        ),
        types.Tool(
            name="get_my_identity",
            description="""Get your current identity in the Collective Memory.

USE THIS WHEN: You need to know your agent ID, persona, or confirm your registration status.

RETURNS: Your agent ID, agent key, persona details, and registration status.""",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="update_my_identity",
            description="""Change your agent identity - agent ID and/or persona.

USE THIS WHEN: You need to switch roles or personas during a session.

EXAMPLES:
- {"persona": "frontend-code"} → Switch to frontend persona
- {"agent_id": "claude-code-wayne-2", "persona": "architect"} → Change both
- {"persona": "consultant"} → Switch to consultant role

NOTE: Changing identity re-registers with the API. Your previous agent remains in the system.

RETURNS: Your new identity details after the change.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "New agent ID (optional - keeps current if not provided)"},
                    "persona": {"type": "string", "description": "New persona role: backend-code, frontend-code, architect, consultant, or custom"}
                }
            }
        ),

        # ============================================================
        # MESSAGE QUEUE TOOLS - Inter-agent and human communication
        # ============================================================
        types.Tool(
            name="send_message",
            description="""Send a message to other agents or human coordinators via the message queue.

USE THIS WHEN: You want to communicate with other agents or humans. Messages appear in the Messages UI, NOT the Chat UI.

Use this for:
- Status updates: "I've completed the API refactoring"
- Questions: "Which database should I use for caching?"
- Handoffs: "Frontend is ready, backend team please review"
- Announcements: "New feature deployed to staging"

EXAMPLES:
- {"channel": "general", "content": "Starting work on auth module", "message_type": "status"}
- {"channel": "backend", "content": "Need help with database schema", "message_type": "question", "priority": "high"}
- {"channel": "frontend", "to_agent": "claude-frontend", "content": "API endpoints are ready", "message_type": "handoff"}

RETURNS: Confirmation with message key.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Channel name: general, backend, frontend, urgent, or custom", "default": "general"},
                    "content": {"type": "string", "description": "Message content"},
                    "message_type": {"type": "string", "description": "Type: announcement, question, handoff, status, update", "default": "announcement"},
                    "to_agent": {"type": "string", "description": "Optional: specific agent ID (null for broadcast)"},
                    "priority": {"type": "string", "description": "Priority: high, normal, low", "default": "normal"}
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="get_messages",
            description="""Get messages from the message queue.

USE THIS WHEN: You want to check for messages from other agents or human coordinators.

EXAMPLES:
- {} → Get all unread messages
- {"channel": "backend"} → Messages from backend channel
- {"unread_only": false, "limit": 50} → Get recent messages including read ones

RETURNS: List of messages with sender, content, type, and read status.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Filter by channel (optional)"},
                    "unread_only": {"type": "boolean", "description": "Only unread messages", "default": True},
                    "limit": {"type": "integer", "description": "Maximum messages to retrieve", "default": 20}
                }
            }
        ),
        types.Tool(
            name="mark_message_read",
            description="""Mark a message as read.

USE THIS WHEN: You've processed a message and want to mark it as handled.

EXAMPLE: {"message_key": "msg-abc123"}

RETURNS: Confirmation.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_key": {"type": "string", "description": "The message key to mark as read"}
                },
                "required": ["message_key"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls by dispatching to appropriate tool functions"""

    # Entity tools
    if name == "search_entities":
        return await search_entities(arguments, config, _session_state)
    elif name == "get_entity":
        return await get_entity(arguments, config, _session_state)
    elif name == "create_entity":
        return await create_entity(arguments, config, _session_state)
    elif name == "update_entity":
        return await update_entity(arguments, config, _session_state)
    elif name == "search_entities_semantic":
        return await search_entities_semantic(arguments, config, _session_state)
    elif name == "extract_entities_from_text":
        return await extract_entities_from_text(arguments, config, _session_state)

    # Relationship tools
    elif name == "list_relationships":
        return await list_relationships(arguments, config, _session_state)
    elif name == "create_relationship":
        return await create_relationship(arguments, config, _session_state)

    # Context tools
    elif name == "get_context":
        return await get_context(arguments, config, _session_state)
    elif name == "get_entity_context":
        return await get_entity_context(arguments, config, _session_state)

    # Persona tools
    elif name == "list_personas":
        return await list_personas(arguments, config, _session_state)
    elif name == "chat_with_persona":
        return await chat_with_persona(arguments, config, _session_state)

    # Agent collaboration tools
    elif name == "list_agents":
        return await list_agents(arguments, config, _session_state)
    elif name == "get_my_identity":
        return await get_my_identity(arguments, config, _session_state)
    elif name == "update_my_identity":
        return await update_my_identity(arguments, config, _session_state)

    # Message queue tools
    elif name == "send_message":
        return await send_message(arguments, config, _session_state)
    elif name == "get_messages":
        return await get_messages(arguments, config, _session_state)
    elif name == "mark_message_read":
        return await mark_message_read(arguments, config, _session_state)

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def register_agent():
    """Register this agent with the Collective Memory API and resolve persona"""
    import httpx

    if not config.has_identity:
        return False

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            # Register the agent
            response = await client.post(
                f"{config.api_endpoint}/agents/register",
                json={
                    "agent_id": config.agent_id,
                    "role": config.persona,  # Use persona as role
                    "capabilities": config.capabilities_list,
                }
            )
            if response.status_code in (200, 201):
                data = response.json()
                if data.get("success"):
                    agent_data = data.get("data", {})
                    _session_state["agent_id"] = config.agent_id
                    _session_state["agent_key"] = agent_data.get("agent_key")
                    _session_state["persona"] = config.persona
                    _session_state["registered"] = True

            # Send initial heartbeat to mark as active
            if _session_state.get("registered"):
                await client.post(
                    f"{config.api_endpoint}/agents/{config.agent_id}/heartbeat"
                )
                print(f"  Initial heartbeat sent", file=sys.stderr)

            # Resolve persona details if configured
            if config.persona:
                personas_response = await client.get(
                    f"{config.api_endpoint}/personas",
                    params={"role": config.persona}
                )
                persona_found = False
                if personas_response.status_code == 200:
                    personas_data = personas_response.json()
                    personas = personas_data.get("data", {}).get("personas", [])
                    if personas:
                        persona = personas[0]
                        _session_state["persona_key"] = persona.get("persona_key")
                        _session_state["persona_name"] = persona.get("name")
                        persona_found = True

                # Auto-create persona if not found
                if not persona_found:
                    print(f"Persona '{config.persona}' not found, creating...", file=sys.stderr)
                    persona_data = await _create_persona(client)
                    if persona_data:
                        _session_state["persona_key"] = persona_data.get("persona_key")
                        _session_state["persona_name"] = persona_data.get("name")

            return _session_state["registered"]
    except Exception as e:
        print(f"Agent registration failed: {e}", file=sys.stderr)
        return False


async def _create_persona(client) -> dict | None:
    """Auto-create a persona from config environment variables"""
    # Build persona name from config or role
    name = config.persona_name or f"Auto-{config.persona.replace('-', ' ').title()}"
    model = config.persona_model or "claude-3-5-sonnet"

    persona_payload = {
        "name": name,
        "model": model,
        "role": config.persona,
        "color": config.persona_color,
        "system_prompt": f"You are an AI assistant acting as {name}.",
        "personality": {
            "traits": ["helpful", "knowledgeable"],
            "communication_style": "professional"
        },
        "capabilities": config.capabilities_list,
    }

    try:
        response = await client.post(
            f"{config.api_endpoint}/personas",
            json=persona_payload
        )
        if response.status_code in (200, 201):
            data = response.json()
            if data.get("success"):
                print(f"  Created persona: {name}", file=sys.stderr)
                return data.get("data", {})
        else:
            print(f"  Failed to create persona: {response.text}", file=sys.stderr)
    except Exception as e:
        print(f"  Error creating persona: {e}", file=sys.stderr)
    return None


async def startup_checks():
    """Perform startup checks and report status"""
    print("=" * 60, file=sys.stderr)
    print(f"Starting MCP Server: {config.server_name} v{config.version}", file=sys.stderr)
    print(f"Environment: {config.environment_display}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Configuration check
    print("\nConfiguration:", file=sys.stderr)
    print(f"  Server Name: {config.server_name}", file=sys.stderr)
    print(f"  API URL: {config.api_url}", file=sys.stderr)
    print(f"  API Endpoint: {config.api_endpoint}", file=sys.stderr)

    # Agent identity
    print("\nAgent Identity:", file=sys.stderr)
    if config.has_identity:
        print(f"  Agent ID: {config.agent_id}", file=sys.stderr)
        print(f"  Persona: {config.persona or '(not set)'}", file=sys.stderr)
        print(f"  Capabilities: {config.capabilities_list}", file=sys.stderr)
    else:
        print("  WARNING: No agent identity configured!", file=sys.stderr)
        print("  Set CM_AGENT_ID and CM_PERSONA for proper collaboration", file=sys.stderr)

    # Validate configuration
    is_valid, error_msg = config.validate()
    if not is_valid:
        print(f"\nConfiguration Error: {error_msg}", file=sys.stderr)
        print("Server will start but API calls may fail.", file=sys.stderr)

    # Register agent with API
    if config.has_identity:
        print("\nRegistering agent...", file=sys.stderr)
        registered = await register_agent()
        if registered:
            print(f"  Agent Key: {_session_state['agent_key']}", file=sys.stderr)
            if _session_state.get("persona_name"):
                print(f"  Acting as: {_session_state['persona_name']}", file=sys.stderr)
        else:
            print("  Registration failed - will retry on first API call", file=sys.stderr)

    # Display usage/instructions in startup logs (SDK 1.1.1 no longer accepts these in Server()).
    if config.debug:
        print("\nInstructions:", file=sys.stderr)
        print(get_server_instructions().strip(), file=sys.stderr)

    print("\n" + "=" * 60, file=sys.stderr)
    print("MCP Server ready - waiting for client connection...", file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)


# Heartbeat interval in seconds (5 minutes - API timeout is 15 minutes)
HEARTBEAT_INTERVAL = 300

# Flag to control heartbeat task
_heartbeat_running = False


async def send_heartbeat():
    """Send a heartbeat to keep the agent active"""
    import httpx

    agent_id = _session_state.get("agent_id")
    if not agent_id:
        return False

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.api_endpoint}/agents/{agent_id}/heartbeat"
            )
            if response.status_code == 200:
                if config.debug:
                    print(f"  Heartbeat sent for {agent_id}", file=sys.stderr)
                return True
            else:
                if config.debug:
                    print(f"  Heartbeat failed: {response.status_code}", file=sys.stderr)
                return False
    except Exception as e:
        if config.debug:
            print(f"  Heartbeat error: {e}", file=sys.stderr)
        return False


async def heartbeat_loop():
    """Background task that sends periodic heartbeats"""
    global _heartbeat_running
    _heartbeat_running = True

    # Wait for initial registration to complete
    await asyncio.sleep(5)

    while _heartbeat_running:
        if _session_state.get("registered"):
            await send_heartbeat()
        await asyncio.sleep(HEARTBEAT_INTERVAL)


async def main():
    """Main entry point"""
    global _heartbeat_running

    # Perform startup checks
    await startup_checks()

    # Start heartbeat background task
    heartbeat_task = None
    if config.has_identity:
        heartbeat_task = asyncio.create_task(heartbeat_loop())
        if config.debug:
            print("Heartbeat task started", file=sys.stderr)

    try:
        # Run server with stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        # Stop heartbeat task when server exits
        _heartbeat_running = False
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


def run():
    """Run the server"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if config.debug:
            print("Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {str(e)}", file=sys.stderr)
        if config.debug:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
