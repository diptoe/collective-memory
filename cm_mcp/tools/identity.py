"""
Identity Tools

MCP tools for agent identity management in the Collective Memory (CM) knowledge graph.
"""

import mcp.types as types
import subprocess
import re
from typing import Any

from .utils import _make_request, get_session_pat, is_guest_session, reject_guest_write


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="identify",
        description="""Identify yourself to Collective Memory (CM). This is the FIRST tool you should call.

USE THIS WHEN: You're connecting to CM for the first time or want to see available options.

BEHAVIOR:
- Called WITHOUT parameters: Shows guidance for dynamic self-identification, available personas, clients, and models
- Called WITH parameters: Registers you with CM using the provided identity

REQUIRED FIELDS when registering:
- agent_id: Your unique identifier based on project/task context
- client: You KNOW this! Are you claude-code, claude-desktop, codex, or gemini-cli?
- model_id: You KNOW this! Your model identifier (e.g., claude-opus-4-5-20251101)

EXAMPLES:
- {} → Show dynamic identity guidance with all options
- {"agent_id": "claude-code-myproject", "client": "claude-code", "model_id": "claude-opus-4-5-20251101", "persona": "backend-code"} → Full registration

RETURNS: Either the identity guidance (options) or confirmation of registration.""",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "REQUIRED: Your unique agent ID (e.g., 'claude-code-collective-memory')"},
                "client": {"type": "string", "description": "REQUIRED: Client type - you know this! claude-code, claude-desktop (includes claude.ai), codex, gemini-cli, cursor"},
                "model_id": {"type": "string", "description": "REQUIRED: Your model identifier - you know this! (e.g., 'claude-opus-4-5-20251101')"},
                "persona": {"type": "string", "description": "Persona role: backend-code, frontend-code, architect, consultant, etc."},
                "model_key": {"type": "string", "description": "Model key from database (alternative to model_id)"},
                "focus": {"type": "string", "description": "What you're currently working on - describe your task"},
                "team_key": {"type": "string", "description": "Explicit team key to set as active (optional - auto-detected from agent_id if not provided)"},
                "team_slug": {"type": "string", "description": "Team slug to set as active (optional - resolved to team_key)"},
                "project_key": {"type": "string", "description": "Explicit project key to link to (optional - auto-detected from git remote or directory name)"}
            }
        }
    ),
    types.Tool(
        name="get_my_identity",
        description="""Get your current identity in Collective Memory (CM).

USE THIS WHEN: You need to know your agent ID, persona, or confirm your registration status.

IF NOT REGISTERED: Shows guidance for dynamic self-identification, including:
- How to choose an agent_id based on context (project, task, hostname)
- Available personas and which to choose based on project type
- Instructions for registering with the identify tool

RETURNS: Your agent ID, agent key, persona details, and registration status (or identity guidance if not registered).""",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="update_my_identity",
        description="""Change your identity in Collective Memory (CM).

USE THIS WHEN: You need to switch personas, change your focus, or register under a NEW agent_id.

IMPORTANT: Changing agent_id creates a NEW agent registration. The old agent remains in the system.
For claude-code users running multiple terminals, use different agent_ids for each (e.g., cc-wayne-1, cc-wayne-2).

EXAMPLES:
- {"persona": "frontend-code"} → Switch to frontend persona (same agent)
- {"agent_id": "cc-wayne-2", "persona": "architect"} → Register as NEW agent
- {"focus": "Working on auth module"} → Update focus only

RETURNS: Your new identity details after the change.""",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "New agent ID (creates NEW agent if different from current)"},
                "persona": {"type": "string", "description": "New persona role: backend-code, frontend-code, architect, consultant, or custom"},
                "model_key": {"type": "string", "description": "New model key (from list_models)"},
                "focus": {"type": "string", "description": "Current work focus"}
            }
        }
    ),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def _detect_project_from_api(config: Any, session_state: dict, repo_url: str) -> dict | None:
    """
    Query API to find project by repository URL.

    Uses the new /repositories/lookup endpoint which returns:
    - repository: The Repository record (if found)
    - projects: Array of Project records linked to this repository (with teams)

    Returns dict with project and teams info if found, None otherwise.
    For backwards compatibility, returns structure similar to old /projects/lookup.
    """
    try:
        from urllib.parse import quote
        encoded_url = quote(repo_url, safe='')
        result = await _make_request(
            config,
            "GET",
            f"/repositories/lookup?url={encoded_url}",
        )
        if result.get('success'):
            data = result.get('data', {})
            repository = data.get('repository')
            projects = data.get('projects', [])

            if repository:
                # Store repository info in session_state
                session_state['repository_key'] = repository.get('repository_key')
                session_state['repository_url'] = repository.get('repository_url')

                # Return first project if available (most common case)
                if projects:
                    # Projects already include teams from the lookup endpoint
                    first_project = projects[0]
                    return {
                        'project': first_project,
                        'teams': first_project.get('teams', []),
                        'repository': repository,
                        'all_projects': projects  # Include all in case caller needs them
                    }
                else:
                    # Repository exists but no projects linked
                    return {
                        'project': None,
                        'teams': [],
                        'repository': repository,
                        'all_projects': []
                    }
        return None
    except Exception:
        return None


