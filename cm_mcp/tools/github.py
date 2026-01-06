"""
Collective Memory MCP Tools - GitHub Integration

Tools for syncing repositories, fetching issues, and analyzing commits.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cm_mcp.config import config
from cm_mcp.tools.utils import _make_request


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
                co_author_str = f" 🤝 {', '.join(commit.co_authors)}"

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
                output += f"**Linked:** IMPLEMENTS → {implements}\n"
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
                output += f"**Linked:** TRACKS → {tracks_idea}\n"
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
    idea → issue → commit.

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
  ↓ {relationship}
**{target_entity.get('name')}** ({target_entity.get('entity_type')})

**Relationship Key:** {rel.get('relationship_key')}

This creates an audit trail connecting work items to ideas and projects.
"""
        else:
            return f"Failed to create link: {link_result.get('msg')}"

    except Exception as e:
        return f"Error linking work items: {e}"
