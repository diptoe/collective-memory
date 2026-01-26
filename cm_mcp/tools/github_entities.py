"""
GitHub Entity Tools

MCP tools for creating and linking GitHub entities (commits, issues, work items).
"""

import os
import sys
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
        name="create_commit_entity",
        description="""Create a Commit entity for a specific commit SHA.

USE THIS WHEN: You need to manually create a Commit entity and optionally link it to an Idea.

EXAMPLES:
- {"repository_url": "owner/repo", "sha": "abc1234"}
- {"repository_url": "owner/repo", "sha": "abc1234", "implements": "ent-idea-key"}

RETURNS: Created entity info with entity_key for further linking.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "sha": {"type": "string", "description": "Commit SHA (full or abbreviated)"},
                "implements": {"type": "string", "description": "Optional entity_key of an Idea or Issue this commit implements"}
            },
            "required": ["repository_url", "sha"]
        }
    ),
    types.Tool(
        name="create_issue_entity",
        description="""Create an Issue entity for a specific GitHub issue number.

USE THIS WHEN: You need to manually create an Issue entity and optionally link it to an Idea.

EXAMPLES:
- {"repository_url": "owner/repo", "issue_number": 42}
- {"repository_url": "owner/repo", "issue_number": 42, "tracks_idea": "ent-idea-key"}

RETURNS: Created entity info with entity_key for further linking.""",
        inputSchema={
            "type": "object",
            "properties": {
                "repository_url": {"type": "string", "description": "GitHub repository URL or owner/repo format"},
                "issue_number": {"type": "integer", "description": "GitHub issue number"},
                "tracks_idea": {"type": "string", "description": "Optional entity_key of an Idea this issue tracks"}
            },
            "required": ["repository_url", "issue_number"]
        }
    ),
    types.Tool(
        name="link_work_item",
        description="""Link a Commit or Issue to an Idea, Issue, or Project.

USE THIS WHEN: You want to create an audit trail connecting work items.

RELATIONSHIP TYPES:
- IMPLEMENTS: Commit implements an Idea or Issue
- TRACKS: Issue tracks an Idea
- RESOLVES: Commit or Issue resolves another Issue
- BELONGS_TO: Entity belongs to a Project

WORKFLOW: After syncing commits, link them to Ideas:
  link_work_item(commit_key, idea_key, "IMPLEMENTS")

EXAMPLES:
- {"source_key": "ent-commit", "target_key": "ent-idea", "relationship": "IMPLEMENTS"}
- {"source_key": "ent-issue", "target_key": "ent-idea", "relationship": "TRACKS"}

