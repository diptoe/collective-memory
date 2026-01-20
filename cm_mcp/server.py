"""
Collective Memory MCP Server

MCP server for Collective Memory knowledge graph platform.
Uses MCP Python SDK 1.1.1.

Supports two transport modes:
- stdio: Local process communication (default, for Claude Code, Cursor, etc.)
- sse: Server-Sent Events over HTTP (for remote/hosted deployments)
"""

import asyncio
import sys
from mcp.server import Server
import mcp.types as types
import mcp.server.stdio

from .config import config

# SSE transport imports (loaded conditionally)
try:
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import Response
    import uvicorn
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

# Import aggregated tool definitions and handlers
from .tools import TOOL_DEFINITIONS, TOOL_HANDLERS

# Import specific functions needed for heartbeat unread notice
from .tools import get_messages


# Server instructions for Claude
SERVER_INSTRUCTIONS = """
Collective Memory (CM) MCP Server - Knowledge Graph Integration

This MCP server provides access to the Collective Memory (CM) knowledge graph platform,
enabling you to search, create, and connect entities in a shared knowledge graph.

## MANDATORY: IDENTIFY YOURSELF AT SESSION START

**You MUST establish your identity before using other CM tools.**

Call `identify()` with ALL required fields:

```
identify(
    agent_id="claude-code-{project-name}",  # REQUIRED: Based on your working directory/task
    client="claude-code",                    # REQUIRED: You know what client you are!
    model_id="claude-opus-4-5-20251101",    # REQUIRED: You know your model ID!
    persona="backend-code",                  # Based on project type you're working on
    focus="What you're currently working on"
)
```

**REQUIRED - You know these things about yourself:**
- **client** (REQUIRED): claude-code, claude-desktop (includes claude.ai web), codex, gemini-cli, or cursor
- **model_id** (REQUIRED): Your model identifier (e.g., claude-opus-4-5-20251101, gpt-4, gemini-pro)
- **agent_id** (REQUIRED): Based on your project/task context

**Choose agent_id based on context:**
- Your working directory or project name
- The task you're working on
- Example: `claude-code-collective-memory-api`

**Choose persona based on project files:**
- Python/Flask/Django → `backend-code`
- React/Vue/TypeScript → `frontend-code`
- Mixed or architecture → `architect` or `full-stack`

## ONGOING: UPDATE YOUR FOCUS

When your work focus changes, update it:
```
update_focus(focus="Now working on X")
```

Periodically ask yourself: "Am I still focused on what I registered?"

## STAYING ACTIVE

Heartbeats are sent automatically whenever you use any CM tool. This keeps you visible
as an active collaborator. If you go 15 minutes without using CM tools, you'll appear offline.

To stay active during a long session:
- Use `get_messages()` to check for messages from other agents
- Use `list_agents()` to see who else is collaborating
- Use `update_focus()` when your task changes

## WORK SESSIONS & MILESTONES

Work sessions track focused work periods on a project. When you have an active session,
record milestones to track your progress.

**If identify() shows you have an active work session:**
- Record milestones as you work to create an audit trail
- Use `record_milestone(name="Starting X", status="started")` when beginning major tasks
- Use `record_milestone(name="X completed", status="completed")` when you finish tasks
- Use `record_milestone(name="Blocked on Y", status="blocked")` if you hit a blocker

**Milestone Status Values:**
- `started`: Beginning a significant task or feature
- `completed`: Finished a task (default if not specified)
- `blocked`: Hit a blocker that needs resolution

**Good milestones to record:**
- Starting/completing feature implementations
- Fixing bugs (reference issue numbers in properties)
- Completing code reviews
- Hitting and resolving blockers
- Making architectural decisions

**Example workflow during a session:**
```
record_milestone(name="Implementing user authentication", status="started")
# ... work on authentication ...
record_milestone(name="JWT auth with refresh tokens working", status="completed")
record_milestone(name="Waiting for OAuth credentials", status="blocked", properties={"blocker": "Need Google API keys"})
```

## Available Tools (45 total)

### IDENTITY & COLLABORATION (4 tools)
- identify: FIRST tool to call - shows options or registers you with CM
- list_agents: See who else is collaborating
- get_my_identity: Check your current identity
- update_my_identity: Change persona or register as new agent

### TEAM & SCOPE TOOLS (3 tools)
- list_my_scopes: See available scopes (domain, team, user) for entity visibility
- set_active_team: Set active team for this session (new entities default to team scope)
- list_teams: List teams you're a member of

### ENTITY OPERATIONS (6 tools)
- search_entities: Keyword search by name or type
- search_entities_semantic: Natural language semantic search
- get_entity: Get detailed entity information
- create_entity: Create new entities (Person, Project, Technology, etc.)
- update_entity: Update entity properties or type
- extract_entities_from_text: NER extraction from text

### RELATIONSHIP OPERATIONS (3 tools)
- list_relationships: View connections between entities
- create_relationship: Link entities (WORKS_ON, KNOWS, USES, CREATED, etc.)
- delete_relationship: Remove a relationship from the graph

### CONTEXT/RAG OPERATIONS (2 tools)
- get_context: Get relevant context for a query (primary RAG tool)
- get_entity_context: Get all relationships around an entity

### AI PERSONA OPERATIONS (2 tools)
- list_personas: See available AI personas
- chat_with_persona: Chat with a specific persona (appears in Chat UI)

### MODEL & CLIENT OPERATIONS (4 tools)
- list_models: See available AI models (Claude, GPT, Gemini)
- list_clients: See client types and persona affinities
- update_focus: Update your current work focus
- set_focused_mode: Enable fast heartbeats (30s) when waiting for replies

### MESSAGE QUEUE (5 tools) - Inter-agent communication
- send_message: Send messages to other agents/humans (appears in Messages UI)
- get_messages: Read messages from a channel
- mark_message_read: Mark a single message as read
- mark_all_messages_read: Clear all unread messages (with optional filters)
- link_message_entities: Link entities to an existing message

### GITHUB INTEGRATION (9 tools) - Repository analysis & work tracking
- sync_repository: Sync Repository entity with live GitHub data (stars, forks, issues)
- get_repo_issues: Fetch open/closed issues from a repository
- get_repo_commits: Get recent commits with co-author detection
- get_repo_contributors: List contributors with commit counts
- sync_repository_history: Full backfill of commits/issues as entities
- sync_repository_updates: Incremental sync since last sync (CALL AFTER COMMITS!)
- create_commit_entity: Create entity for a specific commit SHA
- create_issue_entity: Create entity for a specific issue number
- link_work_item: Link commits/issues to Ideas (IMPLEMENTS, TRACKS, RESOLVES)

### ACTIVITY MONITORING (2 tools) - Track system activity
- list_activities: View recent activities with filtering (by type, actor, time)
- get_activity_summary: Get aggregated activity counts by type

### WORK SESSIONS (5 tools) - Track focused work periods
- get_active_session: Check for an active work session
- start_session: Start a new work session for a project
- end_session: Close a work session with optional summary
- extend_session: Extend the auto-close timer
- record_milestone: Record progress milestones (started/completed/blocked)

## Recommended Workflow
1. Identify yourself: identify() to see options, then identify with your agent_id
2. Update focus: update_focus to let others know what you're working on
3. Search before creating: search_entities or search_entities_semantic
4. Get context: get_context for background knowledge
5. Create and connect: create_entity, create_relationship
6. Communicate: send_message to notify others of your progress

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
    "client": None,         # Client type: claude-code, claude-desktop, etc.
    "model_key": None,      # Model key from DB
    "model_id": None,       # Model API identifier (e.g., claude-opus-4-5-20251101)
    "model_name": None,     # Model display name
    "persona": None,        # Persona role: backend-code, frontend-code, architect
    "persona_key": None,    # Resolved persona key from API
    "persona_name": None,   # Display name
    "focus": None,          # Current work focus
    "affinity_warning": None,  # Warning if persona doesn't match client
    "registered": False,
    # Current milestone tracking (from heartbeat response)
    "current_milestone": None,  # {key, name, status, started_at}
    # Tool call counting for milestone metrics
    "tool_call_count": 0,               # Total tool calls this session
    "milestone_start_tool_count": 0,    # Tool count when milestone started
    # Work session activity tracking
    "active_session_key": None,         # Current active work session key
    "last_session_activity_update": None,  # Timestamp of last activity update
}


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools - returns all tool definitions from cm_mcp.tools"""
    return TOOL_DEFINITIONS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls by dispatching to appropriate tool functions"""

    # Increment tool call counter for milestone metrics
    _session_state["tool_call_count"] += 1

    # Tools that don't require registration (identity-related tools)
    identity_tools = ("identify", "get_my_identity")

    # Enforce registration for all other tools
    if name not in identity_tools and not _session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="## Registration Required\n\n"
                 "You must identify yourself before using CM tools.\n\n"
                 "**Call `identify` first** with your identity:\n\n"
                 "```\n"
                 "identify(\n"
                 '    agent_id="claude-code-{project}",  # Based on your project/task\n'
                 '    client="claude-code",              # Your client type\n'
                 '    model_id="your-model-id",          # Your model identifier\n'
                 '    persona="backend-code"             # Or frontend-code, architect, etc.\n'
                 ")\n"
                 "```\n\n"
                 "Or call `get_my_identity` to see available options and guidance."
        )]

    # Send heartbeat on every tool call (if registered) to keep agent active
    # Skip for identify/get_my_identity since they handle registration themselves
    # Skip for get_messages/mark_* since those are message-related
    unread_count = 0
    autonomous_count = 0
    message_tools = ("get_messages", "mark_message_read", "mark_all_messages_read", "send_message", "link_message_entities")
    if _session_state.get("registered") and name not in ("identify", "get_my_identity", *message_tools):
        try:
            unread_count, autonomous_count = await send_heartbeat()
        except Exception:
            pass  # Don't fail tool call if heartbeat fails

    # Update work session activity periodically to prevent auto-close
    # This slides the session expiration whenever we're actively using tools
    if _session_state.get("registered") and _session_state.get("active_session_key"):
        try:
            await update_session_activity()
        except Exception:
            pass  # Don't fail tool call if session update fails

    # Helper to append unread/autonomous notice to results with message preview
    async def maybe_append_unread_notice(result: list[types.TextContent]) -> list[types.TextContent]:
        if name in message_tools:
            return result
        if unread_count > 0 or autonomous_count > 0:
            # Fetch and preview unread messages so AI can act on them
            try:
                messages_result = await get_messages({"unread_only": True, "limit": 5}, config, _session_state)
                if messages_result and len(messages_result) > 0:
                    # Extract text content from the result
                    messages_text = messages_result[0].text if hasattr(messages_result[0], 'text') else str(messages_result[0])

                    if autonomous_count > 0:
                        notice = f"\n\n---\n🤖 **AUTONOMOUS TASK(S) - IMMEDIATE ACTION REQUIRED**\n\n"
                        notice += f"You have {autonomous_count} autonomous task(s) that require your immediate attention.\n"
                        notice += "**You MUST:**\n"
                        notice += "1. Read the task request below\n"
                        notice += "2. Acknowledge with `send_message(reply_to=\"msg-key\", message_type=\"acknowledged\", content=\"Starting...\")`\n"
                        notice += "3. Complete the work\n"
                        notice += "4. Reply when done with `send_message(reply_to=\"msg-key\", content=\"Done: ...\")`\n\n"
                    else:
                        notice = f"\n\n---\n📬 **UNREAD MESSAGES - PLEASE REVIEW**\n\n"
                        notice += f"You have {unread_count} unread message(s).\n"
                        notice += "**Action:** Review and respond to any that need your attention.\n"
                        notice += "Use `mark_message_read` for informational messages, or `send_message(reply_to=...)` to respond.\n\n"

                    notice += "**Messages:**\n"
                    notice += messages_text
                    notice += "\n\n---"
                    result.append(types.TextContent(type="text", text=notice))
            except Exception:
                # Fall back to simple notice if fetching fails
                if autonomous_count > 0:
                    notice = f"\n\n---\n🤖 **AUTONOMOUS TASK(S):** You have {autonomous_count} autonomous task(s) waiting. Use `get_messages` to see details and take action."
                else:
                    notice = f"\n\n---\n⚠️ **ACTION REQUIRED:** You have {unread_count} unread message(s). Use `get_messages` to check them."
                result.append(types.TextContent(type="text", text=notice))
        return result

    def maybe_append_milestone_reminder(result: list[types.TextContent]) -> list[types.TextContent]:
        """Append milestone reminder if agent has an active milestone."""
        # Don't show reminder for milestone-related tools
        milestone_tools = ["record_milestone", "record_interaction", "get_active_session", "start_session", "end_session", "extend_session"]
        if name in milestone_tools:
            return result

        milestone = _session_state.get("current_milestone")
        if milestone and milestone.get("status") == "started":
            # Calculate elapsed time if we have started_at
            elapsed_str = ""
            started_at = milestone.get("started_at")
            if started_at:
                try:
                    from datetime import datetime, timezone
                    # Parse ISO format timestamp
                    if started_at.endswith('Z'):
                        started_at = started_at.replace('Z', '+00:00')
                    start_dt = datetime.fromisoformat(started_at)
                    now = datetime.now(timezone.utc)
                    elapsed = now - start_dt
                    minutes = int(elapsed.total_seconds() // 60)
                    if minutes >= 60:
                        hours = minutes // 60
                        mins = minutes % 60
                        elapsed_str = f" ({hours}h {mins}m elapsed)"
                    elif minutes > 0:
                        elapsed_str = f" ({minutes}m elapsed)"
                except Exception:
                    pass  # Ignore timestamp parsing errors

            notice = f"\n\n---\n🎯 **CURRENT MILESTONE:** {milestone.get('name')}{elapsed_str}\n"
            notice += "Use `record_milestone` when you complete this task or hit a blocker."
            result.append(types.TextContent(type="text", text=notice))
        return result

    # Dispatch to tool handler using TOOL_HANDLERS lookup
    handler = TOOL_HANDLERS.get(name)
    if handler:
        result = await handler(arguments, config, _session_state)
    else:
        result = [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    # Append notices: first unread messages, then milestone reminder
    result = await maybe_append_unread_notice(result)
    result = maybe_append_milestone_reminder(result)
    return result


async def register_agent():
    """Register this agent with the Collective Memory API and resolve persona"""
    import httpx

    if not config.has_identity:
        return False

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as http_client:
            # Detect client type
            detected_client = config.detected_client
            _session_state["client"] = detected_client

            # Build registration payload with new fields
            registration_data = {
                "agent_id": config.agent_id,
                "capabilities": config.capabilities_list,
            }

            # Add client type
            if detected_client:
                registration_data["client"] = detected_client

            # Add model_key if configured
            if config.model_key:
                registration_data["model_key"] = config.model_key
                _session_state["model_key"] = config.model_key

            # Add focus if configured
            if config.focus:
                registration_data["focus"] = config.focus
                _session_state["focus"] = config.focus

            # Resolve persona to persona_key if configured
            persona_key = None
            if config.persona:
                try:
                    personas_response = await http_client.get(
                        f"{config.api_endpoint}/personas/by-role/{config.persona}"
                    )
                    if personas_response.status_code == 200:
                        personas_data = personas_response.json()
                        if personas_data.get("success"):
                            persona = personas_data.get("data", {})
                            persona_key = persona.get("persona_key")
                            _session_state["persona_key"] = persona_key
                            _session_state["persona_name"] = persona.get("name")
                except Exception:
                    pass  # Will try to create persona later

                if persona_key:
                    registration_data["persona_key"] = persona_key

            # Register the agent
            response = await http_client.post(
                f"{config.api_endpoint}/agents/register",
                json=registration_data
            )
            if response.status_code in (200, 201):
                data = response.json()
                if data.get("success"):
                    agent_data = data.get("data", {})
                    _session_state["agent_id"] = config.agent_id
                    _session_state["agent_key"] = agent_data.get("agent_key")
                    _session_state["persona"] = config.persona
                    _session_state["registered"] = True

                    # Store affinity warning if present
                    if agent_data.get("affinity_warning"):
                        _session_state["affinity_warning"] = agent_data.get("affinity_warning")
                        print(f"  Affinity notice: {agent_data.get('affinity_warning')}", file=sys.stderr)

            # Send initial heartbeat to mark as active
            if _session_state.get("registered"):
                await http_client.post(
                    f"{config.api_endpoint}/agents/{config.agent_id}/heartbeat"
                )
                print(f"  Initial heartbeat sent", file=sys.stderr)

            # If persona wasn't found earlier, try to create it
            if config.persona and not _session_state.get("persona_key"):
                print(f"Persona '{config.persona}' not found, creating...", file=sys.stderr)
                persona_data = await _create_persona(http_client)
                if persona_data:
                    _session_state["persona_key"] = persona_data.get("persona_key")
                    _session_state["persona_name"] = persona_data.get("name")

            return _session_state["registered"]
    except Exception as e:
        print(f"Agent registration failed: {e}", file=sys.stderr)
        return False


async def _create_persona(http_client) -> dict | None:
    """Auto-create a persona from config environment variables"""
    # Build persona name from config or role
    name = config.persona_name or f"Auto-{config.persona.replace('-', ' ').title()}"

    # Determine suggested clients based on detected client
    suggested_clients = []
    detected = config.detected_client
    if detected:
        suggested_clients = [detected]

    persona_payload = {
        "name": name,
        "role": config.persona,
        "color": config.persona_color,
        "system_prompt": f"You are an AI assistant acting as {name}.",
        "personality": {
            "traits": ["helpful", "knowledgeable"],
            "communication_style": "professional"
        },
        "capabilities": config.capabilities_list,
        "suggested_clients": suggested_clients,
    }

    try:
        response = await http_client.post(
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
    print(f"API: {config.api_url}", file=sys.stderr)
    print(f"Transport: {config.transport.upper()}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Configuration check
    print("\nConfiguration:", file=sys.stderr)
    print(f"  Server Name: {config.server_name}", file=sys.stderr)
    print(f"  Transport: {config.transport.upper()}", file=sys.stderr)
    if config.is_sse:
        print(f"  SSE URL: {config.sse_url}", file=sys.stderr)
        if not SSE_AVAILABLE:
            print("  WARNING: SSE dependencies not installed!", file=sys.stderr)
            print("           Run: pip install starlette uvicorn", file=sys.stderr)
    print(f"  API URL: {config.api_url}", file=sys.stderr)
    print(f"  API Endpoint: {config.api_endpoint}", file=sys.stderr)

    # Agent identity
    print("\nAgent Identity:", file=sys.stderr)
    if config.has_identity:
        print(f"  Agent ID: {config.agent_id}", file=sys.stderr)
        print(f"  Client: {config.detected_client}", file=sys.stderr)
        print(f"  Persona: {config.persona or '(not set)'}", file=sys.stderr)
        if config.model_key:
            print(f"  Model: {config.model_key}", file=sys.stderr)
        if config.focus:
            print(f"  Focus: {config.focus}", file=sys.stderr)
        print(f"  Capabilities: {config.capabilities_list}", file=sys.stderr)
    else:
        print("  Mode: Dynamic Self-Identification", file=sys.stderr)
        print(f"  Detected Client: {config.detected_client}", file=sys.stderr)
        print("  ", file=sys.stderr)
        print("  The AI will choose its own identity at runtime.", file=sys.stderr)
        print("  It should call get_my_identity() or identify() to:", file=sys.stderr)
        print("    1. See available personas and guidance", file=sys.stderr)
        print("    2. Create an agent_id based on context (project, task)", file=sys.stderr)
        print("    3. Register with identify(agent_id='...', persona='...')", file=sys.stderr)

    # Validate configuration
    is_valid, msg = config.validate()
    if not is_valid:
        print(f"\nConfiguration Error: {msg}", file=sys.stderr)
        print("Server will start but API calls may fail.", file=sys.stderr)
    elif msg:
        # Validation passed but has a message (e.g., dynamic identity mode)
        print(f"\nNote: {msg}", file=sys.stderr)

    # Register agent with API
    if config.has_identity:
        print("\nRegistering agent...", file=sys.stderr)
        registered = await register_agent()
        if registered:
            print(f"  Agent Key: {_session_state['agent_key']}", file=sys.stderr)
            print(f"  Client: {_session_state.get('client', 'unknown')}", file=sys.stderr)
            if _session_state.get("persona_name"):
                print(f"  Acting as: {_session_state['persona_name']}", file=sys.stderr)
            if _session_state.get("focus"):
                print(f"  Focus: {_session_state['focus']}", file=sys.stderr)
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


# Session activity update interval (10 minutes)
SESSION_ACTIVITY_INTERVAL = 600


async def update_session_activity() -> bool:
    """Update work session activity to prevent auto-close.

    Called periodically during tool usage to slide the session expiration.
    Returns True if update was sent, False otherwise.
    """
    import httpx
    from datetime import datetime, timezone

    session_key = _session_state.get("active_session_key")
    if not session_key:
        return False

    # Check if enough time has passed since last update
    last_update = _session_state.get("last_session_activity_update")
    now = datetime.now(timezone.utc)

    if last_update:
        elapsed = (now - last_update).total_seconds()
        if elapsed < SESSION_ACTIVITY_INTERVAL:
            return False  # Not enough time passed

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.api_endpoint}/work-sessions/{session_key}/activity"
            )
            if response.status_code == 200:
                _session_state["last_session_activity_update"] = now
                if config.debug:
                    print(f"  Session activity updated for {session_key}", file=sys.stderr)
                return True
            else:
                # Session might have been closed/expired
                if response.status_code == 404 or response.status_code == 400:
                    _session_state["active_session_key"] = None
                if config.debug:
                    print(f"  Session activity update failed: {response.status_code}", file=sys.stderr)
                return False
    except Exception as e:
        if config.debug:
            print(f"  Session activity update error: {e}", file=sys.stderr)
        return False


async def send_heartbeat() -> tuple[int, int]:
    """Send a heartbeat to keep the agent active.

    Returns tuple of (unread_messages, autonomous_tasks) counts.
    """
    import httpx

    agent_id = _session_state.get("agent_id")
    if not agent_id:
        return 0, 0

    try:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.api_endpoint}/agents/{agent_id}/heartbeat"
            )
            if response.status_code == 200:
                data = response.json()
                agent_data = data.get("data", {})
                unread = agent_data.get("unread_messages", 0)
                autonomous = agent_data.get("autonomous_tasks", 0)
                _session_state["unread_messages"] = unread
                _session_state["autonomous_tasks"] = autonomous

                # Capture current milestone from heartbeat response
                milestone = agent_data.get("current_milestone")
                _session_state["current_milestone"] = milestone

                if config.debug:
                    print(f"  Heartbeat sent for {agent_id}", file=sys.stderr)
                if autonomous > 0:
                    print(f"  🤖 AUTONOMOUS TASK(S): {autonomous} task(s) require your attention - work on them and reply!", file=sys.stderr)
                elif unread > 0:
                    print(f"  ⚠️  You have {unread} unread message(s) - use get_messages to check them", file=sys.stderr)
                if milestone and milestone.get("status") == "started":
                    print(f"  🎯 CURRENT MILESTONE: {milestone.get('name')}", file=sys.stderr)

                return unread, autonomous
            else:
                if config.debug:
                    print(f"  Heartbeat failed: {response.status_code}", file=sys.stderr)
                return 0, 0
    except Exception as e:
        if config.debug:
            print(f"  Heartbeat error: {e}", file=sys.stderr)
        return 0, 0


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


async def main_stdio():
    """Run server with stdio transport (for local AI clients)"""
    global _heartbeat_running

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


def create_sse_app():
    """Create Starlette ASGI app for SSE transport"""
    if not SSE_AVAILABLE:
        raise RuntimeError("SSE dependencies not installed. Run: pip install starlette uvicorn")

    # Create SSE transport
    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        """Handle SSE connections"""
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options()
            )
        return Response()

    async def handle_messages(request):
        """Handle POST messages for SSE"""
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )
        return Response()

    async def health_check(request):
        """Health check endpoint"""
        return Response(
            content='{"status":"healthy","server":"collective-memory-mcp"}',
            media_type="application/json"
        )

    # Create Starlette app with routes
    app = Starlette(
        debug=config.debug,
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Route("/sse", handle_sse, methods=["GET"]),
            Route("/messages/", handle_messages, methods=["POST"]),
        ],
    )

    return app


async def main():
    """Main entry point"""
    # Perform startup checks
    await startup_checks()

    if config.is_sse:
        # SSE transport mode
        if not SSE_AVAILABLE:
            print("ERROR: SSE dependencies not installed!", file=sys.stderr)
            print("Run: pip install starlette uvicorn", file=sys.stderr)
            sys.exit(1)

        print(f"\nStarting SSE server on {config.sse_url}", file=sys.stderr)
        print(f"SSE endpoint: {config.sse_url}/sse", file=sys.stderr)
        print(f"Messages endpoint: {config.sse_url}/messages/", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)

        # Create and run the SSE app
        app = create_sse_app()
        uvicorn_config = uvicorn.Config(
            app,
            host=config.sse_host,
            port=config.sse_port,
            log_level="info" if config.debug else "warning",
        )
        uvicorn_server = uvicorn.Server(uvicorn_config)
        await uvicorn_server.serve()
    else:
        # stdio transport mode (default)
        await main_stdio()


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