def _detect_project_from_git() -> dict | None:
    """
    Detect project from git remote URL.

    Returns dict with owner, repo, url if detected, None otherwise.
    """
    try:
        # Run git remote get-url origin
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        url = result.stdout.strip()
        if not url:
            return None

        # Parse GitHub URL formats:
        # HTTPS: https://github.com/owner/repo.git or https://github.com/owner/repo
        # SSH: git@github.com:owner/repo.git or git@github.com:owner/repo

        # HTTPS format
        https_match = re.match(r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$', url)
        if https_match:
            return {
                'owner': https_match.group(1),
                'repo': https_match.group(2),
                'url': url,
            }

        # SSH format
        ssh_match = re.match(r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$', url)
        if ssh_match:
            return {
                'owner': ssh_match.group(1),
                'repo': ssh_match.group(2),
                'url': url,
            }

        return None

    except Exception:
        return None


def _get_working_directory_name() -> str | None:
    """
    Get the current working directory name.

    Returns the folder name (not full path), or None if unable to determine.
    """
    try:
        import os
        cwd = os.getcwd()
        return os.path.basename(cwd)
    except Exception:
        return None


async def _fetch_user_projects(config: Any) -> list:
    """
    Fetch projects accessible to the authenticated user (via their team memberships).

    Returns a list of project dicts with project_key, name, repository_name, etc.
    """
    try:
        result = await _make_request(
            config,
            "GET",
            "/projects",
            params={"include_teams": "true"}
        )
        if result.get("success"):
            return result.get("data", {}).get("projects", [])
        return []
    except Exception:
        return []


def _match_directory_to_project(dir_name: str, projects: list) -> dict | None:
    """
    Try to match a directory name to a project.

    Matching strategy (in order of confidence):
    1. Exact match on repository_name (case-insensitive)
    2. Exact match on project name (case-insensitive)
    3. Normalized match (replace - with _, etc.)

    Returns the matched project dict or None if no confident match.
    """
    if not dir_name or not projects:
        return None

    dir_lower = dir_name.lower()
    dir_normalized = dir_lower.replace('-', '_').replace(' ', '_')

    # First pass: exact match on repository_name
    for project in projects:
        repo_name = project.get('repository_name', '')
        if repo_name and repo_name.lower() == dir_lower:
            return project

    # Second pass: exact match on project name
    for project in projects:
        name = project.get('name', '')
        if name and name.lower() == dir_lower:
            return project

    # Third pass: normalized match on repository_name
    for project in projects:
        repo_name = project.get('repository_name', '')
        if repo_name:
            repo_normalized = repo_name.lower().replace('-', '_').replace(' ', '_')
            if repo_normalized == dir_normalized:
                return project

    # Fourth pass: normalized match on project name
    for project in projects:
        name = project.get('name', '')
        if name:
            name_normalized = name.lower().replace('-', '_').replace(' ', '_')
            if name_normalized == dir_normalized:
                return project

    return None


def _format_project_selection_prompt(projects: list, dir_name: str | None = None) -> str:
    """
    Format a prompt asking the user to select a project.

    Returns formatted text with project list and instructions.
    """
    output = "## Project Selection\n\n"

    if dir_name:
        output += f"Could not automatically match directory `{dir_name}` to a project.\n\n"
    else:
        output += "No git remote detected and unable to determine project from directory.\n\n"

    if not projects:
        output += "No projects available. Ask a domain admin to create a project and add your team to it.\n"
        return output

    output += "**Available projects from your teams:**\n\n"
    output += "| # | Project | Repository | Teams |\n"
    output += "|---|---------|------------|-------|\n"

    for i, project in enumerate(projects[:10], 1):
        name = project.get('name', 'Unknown')
        repo = project.get('repository_name') or '-'
        teams = project.get('teams', [])
        team_names = ', '.join([t.get('team', {}).get('name', t.get('team_key', '')) for t in teams[:2]])
        if len(teams) > 2:
            team_names += f" +{len(teams) - 2}"
        output += f"| {i} | {name} | {repo} | {team_names} |\n"

    if len(projects) > 10:
        output += f"\n*...and {len(projects) - 10} more projects*\n"

    output += "\n**To link to a project, call identify with `project_key`:**\n"
    output += "```\n"
    output += f'identify(agent_id="...", client="...", model_id="...", project_key="{projects[0].get("project_key")}")\n'
    output += "```\n\n"
    output += "*Or continue without a project - sessions and milestones will still work but won't be linked to a specific project.*\n"

    return output


async def _fetch_existing_agents_for_user(config: Any, client_filter: str = None) -> list:
    """
    Fetch existing agents for the authenticated user.

    Returns a list of agent dicts with agent_id, focus, last_heartbeat, client, etc.
    """
    try:
        params = {"active_only": "false"}  # Show all agents, not just active
        if client_filter:
            params["client"] = client_filter

        # The /agents endpoint already filters by authenticated user
        result = await _make_request(config, "GET", "/agents", params=params)

        if result.get("success"):
            return result.get("data", {}).get("agents", [])
        return []
    except Exception:
        return []


def _score_agent_relevance(agent: dict, client_type: str, project_name: str) -> int:
    """
    Score an agent's relevance to the current context.

    Higher score = more relevant.
    """
    score = 0

    # Same client type is a strong signal
    if agent.get("client") == client_type:
        score += 50

    # Project name in agent_id
    agent_id = agent.get("agent_id", "").lower()
    if project_name and project_name.lower() in agent_id:
        score += 40

    # Active agents score higher
    if agent.get("is_active"):
        score += 30

    # Recent heartbeat (within last hour)
    last_heartbeat = agent.get("last_heartbeat")
    if last_heartbeat:
        try:
            from datetime import datetime, timezone
            hb_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_minutes = (now - hb_time).total_seconds() / 60
            if age_minutes < 60:
                score += 20
            elif age_minutes < 240:
                score += 10
        except Exception:
            pass

    return score


def _format_existing_agents(agents: list, client_type: str, project_name: str) -> str:
    """
    Format existing agents for display with relevance scoring.
    """
    if not agents:
        return ""

    # Score and sort agents by relevance
    scored_agents = []
    for agent in agents:
        score = _score_agent_relevance(agent, client_type, project_name)
        scored_agents.append((score, agent))

    scored_agents.sort(key=lambda x: x[0], reverse=True)

    output = "## Existing Agents Found\n\n"
    output += "You have existing agent registrations that might be you:\n\n"
    output += "| Agent ID | Client | Focus | Status | Relevance |\n"
    output += "|----------|--------|-------|--------|----------|\n"

    best_match = None
    for score, agent in scored_agents[:5]:  # Show top 5
        agent_id = agent.get("agent_id", "unknown")
        client = agent.get("client", "-")
        focus = agent.get("focus", "-")
        if focus and len(focus) > 30:
            focus = focus[:27] + "..."

        is_active = agent.get("is_active", False)
        status = "🟢 Active" if is_active else "⚪ Inactive"

        # Relevance indicator
        if score >= 80:
            relevance = "⭐⭐⭐ High"
            if not best_match:
                best_match = agent
        elif score >= 50:
            relevance = "⭐⭐ Medium"
            if not best_match:
                best_match = agent
        elif score >= 20:
            relevance = "⭐ Low"
        else:
            relevance = "- None"

        output += f"| `{agent_id}` | {client} | {focus} | {status} | {relevance} |\n"

    output += "\n"

    # Suggestion
    if best_match:
        output += f"**💡 Suggestion:** Use `{best_match.get('agent_id')}` (best match for current context)\n\n"
        output += "To continue as this agent, use the same agent_id:\n"
        output += "```\n"
        output += f'identify(agent_id="{best_match.get("agent_id")}", client="{client_type}", model_id="...")\n'
        output += "```\n\n"
        output += "Or proceed with a new agent_id to create a fresh registration.\n\n"
    else:
        output += "No strong matches found. Proceeding will create a new agent registration.\n\n"

    output += "---\n\n"
    return output


async def _fetch_available_options(config: Any) -> dict:
    """Fetch available personas, clients, and models from CM API."""
    options = {
        "personas": [],
        "clients": [],
        "models": [],
    }

    try:
        # Fetch personas
        personas_result = await _make_request(config, "GET", "/personas")
        if personas_result.get("success"):
            personas = personas_result.get("data", {}).get("personas", [])
            options["personas"] = [
                {
                    "role": p.get("role"),
                    "name": p.get("name"),
                    "persona_key": p.get("persona_key"),
                    "suggested_clients": p.get("suggested_clients", []),
                }
                for p in personas
            ]
    except Exception:
        pass

    try:
        # Fetch clients
        clients_result = await _make_request(config, "GET", "/clients")
        if clients_result.get("success"):
            clients = clients_result.get("data", {}).get("clients", [])
            options["clients"] = [
                {
                    "client": c.get("value"),  # API returns 'value' not 'client'
                    "name": c.get("name"),
                    "description": c.get("description"),
                    "suggested_personas": c.get("suggested_personas", []),
                }
                for c in clients
            ]
    except Exception:
        pass

    try:
        # Fetch models
        models_result = await _make_request(config, "GET", "/models")
        if models_result.get("success"):
            models = models_result.get("data", {}).get("models", [])
            options["models"] = [
                {
                    "model_key": m.get("model_key"),
                    "name": m.get("name"),
                    "provider": m.get("provider"),
                    "model_id": m.get("model_id"),
                }
                for m in models
                if m.get("status") == "active"
            ]
    except Exception:
        pass

    return options


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def identify(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Identify yourself to Collective Memory (CM).

    When called without parameters: Shows available options for personas, clients, and models.
    When called with parameters: Registers or updates your identity.

    This is the recommended first tool to call when connecting to CM.

    Args:
        agent_id: Your unique agent identifier (e.g., "claude-code-wayne-auth-task")
        persona: Persona role to adopt (e.g., "backend-code", "architect", "consultant")
        client: Client type - you know this! (claude-code, claude-desktop, codex, gemini-cli, cursor)
        model_id: Your model identifier - you know this! (e.g., "claude-opus-4-5-20251101")
        model_key: Model key from database (alternative to model_id)
        focus: What you're currently working on - describe your task
        team_key: Explicit team key to set as active (optional - auto-detected if not provided)
        team_slug: Team slug to set as active (optional - resolved to team_key)
    """
    agent_id = arguments.get("agent_id")
    persona = arguments.get("persona")
    client_type = arguments.get("client")
    model_id = arguments.get("model_id")
    model_key = arguments.get("model_key")
    focus = arguments.get("focus")
    explicit_team_key = arguments.get("team_key")
    explicit_team_slug = arguments.get("team_slug")
    explicit_project_key = arguments.get("project_key")

    # If no identity parameters provided, show the challenge/options
    if not agent_id and not persona:
        options = await _fetch_available_options(config)

        output = "# Welcome to Collective Memory (CM)\n\n"
        output += "To collaborate in CM, you need to identify yourself.\n\n"

        # Show current identity if registered
        if session_state.get("registered"):
            output += "## Current Identity\n"
            output += f"- **Agent ID:** {session_state.get('agent_id')}\n"
            output += f"- **Persona:** {session_state.get('persona') or '(not set)'}\n"
            output += f"- **Client:** {session_state.get('client') or '(not set)'}\n"
            output += f"- **Focus:** {session_state.get('focus') or '(not set)'}\n\n"
            output += "---\n\n"

        # Show existing agents for this user
        existing_agents = await _fetch_existing_agents_for_user(config)
        if existing_agents:
            output += "## Your Existing Agent Registrations\n"
            output += "You have previously registered agents that you can resume:\n\n"
            output += "| Agent ID | Client | Focus | Status |\n"
            output += "|----------|--------|-------|--------|\n"
            for agent in existing_agents[:10]:  # Show top 10
                agent_id_display = agent.get("agent_id", "unknown")
                client = agent.get("client", "-")
                focus = agent.get("focus", "-")
                if focus and len(focus) > 30:
                    focus = focus[:27] + "..."
                is_active = agent.get("is_active", False)
                status = "🟢 Active" if is_active else "⚪ Inactive"
                output += f"| `{agent_id_display}` | {client} | {focus} | {status} |\n"
            output += "\n*To resume an existing agent, use its agent_id when calling identify.*\n\n"
            output += "---\n\n"

        # Dynamic identity guidance
        output += "## Dynamic Self-Identification\n\n"
        output += "You can choose your own identity based on your current context:\n\n"

        # Agent ID suggestions based on context
        output += "### Agent ID\n"
        output += "Create an agent_id that reflects your context:\n"
        detected_client = config.detected_client
        if detected_client == "claude-code":
            output += "- Based on project: `claude-code-{project-name}`\n"
            output += "- Based on task: `cc-{user}-{task-description}`\n"
            output += "- With uniqueness: `claude-code-{project}-{short-uuid}`\n"
            output += "\nExamples:\n"
            output += "- `claude-code-collective-memory-api`\n"
            output += "- `cc-wayne-auth-refactor`\n"
            output += "- `claude-code-dashboard-frontend`\n"
        elif detected_client == "claude-desktop":
            output += "- `claude-desktop-{user}-{context}`\n"
            output += "- `cd-{user}-research`\n"
        else:
            output += "- `{client}-{user}-{task}`\n"
            output += "- `ai-agent-{project}`\n"
        output += "\n"

        # Available personas with guidance
        output += "### Persona Selection\n"
        output += "Choose a persona that matches your current work:\n\n"
        if options["personas"]:
            for p in options["personas"]:
                clients_hint = ""
                if p.get("suggested_clients"):
                    clients_hint = f" (best for: {', '.join(p['suggested_clients'])})"
                output += f"- **{p['role']}**: {p['name']}{clients_hint}\n"
            output += "\n*Tip: Inspect project files to choose the right persona:*\n"
            output += "*- Python/Flask/Django → backend-code*\n"
            output += "*- React/Vue/TypeScript → frontend-code*\n"
            output += "*- Mixed stack → full-stack or architect*\n"
        else:
            output += "- *No personas available - contact CM admin*\n"
        output += "\n"

        # Available clients
        output += "## Client Types\n"
        if detected_client:
            output += f"*Auto-detected: **{detected_client}***\n\n"
        if options["clients"]:
            for c in options["clients"]:
                output += f"- **{c['client']}**: {c['description']}\n"
        else:
            output += "- claude-code, claude-desktop, codex, gemini-cli, cursor\n"
        output += "\n"

        # Available models
        output += "## Available Models\n"
        output += "*Use model_id when registering (not model_key)*\n\n"
        if options["models"]:
            by_provider = {}
            for m in options["models"]:
                provider = m.get("provider", "unknown")
                if provider not in by_provider:
                    by_provider[provider] = []
                by_provider[provider].append(m)

            for provider, models in by_provider.items():
                output += f"**{provider.title()}:**\n"
                for m in models:
                    output += f"- {m['name']}: `{m['model_id']}`\n"
        else:
            output += "- *No models registered*\n"
        output += "\n"

        # Example usage
        output += "---\n\n"
        output += "## Register Your Identity\n"
        output += "Call `identify` with your chosen parameters:\n"
        output += "```\n"
        output += 'identify(agent_id="claude-code-{project}", persona="backend-code")\n'
        output += "```\n\n"
        output += "**Why dynamic identity?**\n"
        output += "- Each terminal/session can have a unique identity\n"
        output += "- Avoids collisions when running multiple Claude Code instances\n"
        output += "- Context-aware naming helps track who did what\n"
        output += "- Use `update_my_identity` to change identity later\n"

        return [types.TextContent(type="text", text=output)]

    # Otherwise, register/update identity
    # Collect missing required fields
    missing_fields = []

    if not agent_id:
        agent_id = session_state.get("agent_id") or config.agent_id
        if not agent_id:
            missing_fields.append("agent_id")

    if not client_type:
        # Don't auto-detect - require explicit client
        missing_fields.append("client")

    if not model_id and not model_key:
        missing_fields.append("model_id")

    if missing_fields:
        output = "## Missing Required Fields\n\n"
        output += f"The following fields are **required** to register: `{', '.join(missing_fields)}`\n\n"
        output += "**You know these things about yourself - provide them!**\n\n"

        if "agent_id" in missing_fields:
            output += "### agent_id\n"
            output += "Choose based on your project/task context:\n"
            output += "- `claude-code-{project-name}` or `claude-desktop-{user}-{context}`\n\n"

        if "client" in missing_fields:
            output += "### client (REQUIRED)\n"
            output += "**You know what client you are!** Pick one:\n"
            output += "- `claude-code` - Claude Code CLI\n"
            output += "- `claude-desktop` - Claude Desktop app or claude.ai web\n"
            output += "- `codex` - OpenAI Codex\n"
            output += "- `gemini-cli` - Google Gemini CLI\n\n"

        if "model_id" in missing_fields:
            output += "### model_id (REQUIRED)\n"
            output += "**You know your model!** Examples:\n"
            output += "- `claude-opus-4-5-20251101`\n"
            output += "- `claude-sonnet-4-20250514`\n"
            output += "- `gpt-4-turbo`\n"
            output += "- `gemini-pro`\n\n"

        output += "**Example registration:**\n"
        output += "```\n"
        output += 'identify(\n'
        output += '    agent_id="claude-code-myproject",\n'
        output += '    client="claude-code",\n'
        output += '    model_id="claude-opus-4-5-20251101",\n'
        output += '    persona="backend-code",\n'
        output += '    focus="Working on feature X"\n'
        output += ')\n'
        output += "```\n"
        return [types.TextContent(type="text", text=output)]

    # Check if PAT is configured (required for agent registration)
    # Priority: 1) Per-session PAT (SSE multi-user), 2) Config PAT (env/stdio)
    session_pat = get_session_pat()
    has_pat = session_pat or (hasattr(config, 'pat') and config.pat)
    if not has_pat:
        output = "## Authentication Required\n\n"
        output += "**Agent registration requires a Personal Access Token (PAT).**\n\n"
        output += "To register agents with Collective Memory, you must:\n\n"
        output += "1. **Create a PAT** in the CM web UI under Profile → Access Tokens\n"
        output += "2. **Configure CM_PAT** environment variable:\n"
        output += "   ```bash\n"
        output += "   export CM_PAT=\"your-personal-access-token\"\n"
        output += "   ```\n"
        output += "3. **Restart your MCP session** to pick up the new config\n\n"
        output += "Without a PAT, agents cannot be registered or updated.\n"
        return [types.TextContent(type="text", text=output)]

    try:
        # Detect project - priority: explicit > git remote > directory name
        git_project = _detect_project_from_git()
        detected_project_key = None
        detected_project_name = None
        detected_db_project = None  # Project from database (via /projects/lookup)
        project_teams = []  # Teams associated with the project
        project_detection_method = None  # Track how project was detected
        user_projects = []  # Will be populated if needed for fallback
        working_dir_name = None  # Current directory name

        # 1. Check for explicit project_key first
        if explicit_project_key:
            try:
                project_result = await _make_request(
                    config,
                    "GET",
                    f"/projects/{explicit_project_key}",
                    params={"include_teams": "true"}
                )
                if project_result.get("success"):
                    detected_db_project = project_result.get("data", {}).get("project")
                    if detected_db_project:
                        detected_project_key = detected_db_project.get('project_key')
                        detected_project_name = detected_db_project.get('name')
                        project_teams = detected_db_project.get('teams', [])
                        project_detection_method = "explicit"
            except Exception:
                pass

        # 2. Try git remote detection
        if not detected_project_key and git_project:
            # Use git remote info for project context
            detected_project_name = git_project['repo']

            # Query API to find project by repository URL
            api_project_data = await _detect_project_from_api(config, session_state, git_project['url'])
            if api_project_data:
                detected_db_project = api_project_data.get('project')
                project_teams = api_project_data.get('teams', [])
                if detected_db_project:
                    detected_project_key = detected_db_project.get('project_key')
                    detected_project_name = detected_db_project.get('name') or detected_project_name
                    project_detection_method = "git_remote"

        # 3. Try directory name matching (fallback when no git remote)
        if not detected_project_key:
            working_dir_name = _get_working_directory_name()
            if working_dir_name:
                # Fetch user's projects for matching
                user_projects = await _fetch_user_projects(config)
                if user_projects:
                    matched_project = _match_directory_to_project(working_dir_name, user_projects)
                    if matched_project:
                        detected_db_project = matched_project
                        detected_project_key = matched_project.get('project_key')
                        detected_project_name = matched_project.get('name')
                        project_teams = matched_project.get('teams', [])
                        project_detection_method = "directory_match"

        # 4. If still no match, show project selection prompt (but continue with registration)
        project_selection_prompt = ""
        if not detected_project_key and not explicit_project_key:
            # Fetch projects if not already fetched
            if not user_projects:
                user_projects = await _fetch_user_projects(config)
            if user_projects:
                project_selection_prompt = _format_project_selection_prompt(user_projects, working_dir_name)

        # Fetch existing agents for this user to help with identity selection
        # Don't filter by client - show all agents and let relevance scoring handle it
        existing_agents = await _fetch_existing_agents_for_user(config)

        # Check if the provided agent_id matches an existing agent
        # Account for auto-suffix: cc-wayne-cm might match cc-wayne-cm-wh
        existing_agent_ids = [a.get("agent_id") for a in existing_agents]
        agent_id_is_existing = agent_id in existing_agent_ids

        # Also check if provided agent_id is a prefix of any existing agent (before suffix)
        agent_id_matches_prefix = any(
            existing_id.startswith(agent_id + "-") or existing_id == agent_id
            for existing_id in existing_agent_ids
        )

        # Build the existing agents display (will be shown in output later)
        existing_agents_display = ""
        if existing_agents and not agent_id_is_existing and not agent_id_matches_prefix:
            # Only show existing agents if the provided agent_id is truly NEW
            existing_agents_display = _format_existing_agents(
                existing_agents,
                client_type,
                detected_project_name
            )

        # Resolve model_id to model_key if provided
        resolved_model_key = model_key
        model_name = None
        model_resolved = False  # Track if we successfully found the model

        if model_id and not model_key:
            # First try looking up by model_id
            try:
                model_result = await _make_request(
                    config,
                    "GET",
                    f"/models/by-model-id/{model_id}"
                )
                if model_result.get("success"):
                    model_data = model_result.get("data", {})
                    resolved_model_key = model_data.get("model_key")
                    model_name = model_data.get("name")
                    model_resolved = True
            except Exception:
                pass

            # If model_id lookup failed and it looks like a UUID, try as model_key
            if not model_resolved and len(model_id) == 36 and model_id.count('-') == 4:
                try:
                    model_result = await _make_request(
                        config,
                        "GET",
                        f"/models/{model_id}"
                    )
                    if model_result.get("success"):
                        model_data = model_result.get("data", {})
                        resolved_model_key = model_data.get("model_key") or model_id
                        model_name = model_data.get("name")
                        model_resolved = True
                except Exception:
                    pass
        elif model_key:
            # If model_key was provided directly, look it up
            try:
                model_result = await _make_request(
                    config,
                    "GET",
                    f"/models/{model_key}"
                )
                if model_result.get("success"):
                    model_data = model_result.get("data", {})
                    model_name = model_data.get("name")
                    model_resolved = True
            except Exception:
                pass

        # Build registration payload
        registration_data = {
            "agent_id": agent_id,
            "capabilities": config.capabilities_list if hasattr(config, 'capabilities_list') else ["search", "create", "update"],
        }

        if client_type:
            registration_data["client"] = client_type
            # Map client type to client_key (e.g., 'claude-code' → 'client-claude-code')
            client_key = f"client-{client_type}" if not client_type.startswith("client-") else client_type
            registration_data["client_key"] = client_key
        if resolved_model_key:
            registration_data["model_key"] = resolved_model_key
        if focus:
            registration_data["focus"] = focus

        # Add project info if detected
        if detected_project_key:
            registration_data["project_key"] = detected_project_key
        if detected_project_name:
            registration_data["project_name"] = detected_project_name

        # Fetch user info BEFORE registration to get team_key
        # We need this for: user initials, membership slug, team resolution, and domain context
        user_initials = None
        membership_slug = None
        resolved_team_key = None
        resolved_team_name = None
        team_detected_from_project = False  # Track how team was detected
        user_data = {}
        teams = []
        available_scopes = []
        default_scope = {}

        if has_pat:
            try:
                me_result = await _make_request(config, "GET", "/auth/me")
                if me_result.get("success"):
                    me_data = me_result.get("data", {})
                    user_data = me_data.get("user", {})
                    teams = me_data.get("teams", [])
                    available_scopes = me_data.get("available_scopes", [])
                    default_scope = me_data.get("default_scope", {})
                    user_initials = user_data.get("initials", "").lower()

                    # Resolve team from explicit params or auto-detect
                    if explicit_team_key:
                        team = next((t for t in teams if t.get('team_key') == explicit_team_key), None)
                        if team:
                            resolved_team_key = explicit_team_key
                            resolved_team_name = team.get('name')
                            membership_slug = team.get('membership_slug')
                    elif explicit_team_slug:
                        team = next((t for t in teams if t.get('slug') == explicit_team_slug), None)
                        if team:
                            resolved_team_key = team.get('team_key')
                            resolved_team_name = team.get('name')
                            membership_slug = team.get('membership_slug')
                    elif teams:
                        # Auto-detect team from project name or agent_id
                        # Priority: 1) detected project name, 2) agent_id pattern

                        # First, try to match detected project name against team names/slugs
                        if detected_project_name and not resolved_team_key:
                            project_name_normalized = detected_project_name.lower().replace('-', ' ').replace('_', ' ')
                            for t in teams:
                                team_slug = t.get('slug', '').lower().replace('-', ' ').replace('_', ' ')
                                team_name = t.get('name', '').lower().replace('-', ' ').replace('_', ' ')
                                # Check if project name matches team slug or name
                                if team_slug and (team_slug == project_name_normalized or project_name_normalized in team_slug or team_slug in project_name_normalized):
                                    resolved_team_key = t.get('team_key')
                                    resolved_team_name = t.get('name')
                                    membership_slug = t.get('membership_slug')
                                    team_detected_from_project = True
                                    break
                                elif team_name and (team_name == project_name_normalized or project_name_normalized in team_name or team_name in project_name_normalized):
                                    resolved_team_key = t.get('team_key')
                                    resolved_team_name = t.get('name')
                                    membership_slug = t.get('membership_slug')
                                    team_detected_from_project = True
                                    break

                        # Second, try to match agent_id against team names/slugs
                        if agent_id and not resolved_team_key:
                            agent_id_lower = agent_id.lower().replace('-', ' ').replace('_', ' ')
                            for t in teams:
                                team_slug = t.get('slug', '').lower().replace('-', ' ').replace('_', ' ')
                                team_name = t.get('name', '').lower()
                                if team_slug and team_slug in agent_id_lower:
                                    resolved_team_key = t.get('team_key')
                                    resolved_team_name = t.get('name')
                                    membership_slug = t.get('membership_slug')
                                    break
                                elif team_name and team_name in agent_id_lower:
                                    resolved_team_key = t.get('team_key')
                                    resolved_team_name = t.get('name')
                                    membership_slug = t.get('membership_slug')
                                    break

                        # Third, use project's associated teams from /projects/lookup
                        # Prefer 'owner' role, then 'contributor', then any
                        if not resolved_team_key and project_teams:
                            # Sort by role priority: owner > contributor > viewer
                            role_priority = {'owner': 0, 'contributor': 1, 'viewer': 2}
                            sorted_teams = sorted(
                                project_teams,
                                key=lambda x: role_priority.get(x.get('role', 'viewer'), 3)
                            )
                            for pt in sorted_teams:
                                pt_team_key = pt.get('team_key')
                                # Check if user is a member of this team
                                user_team = next((t for t in teams if t.get('team_key') == pt_team_key), None)
                                if user_team:
                                    resolved_team_key = pt_team_key
                                    resolved_team_name = user_team.get('name')
                                    membership_slug = user_team.get('membership_slug')
                                    team_detected_from_project = True
                                    break
            except Exception:
                pass  # Continue without user info

        # Use membership_slug if available (team-specific), otherwise fall back to user_initials
        suffix = membership_slug or user_initials

        # Auto-suffix agent_id with suffix (if not already present)
        if suffix and agent_id:
            if not agent_id.endswith(f'-{suffix}'):
                # Check if agent_id already has a short alphanumeric suffix that we should replace
                parts = agent_id.rsplit('-', 1)
                if len(parts) == 2 and len(parts[1]) <= 10 and parts[1].replace('-', '').isalnum():
                    # Replace existing suffix with user's suffix
                    agent_id = f"{parts[0]}-{suffix}"
                else:
                    # Append suffix
                    agent_id = f"{agent_id}-{suffix}"

        # Add team_key to registration if resolved
        if resolved_team_key:
            registration_data["team_key"] = resolved_team_key

        # Resolve persona to persona_key
        persona_key = None
        if persona:
            try:
                personas_result = await _make_request(
                    config,
                    "GET",
                    "/personas/by-role/" + persona
                )
                if personas_result.get("success"):
                    persona_data = personas_result.get("data", {})
                    persona_key = persona_data.get("persona_key")
                    if persona_key:
                        registration_data["persona_key"] = persona_key
            except Exception:
                pass

        # Register with CM
        result = await _make_request(
            config,
            "POST",
            "/agents/register",
            json=registration_data
        )

        if result.get("success"):
            agent_data = result.get("data", {})

            # Update session state
            session_state["agent_id"] = agent_id
            session_state["agent_key"] = agent_data.get("agent_key")
            session_state["persona"] = persona
            session_state["persona_key"] = persona_key
            session_state["model_key"] = resolved_model_key if model_resolved else None
            session_state["model_id"] = model_id
            session_state["model_name"] = model_name
            session_state["model_resolved"] = model_resolved
            session_state["focus"] = focus
            session_state["client"] = client_type
            # Store client_key for milestone EXECUTED_BY relationships
            if client_type:
                session_state["client_key"] = f"client-{client_type}" if not client_type.startswith("client-") else client_type
            session_state["registered"] = True

            # Store affinity warning if present
            if agent_data.get("affinity_warning"):
                session_state["affinity_warning"] = agent_data.get("affinity_warning")

            # Store project info in session_state (from git detection and API lookup)
            if git_project:
                session_state["project_owner"] = git_project.get('owner')
                session_state["project_repo"] = git_project.get('repo')
                session_state["repository_url"] = git_project.get('url')
            if detected_project_key:
                session_state["project_key"] = detected_project_key
            if detected_project_name:
                session_state["project_name"] = detected_project_name
            if project_detection_method:
                session_state["project_detection_method"] = project_detection_method
            # Store database project info if found
            if detected_db_project:
                session_state["db_project"] = detected_db_project
                session_state["db_project_key"] = detected_db_project.get('project_key')

            # Store user info (already fetched before registration)
            if user_data:
                session_state["user_key"] = user_data.get("user_key")
                session_state["user_email"] = user_data.get("email")
                session_state["user_display_name"] = user_data.get("display_name")
                session_state["user_first_name"] = user_data.get("first_name")
                session_state["user_last_name"] = user_data.get("last_name")
                session_state["user_role"] = user_data.get("role")
                session_state["user_status"] = user_data.get("status")
                session_state["user_initials"] = user_data.get("initials")
                domain_key = user_data.get("domain_key")
                if domain_key:
                    session_state["domain_key"] = domain_key
                # Store domain details if available
                domain_data = user_data.get("domain")
                if domain_data:
                    session_state["domain_name"] = domain_data.get("name")

            # Store teams info
            session_state["teams"] = teams

            # Store scopes info
            session_state["available_scopes"] = available_scopes
            session_state["default_scope"] = default_scope

            # Set active team if resolved (already done before registration)
            if resolved_team_key:
                session_state["active_team_key"] = resolved_team_key
                session_state["active_team_name"] = resolved_team_name
                session_state["membership_slug"] = membership_slug
                # Determine detection method for display
                if explicit_team_key:
                    session_state["active_team_method"] = "explicit_team_key"
                elif explicit_team_slug:
                    session_state["active_team_method"] = "explicit_team_slug"
                elif team_detected_from_project:
                    session_state["active_team_method"] = f"auto (from project: {detected_project_name})"
                else:
                    session_state["active_team_method"] = "auto (from agent_id)"
                # Update default scope to team
                session_state["default_scope"] = {
                    "scope_type": "team",
                    "scope_key": resolved_team_key
                }

            # Try to resolve persona name
            if persona:
                try:
                    personas_result = await _make_request(
                        config,
                        "GET",
                        "/personas",
                        params={"role": persona}
                    )
                    if personas_result.get("success"):
                        personas = personas_result.get("data", {}).get("personas", [])
                        if personas:
                            session_state["persona_name"] = personas[0].get("name")
                except Exception:
                    pass

            # Check for active work session
            active_work_session = None
            try:
                work_session_result = await _make_request(
                    config,
                    "GET",
                    "/work-sessions/active"
                )
                if work_session_result.get("success"):
                    active_work_session = work_session_result.get("data", {}).get("session")
                    if active_work_session:
                        session_state["active_work_session"] = active_work_session
                        # Track active session key for automatic activity updates
                        session_state["active_session_key"] = active_work_session.get("session_key")
                        session_state["last_session_activity_update"] = None  # Will update on next tool call
            except Exception:
                pass  # Continue without work session info

            output = "# Identity Confirmed\n\n"
            output += f"Welcome to Collective Memory (CM)!\n\n"

            # Show existing agents if any (and this is a new agent_id)
            if existing_agents_display:
                output += existing_agents_display

            # Show authenticated user details prominently
            if session_state.get("user_display_name") or session_state.get("user_email"):
                output += "## Authenticated User\n"
                if session_state.get("user_display_name"):
                    output += f"**Name:** {session_state.get('user_display_name')}\n"
                if session_state.get("user_email"):
                    output += f"**Email:** {session_state.get('user_email')}\n"
                if session_state.get("user_role"):
                    output += f"**Role:** {session_state.get('user_role')}\n"
                if session_state.get("user_key"):
                    output += f"**User Key:** {session_state.get('user_key')}\n"
                output += "\n"

            # Show domain context
            if session_state.get("domain_key"):
                output += "## Domain\n"
                if session_state.get("domain_name"):
                    output += f"**Name:** {session_state.get('domain_name')}\n"
                output += f"**Domain Key:** {session_state.get('domain_key')}\n"
                output += "\n"

            # Show teams if any
            teams = session_state.get("teams", [])
            if teams:
                output += "## Teams\n"
                for t in teams:
                    output += f"- **{t.get('name')}** ({t.get('role')})\n"
                output += "\n"

            # Show scopes info
            available_scopes = session_state.get("available_scopes", [])
            default_scope = session_state.get("default_scope", {})
            if available_scopes:
                output += "## Available Scopes\n"
                for s in available_scopes:
                    scope_type = s.get('scope_type', 'unknown')
                    scope_name = s.get('name', 'Unknown')
                    access_level = s.get('access_level', 'member')
                    is_default = (
                        s.get('scope_type') == default_scope.get('scope_type') and
                        s.get('scope_key') == default_scope.get('scope_key')
                    )
                    default_marker = " ← default" if is_default else ""
                    output += f"- **{scope_name}** ({scope_type}, {access_level}){default_marker}\n"
                output += "\n*Use scope_type/scope_key in create_entity to target specific scopes*\n\n"

            output += "## Agent Registration\n"
            output += f"**Agent ID:** {agent_id}\n"
            output += f"**Agent Key:** {agent_data.get('agent_key')}\n"
            output += f"**Client:** {client_type}\n"

            if persona:
                output += f"**Persona:** {persona}"
                if session_state.get("persona_name"):
                    output += f" ({session_state['persona_name']})"
                output += "\n"

            if model_resolved and model_name:
                output += f"**Model:** {model_name}\n"
            elif model_id and not model_resolved:
                # Model wasn't found - show warning
                output += f"**Model:** ⚠️ Unknown ({model_id[:20]}{'...' if len(model_id) > 20 else ''})\n"

            if focus:
                output += f"**Focus:** {focus}\n"

            # Show active team if set
            if session_state.get("active_team_key"):
                output += f"**Active Team:** {session_state.get('active_team_name', session_state.get('active_team_key'))}"
                if session_state.get("active_team_method"):
                    output += f" ({session_state.get('active_team_method')})"
                output += "\n"

            # Show project info if detected
            if detected_project_name or detected_project_key or git_project or detected_db_project:
                output += "\n## Project Context\n"
                if git_project:
                    output += f"**GitHub:** {git_project.get('owner')}/{git_project.get('repo')}\n"
                if detected_project_name:
                    output += f"**Name:** {detected_project_name}\n"
                if detected_db_project:
                    output += f"**Project Key:** {detected_db_project.get('project_key')}\n"
                    if project_teams:
                        team_names = [t.get('team', {}).get('name') or t.get('team_key') for t in project_teams[:3]]
                        output += f"**Teams:** {', '.join(team_names)}\n"
                # Show detection method
                if project_detection_method:
                    method_labels = {
                        "explicit": "explicit project_key",
                        "git_remote": "git remote",
                        "directory_match": f"directory name match ({working_dir_name})"
                    }
                    output += f"**Detected via:** {method_labels.get(project_detection_method, project_detection_method)}\n"
            elif project_selection_prompt:
                # No project detected - show selection prompt
                output += "\n" + project_selection_prompt

            # Show active work session if any
            if active_work_session:
                output += "\n## Active Work Session\n"
                session_name = active_work_session.get('name') or 'Unnamed session'
                project_info = active_work_session.get('project', {})
                project_name = project_info.get('name') if project_info else active_work_session.get('project_key', 'Unknown')
                output += f"**Session:** {session_name}\n"
                output += f"**Project:** {project_name}\n"
                # Show time remaining if available
                time_remaining = active_work_session.get('time_remaining_seconds')
                if time_remaining is not None:
                    if time_remaining < 600:  # Less than 10 minutes
                        mins = max(1, time_remaining // 60)
                        output += f"**Expires in:** ⚠️ {mins} minute{'s' if mins != 1 else ''}\n"
                    elif time_remaining < 3600:  # Less than 1 hour
                        mins = time_remaining // 60
                        output += f"**Expires in:** {mins} minutes\n"
                    else:
                        hours = time_remaining // 3600
                        mins = (time_remaining % 3600) // 60
                        output += f"**Expires in:** {hours}h {mins}m\n"
                output += "\n**Track your progress with milestones:**\n"
                output += "- `record_milestone(name=\"Starting X\", status=\"started\")` - when beginning major tasks\n"
                output += "- `record_milestone(name=\"X completed\")` - when finishing tasks (status defaults to \"completed\")\n"
                output += "- `record_milestone(name=\"Blocked on Y\", status=\"blocked\")` - if you hit a blocker\n"

            if agent_data.get("affinity_warning"):
                output += f"\n⚠️ {agent_data.get('affinity_warning')}\n"

            output += "\nYou are now registered and can collaborate in CM.\n"
            output += "Use `update_focus` to let others know what you're working on.\n\n"
            output += "*Heartbeats are sent automatically when you use CM tools to keep you active.*"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Failed to identify: {result.get('msg', 'Unknown error')}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error identifying with CM: {str(e)}"
        )]


async def get_my_identity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Get the current agent's identity in Collective Memory (CM).

    Returns the agent's ID, client, model, persona, focus, and registration status.
    If not registered, shows guidance for dynamic self-identification.
    """
    if not session_state.get("registered"):
        # Show guidance for dynamic self-identification
        options = await _fetch_available_options(config)

        output = "# Identity Not Established\n\n"
        output += "You are not yet registered with Collective Memory.\n\n"

        output += "## Dynamic Self-Identification\n\n"
        output += "You can create your own identity based on context:\n\n"

        output += "**1. Choose an agent_id** based on:\n"
        output += "   - Your current working directory/project name\n"
        output += "   - The task you're working on\n"
        output += "   - Your hostname or terminal session\n"
        output += "   - Example: `claude-code-{project}-{task}` or `cc-{user}-{context}`\n\n"

        output += "**2. Select a persona** based on the work:\n"
        if options["personas"]:
            output += "   Available personas:\n"
            for p in options["personas"][:6]:
                clients_hint = ""
                if p.get("suggested_clients"):
                    clients_hint = f" (for: {', '.join(p['suggested_clients'][:2])})"
                output += f"   - `{p['role']}`: {p['name']}{clients_hint}\n"
            if len(options["personas"]) > 6:
                output += f"   - ... and {len(options['personas']) - 6} more\n"
        output += "\n"

        output += "**3. Provide what you KNOW about yourself (REQUIRED):**\n"
        output += "   - `client` (REQUIRED): claude-code, claude-desktop (includes claude.ai), codex, or gemini-cli, cursor\n"
        output += "   - `model_id` (REQUIRED): Your model (e.g., `claude-opus-4-5-20251101`)\n"
        output += "   - `focus`: What task are you currently helping with?\n\n"

        output += "**4. Register with `identify`:**\n"
        output += "```\n"
        output += 'identify(\n'
        output += '    agent_id="claude-code-{project}",\n'
        output += '    client="claude-code",           # REQUIRED - you know this!\n'
        output += '    model_id="claude-opus-4-5-20251101",  # REQUIRED - you know this!\n'
        output += '    persona="backend-code",\n'
        output += '    focus="What you are working on"\n'
        output += ')\n'
        output += "```\n\n"

        output += "**You MUST provide client and model_id - you know these!**\n"

        return [types.TextContent(type="text", text=output)]

    output = "## My Identity in CM\n\n"

    # Show authenticated user details first
    if session_state.get("user_display_name") or session_state.get("user_email"):
        output += "### Authenticated User\n"
        if session_state.get("user_display_name"):
            output += f"**Name:** {session_state.get('user_display_name')}\n"
        if session_state.get("user_email"):
            output += f"**Email:** {session_state.get('user_email')}\n"
        if session_state.get("user_role"):
            output += f"**Role:** {session_state.get('user_role')}\n"
        if session_state.get("user_key"):
            output += f"**User Key:** {session_state.get('user_key')}\n"
        output += "\n"

    # Show domain context
    if session_state.get("domain_key"):
        output += "### Domain\n"
        if session_state.get("domain_name"):
            output += f"**Name:** {session_state.get('domain_name')}\n"
        output += f"**Domain Key:** {session_state.get('domain_key')}\n"
        output += "\n"

    # Show teams if any
    teams = session_state.get("teams", [])
    if teams:
        output += "### Teams\n"
        for t in teams:
            output += f"- **{t.get('name')}** ({t.get('role')})\n"
        output += "\n"

    # Show scopes info
    available_scopes = session_state.get("available_scopes", [])
    default_scope = session_state.get("default_scope", {})
    if available_scopes:
        output += "### Available Scopes\n"
        for s in available_scopes:
            scope_type = s.get('scope_type', 'unknown')
            scope_name = s.get('name', 'Unknown')
            access_level = s.get('access_level', 'member')
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            default_marker = " ← default" if is_default else ""
            output += f"- **{scope_name}** ({scope_type}, {access_level}){default_marker}\n"
        output += "\n"

    output += "### Agent\n"
    output += f"**Agent ID:** {session_state.get('agent_id')}\n"
    output += f"**Agent Key:** {session_state.get('agent_key')}\n"

    # Client info
    client = session_state.get("client")
    if client:
        output += f"**Client:** {client}\n"

    # Model info - only show if resolved
    if session_state.get("model_resolved") and session_state.get("model_name"):
        output += f"\n### Model\n"
        output += f"**Name:** {session_state.get('model_name')}\n"
        if session_state.get("model_key"):
            output += f"**Model Key:** {session_state.get('model_key')}\n"
    elif session_state.get("model_id") and not session_state.get("model_resolved"):
        output += f"\n### Model\n"
        output += f"**Status:** ⚠️ Unknown model\n"

    # Persona info
    if session_state.get("persona_name"):
        output += f"\n### Persona\n"
        output += f"**Name:** {session_state.get('persona_name')}\n"
        output += f"**Role:** {session_state.get('persona')}\n"
        output += f"**Persona Key:** {session_state.get('persona_key')}\n"
    else:
        output += f"**Persona:** {session_state.get('persona') or '(not set)'}\n"

    # Focus
    focus = session_state.get("focus")
    if focus:
        output += f"\n### Current Focus\n"
        output += f"{focus}\n"

    # Project context
    project_name = session_state.get("project_name")
    project_key = session_state.get("project_key")
    project_owner = session_state.get("project_owner")
    project_repo = session_state.get("project_repo")
    if project_name or project_key:
        output += f"\n### Project Context\n"
        if project_name:
            output += f"**Repository:** {project_name}\n"
        if project_owner and project_repo:
            output += f"**GitHub:** {project_owner}/{project_repo}\n"
        if project_key:
            output += f"**Entity Key:** {project_key}\n"

    # Affinity warning
    affinity_warning = session_state.get("affinity_warning")
    if affinity_warning:
        output += f"\n### Affinity Notice\n"
        output += f"{affinity_warning}\n"

    output += f"\n**Registered:** Yes\n"

    return [types.TextContent(type="text", text=output)]


async def update_my_identity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update the agent's identity - change agent ID, persona, model, and/or focus.

    This re-registers with the API under the new identity.

    Args:
        agent_id: New agent ID (optional, keeps current if not provided)
        persona: New persona role (optional, keeps current if not provided)
        model_key: New model key (optional, keeps current if not provided)
        focus: Current work focus (optional)
    """
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("update_my_identity")

    new_agent_id = arguments.get("agent_id")
    new_persona = arguments.get("persona")
    new_model_key = arguments.get("model_key")
    new_focus = arguments.get("focus")

    # Must provide at least one change
    if not new_agent_id and not new_persona and not new_model_key and new_focus is None:
        return [types.TextContent(
            type="text",
            text="No changes specified.\n\n"
                 "Provide `agent_id`, `persona`, `model_key`, and/or `focus` to update your identity."
        )]

    # Use current values if not changing
    agent_id = new_agent_id or session_state.get("agent_id") or config.agent_id
    persona = new_persona or session_state.get("persona") or config.persona
    model_key = new_model_key or session_state.get("model_key") or config.model_key
    focus = new_focus if new_focus is not None else session_state.get("focus") or config.focus
    client = session_state.get("client") or config.detected_client

    if not agent_id:
        return [types.TextContent(
            type="text",
            text="Cannot update identity: No agent_id available.\n\n"
                 "Either provide an agent_id or set CM_AGENT_ID environment variable."
        )]

    try:
        # Build registration payload
        registration_data = {
            "agent_id": agent_id,
            "capabilities": config.capabilities_list if hasattr(config, 'capabilities_list') else ["search", "create", "update"],
        }

        # Add optional fields
        if client:
            registration_data["client"] = client
        if model_key:
            registration_data["model_key"] = model_key
        if persona:
            # Look up persona_key from role
            try:
                personas_result = await _make_request(
                    config,
                    "GET",
                    "/personas/by-role/" + persona
                )
                if personas_result.get("success"):
                    persona_data = personas_result.get("data", {})
                    if persona_data.get("persona_key"):
                        registration_data["persona_key"] = persona_data.get("persona_key")
            except Exception:
                pass  # Persona lookup failed, continue without persona_key
        if focus:
            registration_data["focus"] = focus

        # Register with new identity
        result = await _make_request(
            config,
            "POST",
            "/agents/register",
            json=registration_data
        )

        if result.get("success"):
            agent_data = result.get("data", {})

            # Capture old values for comparison
            old_agent_id = session_state.get("agent_id")
            old_persona = session_state.get("persona")
            old_model_key = session_state.get("model_key")
            old_focus = session_state.get("focus")

            # Update session state with new identity
            session_state["agent_id"] = agent_id
            session_state["agent_key"] = agent_data.get("agent_key")
            session_state["persona"] = persona
            session_state["model_key"] = model_key
            session_state["focus"] = focus
            session_state["client"] = client
            session_state["registered"] = True

            # Store affinity warning if present
            if agent_data.get("affinity_warning"):
                session_state["affinity_warning"] = agent_data.get("affinity_warning")

            # Clear persona details - they'll need to be re-resolved
            session_state["persona_key"] = None
            session_state["persona_name"] = None
            session_state["model_name"] = None

            # Try to resolve new persona details
            if persona:
                try:
                    personas_result = await _make_request(
                        config,
                        "GET",
                        "/personas",
                        params={"role": persona}
                    )
                    if personas_result.get("success"):
                        personas = personas_result.get("data", {}).get("personas", [])
                        if personas:
                            p = personas[0]
                            session_state["persona_key"] = p.get("persona_key")
                            session_state["persona_name"] = p.get("name")
                except Exception:
                    pass  # Persona lookup failed, but identity update succeeded

            # Try to resolve model name
            if model_key:
                try:
                    model_result = await _make_request(
                        config,
                        "GET",
                        f"/models/{model_key}"
                    )
                    if model_result.get("success"):
                        model_data = model_result.get("data", {})
                        session_state["model_name"] = model_data.get("name")
                except Exception:
                    pass

            # Build response
            output = "## Identity Updated\n\n"

            if old_agent_id != agent_id:
                output += f"**Agent ID:** {old_agent_id} -> **{agent_id}**\n"
            else:
                output += f"**Agent ID:** {agent_id}\n"

            output += f"**Agent Key:** {agent_data.get('agent_key')}\n"
            output += f"**Client:** {client}\n"

            if old_model_key != model_key and model_key:
                output += f"**Model:** {old_model_key or '(none)'} -> **{model_key}**\n"
            elif model_key:
                output += f"**Model:** {model_key}\n"
                if session_state.get("model_name"):
                    output += f"**Model Name:** {session_state['model_name']}\n"

            if old_persona != persona:
                output += f"**Persona:** {old_persona or '(none)'} -> **{persona}**\n"
            else:
                output += f"**Persona:** {persona or '(not set)'}\n"

            if session_state.get("persona_name"):
                output += f"**Persona Name:** {session_state['persona_name']}\n"

            if old_focus != focus and focus:
                output += f"**Focus:** {focus}\n"
            elif focus:
                output += f"**Focus:** {focus}\n"

            # Show affinity warning if present
            if agent_data.get("affinity_warning"):
                output += f"\n**Note:** {agent_data.get('affinity_warning')}\n"

            output += f"\nRe-registered successfully\n"

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to update identity: {result.get('msg', 'Unknown error')}"
            )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error updating identity: {str(e)}"
        )]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "identify": identify,
    "get_my_identity": get_my_identity,
    "update_my_identity": update_my_identity,
}