RETURNS: Confirmation with relationship details.""",
        inputSchema={
            "type": "object",
            "properties": {
                "source_key": {"type": "string", "description": "Entity key of the source (Commit or Issue)"},
                "target_key": {"type": "string", "description": "Entity key of the target (Idea, Issue, or Project)"},
                "relationship": {"type": "string", "description": "IMPLEMENTS, TRACKS, RESOLVES, or BELONGS_TO", "default": "IMPLEMENTS"}
            },
            "required": ["source_key", "target_key"]
        }
    ),
]


# ============================================================
# INTERNAL IMPLEMENTATIONS
# ============================================================

async def create_commit_entity(
    repository_url: str,
    sha: str,
    implements: Optional[str] = None,
) -> str:
    """
    Create a Commit entity for a specific commit.

    Use this to manually create a Commit entity and optionally link it to an
    Idea or Issue that it implements.

    Args:
        repository_url: GitHub repository URL
        sha: The commit SHA (full or abbreviated)
        implements: Optional entity_key of an Idea or Issue this commit implements

    Returns:
        Formatted string with created entity info
    """
    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        # Fetch the specific commit
        commits = gh.get_commits(owner, repo_name, limit=100)
        commit_info = None
        for c in commits:
            if c.sha.startswith(sha) or sha.startswith(c.sha[:7]):
                commit_info = c
                break

        if not commit_info:
            return f"Commit {sha} not found in recent history of {owner}/{repo_name}"

        # Find Repository entity
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
            return f"Repository entity not found for {owner}/{repo_name}. Run sync_repository first."

        # Check if Commit entity already exists
        existing_search = await _make_request(
            config, "GET", "/entities",
            params={"type": "Commit", "search": commit_info.sha[:12]}
        )

        commit_key = None
        existing = False
        if existing_search.get("success"):
            for e in existing_search.get("data", {}).get("entities", []):
                if e.get("properties", {}).get("sha") == commit_info.sha:
                    commit_key = e.get("entity_key")
                    existing = True
                    break

        # Create commit entity if it doesn't exist
        if not commit_key:
            properties = gh.to_commit_entity_properties(commit_info)
            title = properties.get('title', '')[:80] if properties.get('title') else commit_info.sha[:7]

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
                commit_key = new_entity.get("entity_key")

                # Create BELONGS_TO relationship
                await _make_request(
                    config, "POST", "/relationships",
                    json={
                        "from_entity_key": commit_key,
                        "to_entity_key": repository_entity_key,
                        "relationship_type": "BELONGS_TO",
                    }
                )
            else:
                return f"Failed to create Commit entity: {create_result.get('msg')}"

        output = f"## Commit Entity {'Found' if existing else 'Created'}\n\n"
        output += f"**SHA:** {commit_info.sha[:7]}\n"
        output += f"**Title:** {commit_info.message.split(chr(10))[0][:60]}\n"
        output += f"**Author:** {commit_info.author_name}\n"
        output += f"**Entity Key:** {commit_key}\n\n"

        # Link to implements target if provided
        if implements and commit_key:
            link_result = await _make_request(
                config,
                "POST",
                "/relationships",
                json={
                    "from_entity_key": commit_key,
                    "to_entity_key": implements,
                    "relationship_type": "IMPLEMENTS"
                }
            )
            if link_result.get("success"):
                output += f"**Linked:** IMPLEMENTS -> {implements}\n"
            else:
                output += f"**Link failed:** {link_result.get('msg')}\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error creating commit entity: {e}"


async def create_issue_entity(
    repository_url: str,
    issue_number: int,
    tracks_idea: Optional[str] = None,
) -> str:
    """
    Create an Issue entity for a specific GitHub issue.

    Use this to manually create an Issue entity and optionally link it to an
    Idea that it tracks.

    Args:
        repository_url: GitHub repository URL
        issue_number: The GitHub issue number
        tracks_idea: Optional entity_key of an Idea this issue tracks

    Returns:
        Formatted string with created entity info
    """
    try:
        from api.services.github import GitHubService

        gh = GitHubService()
        owner, repo_name = gh.parse_repo_url(repository_url)

        # Fetch the specific issue
        issues = gh.get_issues(owner, repo_name, state="all", limit=200)
        issue_info = None
        for i in issues:
            if i.number == issue_number:
                issue_info = i
                break

        if not issue_info:
            return f"Issue #{issue_number} not found in {owner}/{repo_name}"

        if issue_info.is_pull_request:
            return f"#{issue_number} is a Pull Request, not an Issue"

        # Find Repository entity
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
            return f"Repository entity not found for {owner}/{repo_name}. Run sync_repository first."

        # Check if Issue entity already exists
        existing_search = await _make_request(
            config, "GET", "/entities",
            params={"type": "Issue", "search": f"#{issue_number}"}
        )

        issue_key = None
        existing = False
        if existing_search.get("success"):
            for e in existing_search.get("data", {}).get("entities", []):
                if e.get("properties", {}).get("github_number") == issue_number:
                    issue_key = e.get("entity_key")
                    existing = True
                    break

        # Create issue entity if it doesn't exist
        if not issue_key:
            properties = gh.to_issue_entity_properties(issue_info)

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
                new_entity = create_result.get("data", {}).get("entity", {})
                issue_key = new_entity.get("entity_key")

                # Create BELONGS_TO relationship
                await _make_request(
                    config, "POST", "/relationships",
                    json={
                        "from_entity_key": issue_key,
                        "to_entity_key": repository_entity_key,
                        "relationship_type": "BELONGS_TO",
                    }
                )
            else:
                return f"Failed to create Issue entity: {create_result.get('msg')}"

        output = f"## Issue Entity {'Found' if existing else 'Created'}\n\n"
        output += f"**Number:** #{issue_info.number}\n"
        output += f"**Title:** {issue_info.title[:60]}\n"
        output += f"**State:** {issue_info.state}\n"
        output += f"**Entity Key:** {issue_key}\n\n"

        # Link to idea if provided
        if tracks_idea and issue_key:
            link_result = await _make_request(
                config,
                "POST",
                "/relationships",
                json={
                    "from_entity_key": issue_key,
                    "to_entity_key": tracks_idea,
                    "relationship_type": "TRACKS"
                }
            )
            if link_result.get("success"):
                output += f"**Linked:** TRACKS -> {tracks_idea}\n"
            else:
                output += f"**Link failed:** {link_result.get('msg')}\n"

        return output

    except ImportError as e:
        return f"GitHub integration not available: {e}"
    except Exception as e:
        return f"Error creating issue entity: {e}"


async def link_work_item(
    source_key: str,
    target_key: str,
    relationship: str = "IMPLEMENTS",
) -> str:
    """
    Link a Commit or Issue to an Idea, Issue, or Project.

    Creates a relationship between work items to build the paper trail from
    idea -> issue -> commit.

    Common relationships:
    - IMPLEMENTS: Commit implements an Idea or Issue
    - TRACKS: Issue tracks an Idea
    - RESOLVES: Commit or Issue resolves another Issue
    - BELONGS_TO: Entity belongs to a Project

    Args:
        source_key: Entity key of the source (Commit or Issue)
        target_key: Entity key of the target (Idea, Issue, or Project)
        relationship: Relationship type (IMPLEMENTS, TRACKS, RESOLVES, BELONGS_TO)

    Returns:
        Formatted string confirming the link
    """
    valid_relationships = ["IMPLEMENTS", "TRACKS", "RESOLVES", "BELONGS_TO", "RELATED_TO"]
    if relationship not in valid_relationships:
        return f"Invalid relationship type. Use one of: {', '.join(valid_relationships)}"

    try:
        # Verify both entities exist
        source_result = await _make_request(config, "GET", f"/entities/{source_key}")
        target_result = await _make_request(config, "GET", f"/entities/{target_key}")

        if not source_result.get("success"):
            return f"Source entity not found: {source_key}"
        if not target_result.get("success"):
            return f"Target entity not found: {target_key}"

        source_entity = source_result.get("data", {}).get("entity", {})
        target_entity = target_result.get("data", {}).get("entity", {})

        # Create relationship
        link_result = await _make_request(
            config,
            "POST",
            "/relationships",
            json={
                "from_entity_key": source_key,
                "to_entity_key": target_key,
                "relationship_type": relationship
            }
        )

        if link_result.get("success"):
            rel = link_result.get("data", {}).get("relationship", {})
            return f"""## Work Item Linked

