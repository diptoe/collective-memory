"""
Agent Tools

MCP tools for agent collaboration in the Collective Memory (CM) knowledge graph.
"""

import mcp.types as types
import subprocess
import re
from typing import Any

from .utils import _make_request


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
                    "client": c.get("client"),
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
    if not hasattr(config, 'pat') or not config.pat:
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
        # Detect project from git remote (auto-detection)
        git_project = _detect_project_from_git()
        detected_project_key = None
        detected_project_name = None

        if git_project:
            # Try to sync Repository entity and find parent Project entity
            repo_entity_key = None
            project_entity_key = None

            try:
                # Step 1: Sync Repository entity from GitHub
                repo_url = f"https://github.com/{git_project['owner']}/{git_project['repo']}"
                sync_result = await _make_request(
                    config,
                    "POST",
                    "/github/sync",
                    json={"repository_url": repo_url}
                )
                if sync_result.get("success"):
                    sync_data = sync_result.get("data", {})
                    entity_data = sync_data.get("entity", {})
                    repo_entity_key = entity_data.get("entity_key")
                    detected_project_name = entity_data.get("name") or git_project['repo']

                # Step 2: Search for a Project entity with matching name
                # Project is the parent entity type for Repository
                repo_name = git_project['repo']
                search_result = await _make_request(
                    config,
                    "GET",
                    "/entities/search",
                    params={"query": repo_name, "entity_type": "Project", "limit": "5"}
                )
                if search_result.get("success"):
                    entities = search_result.get("data", {}).get("entities", [])
                    # Look for exact or close match
                    for entity in entities:
                        entity_name = entity.get("name", "").lower()
                        if entity_name == repo_name.lower() or entity_name == repo_name.lower().replace("-", " "):
                            project_entity_key = entity.get("entity_key")
                            detected_project_name = entity.get("name")
                            break

                # Step 3: Use Project entity_key if found, otherwise use Repository entity_key
                if project_entity_key:
                    detected_project_key = project_entity_key
                    git_project['entity_type'] = 'Project'
                elif repo_entity_key:
                    detected_project_key = repo_entity_key
                    git_project['entity_type'] = 'Repository'

                # Store both for reference
                git_project['repo_entity_key'] = repo_entity_key
                git_project['project_entity_key'] = project_entity_key

            except Exception as e:
                # If sync fails, just use repo name as project name
                detected_project_name = git_project['repo']
                git_project['sync_error'] = str(e)

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
        # We need this for: user initials, team resolution, and domain context
        user_initials = None
        resolved_team_key = None
        resolved_team_name = None
        user_data = {}
        teams = []
        available_scopes = []
        default_scope = {}

        if hasattr(config, 'pat') and config.pat:
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
                    elif explicit_team_slug:
                        team = next((t for t in teams if t.get('slug') == explicit_team_slug), None)
                        if team:
                            resolved_team_key = team.get('team_key')
                            resolved_team_name = team.get('name')
                    elif teams and agent_id:
                        # Auto-detect from agent_id pattern matching team slugs or names
                        agent_id_lower = agent_id.lower().replace('-', ' ').replace('_', ' ')
                        for t in teams:
                            team_slug = t.get('slug', '').lower().replace('-', ' ').replace('_', ' ')
                            team_name = t.get('name', '').lower()
                            if team_slug and team_slug in agent_id_lower:
                                resolved_team_key = t.get('team_key')
                                resolved_team_name = t.get('name')
                                break
                            elif team_name and team_name in agent_id_lower:
                                resolved_team_key = t.get('team_key')
                                resolved_team_name = t.get('name')
                                break
            except Exception:
                pass  # Continue without user info

        # Auto-suffix agent_id with user initials (if not already present)
        if user_initials and agent_id:
            if not agent_id.endswith(f'-{user_initials}'):
                # Check if agent_id already has a 2-char alphabetic suffix
                parts = agent_id.rsplit('-', 1)
                if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isalpha():
                    # Replace existing 2-char suffix with user initials
                    agent_id = f"{parts[0]}-{user_initials}"
                else:
                    # Append user initials
                    agent_id = f"{agent_id}-{user_initials}"

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
            session_state["registered"] = True

            # Store affinity warning if present
            if agent_data.get("affinity_warning"):
                session_state["affinity_warning"] = agent_data.get("affinity_warning")

            # Store project info in session_state (from git detection)
            if git_project:
                session_state["project_owner"] = git_project.get('owner')
                session_state["project_repo"] = git_project.get('repo')
            if detected_project_key:
                session_state["project_key"] = detected_project_key
            if detected_project_name:
                session_state["project_name"] = detected_project_name

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
                # Determine detection method for display
                if explicit_team_key:
                    session_state["active_team_method"] = "explicit_team_key"
                elif explicit_team_slug:
                    session_state["active_team_method"] = "explicit_team_slug"
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

            output = "# Identity Confirmed\n\n"
            output += f"Welcome to Collective Memory (CM)!\n\n"

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
            if detected_project_name or detected_project_key or git_project:
                output += "\n## Project Context\n"
                if git_project:
                    output += f"**GitHub:** {git_project.get('owner')}/{git_project.get('repo')}\n"
                if detected_project_name:
                    output += f"**Name:** {detected_project_name}\n"
                if detected_project_key:
                    entity_type = git_project.get('entity_type', 'Unknown') if git_project else 'Unknown'
                    output += f"**Entity:** {detected_project_key} ({entity_type})\n"
                # Show both entity keys if different
                if git_project:
                    repo_key = git_project.get('repo_entity_key')
                    proj_key = git_project.get('project_entity_key')
                    if repo_key and proj_key and repo_key != proj_key:
                        output += f"**Repository Entity:** {repo_key}\n"
                        output += f"**Project Entity:** {proj_key}\n"
                    if git_project.get('sync_error'):
                        output += f"**Note:** {git_project.get('sync_error')}\n"

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


