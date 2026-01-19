"""
GitHub Sync Tools

MCP tools for syncing repository history (commits and issues) as entities.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cm_mcp.config import config
from cm_mcp.tools.utils import _make_request

import mcp.types as types


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="sync_repository_history",
        description="""Sync full repository history (commits and issues) as entities.

USE THIS WHEN: You want to do a complete backfill of a repository's commits and issues into the knowledge graph.

This performs a full historical sync, creating Commit and Issue entities with:
- BELONGS_TO relationships to the Repository
- CO_AUTHORED_BY relationships for AI co-authors (Claude, Copilot, etc.)

WORKFLOW: After you make commits to a tracked repository:
1. git add / git commit / git push
2. sync_repository_updates() to capture your work
3. link_work_item(commit_key, idea_key, "IMPLEMENTS") to connect to Ideas
4. Update Idea status if work is complete

EXAMPLES:
- {"repository_url": "owner/repo"} → Sync both commits and issues
- {"repository_url": "owner/repo", "entity_types": ["commits"], "commits_limit": 1000}

RETURNS: Summary of created/updated entities.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "entity_types": {"type": "array", "items": {"type": "string"}, "description": "Types to sync: ['commits', 'issues']. Defaults to both."},
                "commits_limit": {"type": "integer", "description": "Maximum commits to sync (default 500)", "default": 500},
                "issues_limit": {"type": "integer", "description": "Maximum issues to sync (default 200)", "default": 200}
            },
            "required": ["repository_url"]
        }
    ),
    types.Tool(
        name="sync_repository_updates",
        description="""Sync recent repository updates (incremental sync).

USE THIS WHEN: You want to capture recent commits and issues since the last sync.

IMPORTANT: Call this after making commits to capture your work in the knowledge graph!

WORKFLOW REMINDER:
1. git add / git commit / git push
2. sync_repository_updates(repo, ["commits"])
3. link_work_item(commit_key, idea_key, "IMPLEMENTS") if implementing an Idea
4. Update Idea status if work is complete

EXAMPLES:
- {"repository_url": "owner/repo"} → Sync all updates
- {"repository_url": "owner/repo", "entity_types": ["commits"]} → Just commits

RETURNS: Summary of new/updated entities with commit keys for linking.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "entity_types": {"type": "array", "items": {"type": "string"}, "description": "Types to sync: ['commits', 'issues']. Defaults to both."}
            },
            "required": ["repository_url"]
        }
    ),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def _sync_commits_via_api(
    gh,
    owner: str,
    repo_name: str,
    repository_entity_key: str,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> dict:
    """
    Sync commits as entities using HTTP API calls (no Flask context needed).
    """
    commits = gh.get_commits(owner, repo_name, since=since, limit=limit)

    created = 0
    updated = 0
    commit_keys = []

    for commit_info in commits:
        # Check if Commit entity already exists by SHA
        search_result = await _make_request(
            config, "GET", "/entities",
            params={"type": "Commit", "search": commit_info.sha[:12]}
        )

        existing_entity = None
        if search_result.get("success"):
            for e in search_result.get("data", {}).get("entities", []):
                if e.get("properties", {}).get("sha") == commit_info.sha:
                    existing_entity = e
                    break

        properties = gh.to_commit_entity_properties(commit_info)

        if existing_entity:
            # Update existing
            await _make_request(
                config, "PUT", f"/entities/{existing_entity['entity_key']}",
                json={"properties": properties}
            )
            updated += 1
            commit_keys.append(existing_entity['entity_key'])
        else:
            # Create new Commit entity
            title = properties['title'][:80] if properties.get('title') else commit_info.sha[:7]
            create_result = await _make_request(
                config, "POST", "/entities",
                json={
                    "name": title,
                    "entity_type": "Commit",
                    "properties": properties,
                    "source": f"github:{owner}/{repo_name}",
                }
            )

            if create_result.get("success"):
                new_entity = create_result.get("data", {}).get("entity", {})
                entity_key = new_entity.get("entity_key")
                commit_keys.append(entity_key)

                # Create BELONGS_TO relationship to Repository
                await _make_request(
                    config, "POST", "/relationships",
                    json={
                        "from_entity_key": entity_key,
                        "to_entity_key": repository_entity_key,
                        "relationship_type": "BELONGS_TO",
                    }
                )

                # Detect AI co-authors and create relationships
                for coauthor in commit_info.co_authors:
                    coauthor_lower = coauthor.lower()
                    ai_type = None
                    if 'claude' in coauthor_lower:
                        ai_type = 'Claude'
                    elif 'copilot' in coauthor_lower or 'github' in coauthor_lower:
                        ai_type = 'GitHub Copilot'
                    elif 'gpt' in coauthor_lower or 'openai' in coauthor_lower:
                        ai_type = 'GPT'
                    elif 'gemini' in coauthor_lower or 'google' in coauthor_lower:
                        ai_type = 'Gemini'

                    if ai_type:
                        # Find or create Agent entity
                        agent_search = await _make_request(
                            config, "GET", "/entities",
                            params={"type": "Agent", "search": ai_type}
                        )
                        agent_key = None
                        if agent_search.get("success"):
                            for a in agent_search.get("data", {}).get("entities", []):
                                if a.get("name") == ai_type:
                                    agent_key = a.get("entity_key")
                                    break

                        if not agent_key:
                            agent_result = await _make_request(
                                config, "POST", "/entities",
                                json={
                                    "name": ai_type,
                                    "entity_type": "Agent",
                                    "properties": {"type": "ai", "provider": ai_type.lower()},
                                    "source": "system",
                                }
                            )
                            if agent_result.get("success"):
                                agent_key = agent_result.get("data", {}).get("entity", {}).get("entity_key")

                        if agent_key:
                            await _make_request(
                                config, "POST", "/relationships",
                                json={
                                    "from_entity_key": entity_key,
                                    "to_entity_key": agent_key,
                                    "relationship_type": "CO_AUTHORED_BY",
                                }
                            )

                created += 1

    return {
        'created': created,
        'updated': updated,
        'total': len(commits),
        'commit_keys': commit_keys,
    }


async def _sync_issues_via_api(
    gh,
    owner: str,
    repo_name: str,
    repository_entity_key: str,
    state: str = "all",
    limit: int = 100,
) -> dict:
    """
    Sync issues as entities using HTTP API calls (no Flask context needed).
    """
    issues = gh.get_issues(owner, repo_name, state=state, limit=limit)

    created = 0
    updated = 0
    skipped = 0

    for issue_info in issues:
        # Skip pull requests
        if issue_info.is_pull_request:
            skipped += 1
            continue

        # Check if Issue entity already exists
        search_result = await _make_request(
            config, "GET", "/entities",
            params={"type": "Issue", "search": f"#{issue_info.number}"}
        )

        existing_entity = None
        if search_result.get("success"):
            for e in search_result.get("data", {}).get("entities", []):
                if e.get("properties", {}).get("github_number") == issue_info.number:
                    existing_entity = e
                    break

        properties = gh.to_issue_entity_properties(issue_info)

        if existing_entity:
            # Update existing
            await _make_request(
                config, "PUT", f"/entities/{existing_entity['entity_key']}",
                json={"properties": properties}
            )
            updated += 1
        else:
            # Create new Issue entity
            create_result = await _make_request(
                config, "POST", "/entities",
                json={
                    "name": f"#{issue_info.number}: {issue_info.title[:60]}",
                    "entity_type": "Issue",
                    "properties": properties,
                    "source": f"github:{owner}/{repo_name}",
                }
            )

            if create_result.get("success"):
                entity_key = create_result.get("data", {}).get("entity", {}).get("entity_key")

                # Create BELONGS_TO relationship
                await _make_request(
                    config, "POST", "/relationships",
                    json={
                        "from_entity_key": entity_key,
                        "to_entity_key": repository_entity_key,
                        "relationship_type": "BELONGS_TO",
                    }
                )
                created += 1

    return {
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'total': len(issues),
    }


# ============================================================
# INTERNAL IMPLEMENTATIONS
# ============================================================

async def sync_repository_history(
    repository_url: str,
    entity_types: list[str] = None,
    commits_limit: int = 500,
    issues_limit: int = 200,
) -> str:
    """
    Sync full repository history (commits and issues) as entities.

    This performs a full historical backfill, creating Commit and Issue entities
    for all items in the repository. Use sync_repository_updates for incremental syncs.

    IMPORTANT: When you commit code to a repository tracked in CM, always follow up with
    sync_repository_updates() to capture your work in the knowledge graph.

    Args:
        repository_url: GitHub repository URL
        entity_types: List of types to sync - ["commits", "issues"]. Defaults to both.
        commits_limit: Maximum commits to sync (default 500)
        issues_limit: Maximum issues to sync (default 200)

    Returns:
        Formatted string with sync results
    """
    if entity_types is None:
        entity_types = ["commits", "issues"]

    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        # First, ensure Repository entity exists
        search_result = await _make_request(
            config,
            "GET",
            "/entities",
            params={"type": "Repository", "search": repo_name}
        )

        repository_entity_key = None
        if search_result.get("success"):
            entities = search_result.get("data", {}).get("entities", [])
            for entity in entities:
                entity_url = entity.get("properties", {}).get("url", "")
                if f"{owner}/{repo_name}" in entity_url or entity.get("name") == repo_name:
                    repository_entity_key = entity.get("entity_key")
                    break

        if not repository_entity_key:
            return f"Repository entity not found for {owner}/{repo_name}. Run sync_repository first to create it."

        output = f"## Repository History Sync: {owner}/{repo_name}\n\n"
        results = {}

        # Sync commits via API
        if "commits" in entity_types:
            commit_result = await _sync_commits_via_api(
                gh, owner, repo_name,
                repository_entity_key,
                since=None,
                limit=commits_limit
            )
            results["commits"] = commit_result
            output += f"### Commits\n"
            output += f"- **Created:** {commit_result['created']}\n"
            output += f"- **Updated:** {commit_result['updated']}\n"
            output += f"- **Total fetched:** {commit_result['total']}\n\n"

        # Sync issues via API
        if "issues" in entity_types:
            issue_result = await _sync_issues_via_api(
                gh, owner, repo_name,
                repository_entity_key,
                state="all",
                limit=issues_limit
            )
            results["issues"] = issue_result
            output += f"### Issues\n"
            output += f"- **Created:** {issue_result['created']}\n"
            output += f"- **Updated:** {issue_result['updated']}\n"
            output += f"- **Skipped (PRs):** {issue_result['skipped']}\n"
            output += f"- **Total fetched:** {issue_result['total']}\n\n"

        # Update Repository entity with sync tracking
        now = datetime.now(timezone.utc).isoformat()
        sync_props = {"last_synced_at": now}
        if "commits" in entity_types:
            sync_props["commits_synced_until"] = now
        if "issues" in entity_types:
            sync_props["issues_synced_until"] = now

        await _make_request(
            config,
            "PUT",
            f"/entities/{repository_entity_key}",
            json={"properties": sync_props}
        )

        output += f"**Repository Entity:** {repository_entity_key}\n"
        output += f"**Synced At:** {now}\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error syncing repository history: {e}"


async def sync_repository_updates(
    repository_url: str,
    entity_types: list[str] = None,
) -> str:
    """
    Sync recent repository updates (incremental sync).

    Only fetches commits and issues since the last sync. Use this after making
    commits to capture your work in the knowledge graph.

    WORKFLOW REMINDER: When you commit code to a tracked repository:
    1. git add / git commit / git push
    2. sync_repository_updates(repo, ["commits"])
    3. link_work_item(commit_key, idea_key, "IMPLEMENTS") if applicable
    4. Update Idea status if work is complete

    Args:
        repository_url: GitHub repository URL
        entity_types: List of types to sync - ["commits", "issues"]. Defaults to both.

    Returns:
        Formatted string with sync results
    """
    if entity_types is None:
        entity_types = ["commits", "issues"]

    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        # Find Repository entity
        search_result = await _make_request(
            config,
            "GET",
            "/entities",
            params={"type": "Repository", "search": repo_name}
        )

        repository_entity = None
        if search_result.get("success"):
            entities = search_result.get("data", {}).get("entities", [])
            for entity in entities:
                entity_url = entity.get("properties", {}).get("url", "")
                if f"{owner}/{repo_name}" in entity_url or entity.get("name") == repo_name:
                    repository_entity = entity
                    break

        if not repository_entity:
            return f"Repository entity not found for {owner}/{repo_name}. Run sync_repository first."

        repository_entity_key = repository_entity.get("entity_key")
        props = repository_entity.get("properties", {})

        output = f"## Repository Updates Sync: {owner}/{repo_name}\n\n"
        results = {}

        # Sync commits (incremental) via API
        if "commits" in entity_types:
            commits_since = props.get("commits_synced_until")
            since_dt = None
            if commits_since:
                since_dt = datetime.fromisoformat(commits_since.replace('Z', '+00:00'))
                output += f"**Commits since:** {commits_since}\n"
            else:
                # Default to last 7 days if never synced
                since_dt = datetime.now(timezone.utc) - timedelta(days=7)
                output += f"**Commits since:** Last 7 days (first sync)\n"

            commit_result = await _sync_commits_via_api(
                gh, owner, repo_name,
                repository_entity_key,
                since=since_dt,
                limit=100
            )
            results["commits"] = commit_result
            output += f"\n### Commits\n"
            output += f"- **Created:** {commit_result['created']}\n"
            output += f"- **Updated:** {commit_result['updated']}\n"
            output += f"- **Total fetched:** {commit_result['total']}\n"

            # Show commit keys for linking
            if commit_result['commit_keys']:
                output += f"- **New commit keys:** {', '.join(commit_result['commit_keys'][:5])}"
                if len(commit_result['commit_keys']) > 5:
                    output += f" (+{len(commit_result['commit_keys']) - 5} more)"
                output += "\n"

        # Sync issues (incremental) via API
        if "issues" in entity_types:
            output += f"\n### Issues\n"
            issue_result = await _sync_issues_via_api(
                gh, owner, repo_name,
                repository_entity_key,
                state="all",
                limit=50
            )
            results["issues"] = issue_result
            output += f"- **Created:** {issue_result['created']}\n"
            output += f"- **Updated:** {issue_result['updated']}\n"
            output += f"- **Skipped (PRs):** {issue_result['skipped']}\n"

        # Update Repository entity with sync tracking
        now = datetime.now(timezone.utc).isoformat()
        sync_props = {"last_synced_at": now}
        if "commits" in entity_types:
            sync_props["commits_synced_until"] = now
        if "issues" in entity_types:
            sync_props["issues_synced_until"] = now

        await _make_request(
            config,
            "PUT",
            f"/entities/{repository_entity_key}",
            json={"properties": sync_props}
        )

        output += f"\n**Synced At:** {now}\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error syncing repository updates: {e}"


# ============================================================
# MCP HANDLER WRAPPERS
# ============================================================

async def _handle_sync_repository_history(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for sync_repository_history."""
    text = await sync_repository_history(
        arguments.get("repository_url"),
        arguments.get("entity_types"),
        arguments.get("commits_limit", 500),
        arguments.get("issues_limit", 200)
    )
    return [types.TextContent(type="text", text=text)]


async def _handle_sync_repository_updates(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for sync_repository_updates."""
    text = await sync_repository_updates(
        arguments.get("repository_url"),
        arguments.get("entity_types")
    )
    return [types.TextContent(type="text", text=text)]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "sync_repository_history": _handle_sync_repository_history,
    "sync_repository_updates": _handle_sync_repository_updates,
}