**{source_entity.get('name')}** ({source_entity.get('entity_type')})
  -> {relationship}
**{target_entity.get('name')}** ({target_entity.get('entity_type')})

**Relationship Key:** {rel.get('relationship_key')}

This creates an audit trail connecting work items to ideas and projects.
"""
        else:
            return f"Failed to create link: {link_result.get('msg')}"

    except Exception as e:
        return f"Error linking work items: {e}"


# ============================================================
# MCP HANDLER WRAPPERS
# ============================================================

async def _handle_create_commit_entity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for create_commit_entity."""
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("create_commit_entity")

    text = await create_commit_entity(
        arguments.get("repository_url"),
        arguments.get("sha"),
        arguments.get("implements")
    )
    return [types.TextContent(type="text", text=text)]


async def _handle_create_issue_entity(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for create_issue_entity."""
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("create_issue_entity")

    text = await create_issue_entity(
        arguments.get("repository_url"),
        arguments.get("issue_number"),
        arguments.get("tracks_idea")
    )
    return [types.TextContent(type="text", text=text)]


async def _handle_link_work_item(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """MCP handler wrapper for link_work_item."""
    # Guest check - block write operations for guest users
    if is_guest_session(session_state):
        return reject_guest_write("link_work_item")

    text = await link_work_item(
        arguments.get("source_key"),
        arguments.get("target_key"),
        arguments.get("relationship", "IMPLEMENTS")
    )
    return [types.TextContent(type="text", text=text)]


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "create_commit_entity": _handle_create_commit_entity,
    "create_issue_entity": _handle_create_issue_entity,
    "link_work_item": _handle_link_work_item,
}