async def list_agents(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List all registered AI agents in the collaboration.

    Args:
        active_only: Only show active agents (default True)
        client: Filter by client type (optional)
    """
    active_only = arguments.get("active_only", True)
    client_filter = arguments.get("client")

    try:
        params = {"active_only": str(active_only).lower()}
        if client_filter:
            params["client"] = client_filter
        result = await _make_request(config, "GET", "/agents", params=params)

        if result.get("success"):
            agents = result.get("data", {}).get("agents", [])
            if agents:
                # Mark current agent
                current_id = session_state.get("agent_id")

                output = f"## Collaborating Agents ({len(agents)})\n\n"
                for a in agents:
                    is_me = a.get("agent_id") == current_id
                    marker = " ← (you)" if is_me else ""
                    status = "🟢" if a.get("is_active") else "⚪"
                    focused = " 🎯" if a.get("is_focused") else ""

                    output += f"{status} **{a.get('agent_id')}**{focused}{marker}\n"

                    # Show client if available
                    if a.get("client"):
                        output += f"   Client: {a.get('client')}\n"

                    # Show persona name (from expanded object) or legacy role
                    persona = a.get("persona")
                    if persona and isinstance(persona, dict) and persona.get("name"):
                        output += f"   Persona: {persona.get('name')} ({persona.get('role', '')})\n"
                    elif a.get("persona_key"):
                        # Fallback to key if persona not expanded
                        output += f"   Persona: {a.get('persona_key')}\n"
                    elif a.get("role"):
                        output += f"   Role: {a.get('role')}\n"

                    # Show model name if available
                    model = a.get("model")
                    if model and isinstance(model, dict) and model.get("name"):
                        output += f"   Model: {model.get('name')}\n"

                    # Show focus if set
                    if a.get("focus"):
                        output += f"   Focus: {a.get('focus')}\n"

                    output += f"   Key: {a.get('agent_key')}\n\n"
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(type="text", text="No agents registered yet.")]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Unknown error')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing agents: {str(e)}")]


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


async def list_my_scopes(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List all scopes the current agent can access.

    Returns available scopes (domain, team, personal) with descriptions
    and shows the current default scope.
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered. Use `identify` to register with Collective Memory first."
        )]

    available_scopes = session_state.get("available_scopes", [])
    default_scope = session_state.get("default_scope", {})
    active_team = session_state.get("active_team_key")

    output = "# My Available Scopes\n\n"

    if not available_scopes:
        output += "No scopes available. Try re-identifying to refresh scope data.\n"
        return [types.TextContent(type="text", text=output)]

    # Group scopes by type
    domain_scopes = [s for s in available_scopes if s.get('scope_type') == 'domain']
    team_scopes = [s for s in available_scopes if s.get('scope_type') == 'team']
    user_scopes = [s for s in available_scopes if s.get('scope_type') == 'user']

    if domain_scopes:
        output += "## Domain Scopes\n"
        for s in domain_scopes:
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            default_marker = " ← **default**" if is_default else ""
            output += f"- **{s.get('name')}** ({s.get('access_level')}){default_marker}\n"
            output += f"  Key: `{s.get('scope_key')}`\n"
        output += "\n"

    if team_scopes:
        output += "## Team Scopes\n"
        for s in team_scopes:
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            is_active = s.get('scope_key') == active_team
            default_marker = " ← **default**" if is_default else ""
            active_marker = " 🎯 **active**" if is_active else ""
            output += f"- **{s.get('name')}** ({s.get('access_level')}){default_marker}{active_marker}\n"
            output += f"  Key: `{s.get('scope_key')}`\n"
        output += "\n"

    if user_scopes:
        output += "## Personal Scope\n"
        for s in user_scopes:
            is_default = (
                s.get('scope_type') == default_scope.get('scope_type') and
                s.get('scope_key') == default_scope.get('scope_key')
            )
            default_marker = " ← **default**" if is_default else ""
            output += f"- **{s.get('name')}** ({s.get('access_level')}){default_marker}\n"
            output += f"  Key: `{s.get('scope_key')}`\n"
        output += "\n"

    output += "---\n\n"
    output += "## Usage\n"
    output += "Use `scope_type` and `scope_key` in `create_entity` to target specific scopes:\n"
    output += "```\n"
    output += 'create_entity(\n'
    output += '    name="My Entity",\n'
    output += '    entity_type="Concept",\n'
    output += '    scope_type="team",\n'
    output += '    scope_key="team-xxx"\n'
    output += ')\n'
    output += "```\n\n"
    output += "Use `set_active_team` to change your default scope for new entities.\n"

    return [types.TextContent(type="text", text=output)]


async def set_active_team(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Set active team for this session.

    New entities will default to this team's scope.

    Args:
        team_key: Team key to set as active (optional - omit to clear active team)
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered. Use `identify` to register with Collective Memory first."
        )]

    team_key = arguments.get("team_key")
    teams = session_state.get("teams", [])

    if team_key:
        # Validate team access
        team = next((t for t in teams if t.get('team_key') == team_key), None)
        if not team:
            output = f"Error: Not a member of team `{team_key}`\n\n"
            if teams:
                output += "Your teams:\n"
                for t in teams:
                    output += f"- **{t.get('name')}** - `{t.get('team_key')}`\n"
            else:
                output += "You are not a member of any teams.\n"
            return [types.TextContent(type="text", text=output)]

        # Set active team
        session_state["active_team_key"] = team_key

        # Update default scope to use this team
        session_state["default_scope"] = {
            "scope_type": "team",
            "scope_key": team_key
        }

        output = f"# Active Team Set\n\n"
        output += f"**Team:** {team.get('name')}\n"
        output += f"**Key:** `{team_key}`\n"
        output += f"**Your Role:** {team.get('role')}\n\n"
        output += "New entities will be created in this team's scope by default.\n"
    else:
        # Clear active team
        previous = session_state.pop("active_team_key", None)

        # Reset default scope
        domain_key = session_state.get("domain_key")
        if domain_key:
            session_state["default_scope"] = {
                "scope_type": "domain",
                "scope_key": domain_key
            }
        else:
            user_key = session_state.get("user_key")
            session_state["default_scope"] = {
                "scope_type": "user",
                "scope_key": user_key
            }

        output = "# Active Team Cleared\n\n"
        if previous:
            output += f"Previously active team `{previous}` has been cleared.\n\n"
        output += "Default scope has been reset to: "
        default_scope = session_state.get("default_scope", {})
        output += f"{default_scope.get('scope_type')} ({default_scope.get('scope_key')})\n"

    return [types.TextContent(type="text", text=output)]


async def list_teams(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    List teams the current user is a member of.

    Returns team names, keys, descriptions, and the user's role in each team.
    """
    if not session_state.get("registered"):
        return [types.TextContent(
            type="text",
            text="Not registered. Use `identify` to register with Collective Memory first."
        )]

    teams = session_state.get("teams", [])
    active_team = session_state.get("active_team_key")

    output = "# My Teams\n\n"

    if not teams:
        output += "You are not a member of any teams.\n\n"
        output += "Teams are managed by domain administrators.\n"
        return [types.TextContent(type="text", text=output)]

    output += f"You are a member of **{len(teams)}** team(s):\n\n"

    for t in teams:
        is_active = t.get('team_key') == active_team
        active_marker = " 🎯 **active**" if is_active else ""

        output += f"## {t.get('name')}{active_marker}\n"
        output += f"**Key:** `{t.get('team_key')}`\n"
        output += f"**Your Role:** {t.get('role')}\n"
        if t.get('description'):
            output += f"**Description:** {t.get('description')}\n"
        output += "\n"

    output += "---\n\n"
    output += "Use `set_active_team(team_key=\"...\")` to set your active team.\n"
    output += "Entities created without explicit scope will use the active team's scope.\n"

    return [types.TextContent(type="text", text=output)]
