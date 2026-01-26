"""
GitHub Repository Tools

MCP tools for basic repository operations: sync, issues, commits, contributors.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cm_mcp.config import config
from cm_mcp.tools.utils import _make_request, is_guest_session, reject_guest_write

import mcp.types as types


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="sync_repository",
        description="""Sync a Repository entity with live data from GitHub.

USE THIS WHEN: You want to update or create a Repository entity with current stats from GitHub.

WHAT IT DOES:
- Fetches current metadata: stars, forks, open issues, language, size
- Creates a Repository entity if it doesn't exist (when create_if_missing=true)
- Updates existing Repository entities with fresh data

EXAMPLES:
- {"repository_url": "https://github.com/owner/repo"}
- {"repository_url": "owner/repo", "create_if_missing": false}

RETURNS: Formatted sync results with current GitHub stats and entity key.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL (e.g., https://github.com/owner/repo) or owner/repo format"},
                "create_if_missing": {"type": "boolean", "description": "Create Repository entity if it doesn't exist (default true)", "default": True}
            },
            "required": ["repository_url"]
        }
    ),
    types.Tool(
        name="get_repo_issues",
        description="""Get issues from a GitHub repository.

USE THIS WHEN: You need to see open issues, track bugs, or understand project priorities.

EXAMPLES:
- {"repository_url": "https://github.com/owner/repo"} → Open issues
- {"repository_url": "owner/repo", "state": "closed", "limit": 50}
- {"repository_url": "owner/repo", "labels": "bug,help wanted"}

RETURNS: Formatted list of issues with numbers, titles, authors, labels, and comment counts.
Issues and PRs are shown separately.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "state": {"type": "string", "description": "Issue state: 'open', 'closed', or 'all' (default 'open')", "default": "open"},
                "limit": {"type": "integer", "description": "Maximum issues to return (default 20)", "default": 20},
                "labels": {"type": "string", "description": "Comma-separated labels to filter by (optional)"}
            },
            "required": ["repository_url"]
        }
    ),
    types.Tool(
        name="get_repo_commits",
        description="""Get recent commits from a GitHub repository.

USE THIS WHEN: You need to understand recent changes, track AI co-authored commits, or analyze development activity.

FEATURES:
- Co-author detection (finds Claude and other AI collaborators)
- Commit stats (additions, deletions)
- Configurable time range

EXAMPLES:
- {"repository_url": "https://github.com/owner/repo"} → Last 7 days
- {"repository_url": "owner/repo", "days": 30, "limit": 50}
- {"repository_url": "owner/repo", "branch": "develop"}

RETURNS: Formatted commit list with SHA, message, author, stats, and co-authors.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "days": {"type": "integer", "description": "Number of days to look back (default 7)", "default": 7},
                "limit": {"type": "integer", "description": "Maximum commits to return (default 20)", "default": 20},
                "branch": {"type": "string", "description": "Branch to get commits from (optional, defaults to default branch)"}
            },
            "required": ["repository_url"]
        }
    ),
    types.Tool(
        name="get_repo_contributors",
        description="""Get contributors for a GitHub repository.

USE THIS WHEN: You need to understand who works on a project and their contribution levels.

EXAMPLES:
- {"repository_url": "https://github.com/owner/repo"}
- {"repository_url": "owner/repo", "limit": 50}

RETURNS: Contributors ranked by commit count with percentages.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "limit": {"type": "integer", "description": "Maximum contributors to return (default 20)", "default": 20}
            },
            "required": ["repository_url"]
        }
    ),
]


# ============================================================
# INTERNAL IMPLEMENTATIONS
# ============================================================

async def sync_repository(
    repository_url: str,
    create_if_missing: bool = True,
) -> str:
    """
    Sync a Repository entity with live data from GitHub.

    Fetches current metadata (stars, forks, issues, language, etc.) and updates
    the Repository entity in the knowledge graph.

    Args:
        repository_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        create_if_missing: If True, create the Repository entity if it doesn't exist

    Returns:
        Formatted string with sync results
    """
    try:
        # Import GitHub service
        from api.services.github import GitHubService

        gh = GitHubService()

        # Parse URL and get repository info
        owner, repo_name = gh.parse_repo_url(repository_url)
        repo_info = gh.get_repository(owner, repo_name)

        # Convert to entity properties
        properties = gh.to_entity_properties(repo_info)

        # Search for existing Repository entity by URL
        search_result = await _make_request(
            config,
            "GET",
            "/entities",
            params={"type": "Repository"}
        )

        existing_entity = None
        if search_result.get("success"):
            entities = search_result.get("data", {}).get("entities", [])
            for entity in entities:
                entity_url = entity.get("properties", {}).get("url", "")
                if repository_url in entity_url or entity_url in repository_url:
                    existing_entity = entity
                    break
                # Also check by name
                if entity.get("name") == repo_name:
                    existing_entity = entity
                    break

        if existing_entity:
            # Update existing entity
            entity_key = existing_entity.get("entity_key")
            update_result = await _make_request(
                config,
                "PUT",
                f"/entities/{entity_key}",
                json={"properties": properties}
            )

            if update_result.get("success"):
                return f"""## Repository Synced

**{repo_info.full_name}** updated successfully!

### Live Stats from GitHub
- **Language:** {repo_info.language}
- **Stars:** {repo_info.stars}
- **Forks:** {repo_info.forks}
- **Open Issues:** {repo_info.open_issues}
- **Size:** {repo_info.size_kb:,} KB
- **Visibility:** {"Private" if repo_info.is_private else "Public"}
- **Last Push:** {repo_info.pushed_at.strftime('%Y-%m-%d %H:%M') if repo_info.pushed_at else 'N/A'}

**Entity Key:** {entity_key}
**Synced At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
            else:
                return f"Failed to update repository: {update_result.get('msg')}"

        elif create_if_missing:
            # Create new Repository entity
            create_result = await _make_request(
                config,
                "POST",
                "/entities",
                json={
                    "entity_type": "Repository",
                    "name": repo_name,
                    "properties": properties
                }
            )

            if create_result.get("success"):
                entity = create_result.get("data", {}).get("entity", {})
                entity_key = entity.get("entity_key")

                return f"""## Repository Created & Synced

**{repo_info.full_name}** created successfully!

### Live Stats from GitHub
- **Language:** {repo_info.language}
- **Stars:** {repo_info.stars}
- **Forks:** {repo_info.forks}
- **Open Issues:** {repo_info.open_issues}
- **Size:** {repo_info.size_kb:,} KB
- **Visibility:** {"Private" if repo_info.is_private else "Public"}
- **Topics:** {', '.join(repo_info.topics) if repo_info.topics else 'None'}
- **Last Push:** {repo_info.pushed_at.strftime('%Y-%m-%d %H:%M') if repo_info.pushed_at else 'N/A'}

**Entity Key:** {entity_key}
**Synced At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
            else:
                return f"Failed to create repository: {create_result.get('msg')}"

        else:
            return f"Repository entity not found for {repository_url} and create_if_missing is False"

    except ImportError as e:
        return f"GitHub integration not available: {e}. Make sure PyGithub is installed and GITHUB_PAT is set."
    except Exception as e:
        return f"Error syncing repository: {e}"


async def get_repo_issues(
    repository_url: str,
    state: str = "open",
    limit: int = 20,
    labels: Optional[str] = None,
) -> str:
    """
    Get issues from a GitHub repository.

    Args:
        repository_url: GitHub repository URL
        state: Issue state filter ('open', 'closed', 'all')
        limit: Maximum number of issues to return (default 20)
        labels: Comma-separated list of labels to filter by (optional)

    Returns:
        Formatted string with issues list
    """
    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        label_list = [l.strip() for l in labels.split(",")] if labels else None
        issues = gh.get_issues(owner, repo_name, state=state, limit=limit, labels=label_list)

        if not issues:
            return f"No {state} issues found for {owner}/{repo_name}"

        # Separate issues and PRs
        actual_issues = [i for i in issues if not i.is_pull_request]
        pull_requests = [i for i in issues if i.is_pull_request]

        output = f"## Issues for {owner}/{repo_name}\n\n"
        output += f"**State:** {state} | **Total:** {len(issues)}\n\n"

        if actual_issues:
            output += "### Issues\n\n"
            for issue in actual_issues:
                labels_str = f" `{', '.join(issue.labels)}`" if issue.labels else ""
                assignees_str = f" → {', '.join(issue.assignees)}" if issue.assignees else ""
                output += f"- **#{issue.number}** [{issue.title}]({issue.url}){labels_str}{assignees_str}\n"
                output += f"  - Created: {issue.created_at.strftime('%Y-%m-%d')} by @{issue.author}"
                if issue.comments_count > 0:
                    output += f" | {issue.comments_count} comments"
                output += "\n"

        if pull_requests:
            output += "\n### Pull Requests\n\n"
            for pr in pull_requests:
                labels_str = f" `{', '.join(pr.labels)}`" if pr.labels else ""
                output += f"- **#{pr.number}** [{pr.title}]({pr.url}){labels_str}\n"
                output += f"  - Created: {pr.created_at.strftime('%Y-%m-%d')} by @{pr.author}\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error fetching issues: {e}"


async def get_repo_commits(
    repository_url: str,
    days: int = 7,
    limit: int = 20,
    branch: Optional[str] = None,
) -> str:
    """
    Get recent commits from a GitHub repository.

    Args:
        repository_url: GitHub repository URL
        days: Number of days to look back (default 7)
        limit: Maximum number of commits to return (default 20)
        branch: Branch to get commits from (optional, defaults to default branch)

    Returns:
        Formatted string with commits list
    """
    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        since = datetime.now(timezone.utc) - timedelta(days=days)
        commits = gh.get_commits(owner, repo_name, since=since, limit=limit, branch=branch)

        if not commits:
            return f"No commits found in the last {days} days for {owner}/{repo_name}"

        # Calculate stats
        total_additions = sum(c.additions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        authors = set(c.author_name for c in commits)

        # Count AI co-authored commits
        ai_commits = [c for c in commits if any("claude" in a.lower() or "anthropic" in a.lower() for a in c.co_authors)]

        output = f"## Commits for {owner}/{repo_name}\n\n"
        output += f"**Period:** Last {days} days | **Commits:** {len(commits)} | **Authors:** {len(authors)}\n"
        output += f"**Changes:** +{total_additions:,} / -{total_deletions:,}\n"

        if ai_commits:
            output += f"**AI Co-Authored:** {len(ai_commits)} commits\n"

        output += "\n### Recent Commits\n\n"

        for commit in commits:
            # First line of commit message
            message_line = commit.message.split('\n')[0][:80]

            # Co-author indicator
            co_author_str = ""
            if commit.co_authors:
                co_author_str = f" {', '.join(commit.co_authors)}"

            output += f"- **{commit.sha[:7]}** {message_line}\n"
            output += f"  - {commit.author_name} | {commit.date.strftime('%Y-%m-%d %H:%M')}"
            output += f" | +{commit.additions}/-{commit.deletions}"
            if co_author_str:
                output += co_author_str
            output += "\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error fetching commits: {e}"


async def get_repo_contributors(
    repository_url: str,
    limit: int = 20,
) -> str:
    """
    Get contributors for a GitHub repository.

    Args:
        repository_url: GitHub repository URL
        limit: Maximum number of contributors to return (default 20)

    Returns:
        Formatted string with contributors list
    """
    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        contributors = gh.get_contributors(owner, repo_name, limit=limit)

        if not contributors:
            return f"No contributors found for {owner}/{repo_name}"

        total_commits = sum(c.commits for c in contributors)

        output = f"## Contributors for {owner}/{repo_name}\n\n"
        output += f"**Total Contributors:** {len(contributors)} | **Total Commits:** {total_commits:,}\n\n"

        for i, contrib in enumerate(contributors, 1):
            percentage = (contrib.commits / total_commits * 100) if total_commits > 0 else 0
            output += f"{i}. **{contrib.name}** (@{contrib.login}) - {contrib.commits} commits ({percentage:.1f}%)\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error fetching contributors: {e}"


# ============================================================
# MCP HANDLER WRAPPERS
# ============================================================

async def _handle_sync_repository(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for sync_repository."""
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("sync_repository")

    text = await sync_repository(
        arguments.get("repository_url"),
        arguments.get("create_if_missing", True)
    )
    return [types.TextContent(type="text", text=text)]


async def _handle_get_repo_issues(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for get_repo_issues."""
    text = await get_repo_issues(
        arguments.get("repository_url"),
        arguments.get("state", "open"),
        arguments.get("limit", 20),
        arguments.get("labels")
    )
    return [types.TextContent(type="text", text=text)]


async def _handle_get_repo_commits(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for get_repo_commits."""
    text = await get_repo_commits(
        arguments.get("repository_url"),
        arguments.get("days", 7),
        arguments.get("limit", 20),
        arguments.get("branch")
    )
    return [types.TextContent(type="text", text=text)]


async def _handle_get_repo_contributors(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for get_repo_contributors."""
    text = await get_repo_contributors(
        arguments.get("repository_url"),
        arguments.get("limit", 20)
    )
    return [types.TextContent(type="text", text=text)]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "sync_repository": _handle_sync_repository,
    "get_repo_issues": _handle_get_repo_issues,
    "get_repo_commits": _handle_get_repo_commits,
    "get_repo_contributors": _handle_get_repo_contributors,
}
