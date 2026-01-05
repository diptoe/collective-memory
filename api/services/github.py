"""
Collective Memory Platform - GitHub Service

Integration with GitHub API for repository analysis, issues, commits, and contributor tracking.
Adapted from github-analysis project.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
    print("[GitHub Service] PyGithub imported successfully")
except ImportError as e:
    GITHUB_AVAILABLE = False
    Github = None
    GithubException = Exception
    print(f"[GitHub Service] PyGithub import failed: {e}")


@dataclass
class RepositoryInfo:
    """Repository metadata from GitHub."""
    name: str
    full_name: str
    description: str
    url: str
    default_branch: str
    language: str
    size_kb: int
    stars: int
    forks: int
    open_issues: int
    is_private: bool
    is_archived: bool
    is_fork: bool
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    topics: List[str]


@dataclass
class IssueInfo:
    """Issue metadata from GitHub."""
    number: int
    title: str
    state: str  # open, closed
    url: str
    body: str
    author: str
    assignees: List[str]
    labels: List[str]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    comments_count: int
    is_pull_request: bool


@dataclass
class CommitInfo:
    """Commit metadata from GitHub."""
    sha: str
    message: str
    author_name: str
    author_email: str
    date: datetime
    additions: int
    deletions: int
    files_changed: int
    co_authors: List[str]
    url: str


@dataclass
class ContributorInfo:
    """Contributor statistics."""
    login: str
    name: str
    avatar_url: str
    commits: int
    additions: int
    deletions: int


class GitHubService:
    """
    Service for GitHub API interactions.

    Provides methods for:
    - Repository metadata retrieval
    - Issue tracking
    - Commit analysis
    - Contributor statistics
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub service.

        Args:
            token: GitHub Personal Access Token. If not provided, reads from GITHUB_PAT env var.
        """
        if not GITHUB_AVAILABLE:
            raise ImportError("PyGithub is not installed. Run: pip install PyGithub")

        self.token = token or os.getenv("GITHUB_PAT") or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token not provided. Set GITHUB_PAT environment variable.")

        self.github = Github(self.token)
        self._user = None

    @property
    def authenticated_user(self) -> str:
        """Get the authenticated user's login."""
        if self._user is None:
            self._user = self.github.get_user().login
        return self._user

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """
        Parse a GitHub URL to extract owner and repo name.

        Args:
            url: GitHub repository URL (e.g., https://github.com/owner/repo)

        Returns:
            Tuple of (owner, repo_name)
        """
        # Handle various URL formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/\.]+)',  # https or ssh
            r'^([^/]+)/([^/]+)$',  # owner/repo format
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip('.git')

        raise ValueError(f"Could not parse GitHub URL: {url}")

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """
        Get repository metadata.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name

        Returns:
            RepositoryInfo dataclass with repository metadata
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")

            return RepositoryInfo(
                name=repository.name,
                full_name=repository.full_name,
                description=repository.description or "",
                url=repository.html_url,
                default_branch=repository.default_branch,
                language=repository.language or "Unknown",
                size_kb=repository.size,
                stars=repository.stargazers_count,
                forks=repository.forks_count,
                open_issues=repository.open_issues_count,
                is_private=repository.private,
                is_archived=repository.archived,
                is_fork=repository.fork,
                created_at=repository.created_at,
                updated_at=repository.updated_at,
                pushed_at=repository.pushed_at,
                topics=repository.get_topics(),
            )
        except GithubException as e:
            raise RuntimeError(f"Failed to get repository {owner}/{repo}: {e}")

    def get_repository_from_url(self, url: str) -> RepositoryInfo:
        """
        Get repository metadata from a GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            RepositoryInfo dataclass
        """
        owner, repo = self.parse_repo_url(url)
        return self.get_repository(owner, repo)

    def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 30,
        labels: Optional[List[str]] = None,
    ) -> List[IssueInfo]:
        """
        Get issues from a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state filter ('open', 'closed', 'all')
            limit: Maximum number of issues to return
            labels: Optional list of labels to filter by

        Returns:
            List of IssueInfo dataclasses
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")

            kwargs = {"state": state}
            if labels:
                kwargs["labels"] = labels

            issues = repository.get_issues(**kwargs)

            result = []
            for i, issue in enumerate(issues):
                if i >= limit:
                    break

                result.append(IssueInfo(
                    number=issue.number,
                    title=issue.title,
                    state=issue.state,
                    url=issue.html_url,
                    body=issue.body or "",
                    author=issue.user.login if issue.user else "unknown",
                    assignees=[a.login for a in issue.assignees],
                    labels=[l.name for l in issue.labels],
                    created_at=issue.created_at,
                    updated_at=issue.updated_at,
                    closed_at=issue.closed_at,
                    comments_count=issue.comments,
                    is_pull_request=issue.pull_request is not None,
                ))

            return result

        except GithubException as e:
            raise RuntimeError(f"Failed to get issues for {owner}/{repo}: {e}")

    def get_commits(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 30,
        branch: Optional[str] = None,
    ) -> List[CommitInfo]:
        """
        Get commits from a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Start date for commits
            until: End date for commits
            limit: Maximum number of commits to return
            branch: Branch to get commits from (defaults to default branch)

        Returns:
            List of CommitInfo dataclasses
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")

            kwargs = {}
            if since:
                kwargs["since"] = since
            if until:
                kwargs["until"] = until
            if branch:
                kwargs["sha"] = branch

            commits = repository.get_commits(**kwargs)

            result = []
            for i, commit in enumerate(commits):
                if i >= limit:
                    break

                # Extract co-authors from commit message
                co_authors = self._extract_co_authors(commit.commit.message)

                # Get commit stats
                stats = commit.stats

                # Get file count - commit.files can be a PaginatedList, so count via iteration
                try:
                    files_changed = sum(1 for _ in commit.files) if commit.files else 0
                except Exception:
                    files_changed = 0

                result.append(CommitInfo(
                    sha=commit.sha,
                    message=commit.commit.message,
                    author_name=commit.commit.author.name if commit.commit.author else "Unknown",
                    author_email=commit.commit.author.email if commit.commit.author else "",
                    date=commit.commit.author.date if commit.commit.author else datetime.now(),
                    additions=stats.additions if stats else 0,
                    deletions=stats.deletions if stats else 0,
                    files_changed=files_changed,
                    co_authors=co_authors,
                    url=commit.html_url,
                ))

            return result

        except GithubException as e:
            raise RuntimeError(f"Failed to get commits for {owner}/{repo}: {e}")

    def get_contributors(
        self,
        owner: str,
        repo: str,
        limit: int = 30,
    ) -> List[ContributorInfo]:
        """
        Get contributors for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            limit: Maximum number of contributors to return

        Returns:
            List of ContributorInfo dataclasses
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            contributors = repository.get_contributors()

            result = []
            for i, contrib in enumerate(contributors):
                if i >= limit:
                    break

                result.append(ContributorInfo(
                    login=contrib.login,
                    name=contrib.name or contrib.login,
                    avatar_url=contrib.avatar_url,
                    commits=contrib.contributions,
                    additions=0,  # Would need separate API calls per commit
                    deletions=0,
                ))

            return result

        except GithubException as e:
            raise RuntimeError(f"Failed to get contributors for {owner}/{repo}: {e}")

    def _extract_co_authors(self, commit_message: str) -> List[str]:
        """
        Extract co-author names from commit message.

        Args:
            commit_message: The commit message text

        Returns:
            List of co-author names
        """
        co_authors = []
        pattern = r'Co-[Aa]uthored-[Bb]y:\s*([^<]+)\s*<'
        matches = re.findall(pattern, commit_message)
        for match in matches:
            co_authors.append(match.strip())
        return co_authors

    def to_entity_properties(self, repo_info: RepositoryInfo) -> Dict[str, Any]:
        """
        Convert RepositoryInfo to properties dict for CM Entity.

        Args:
            repo_info: RepositoryInfo dataclass

        Returns:
            Dict suitable for Entity.properties
        """
        return {
            "url": repo_info.url,
            "owner": repo_info.full_name.split("/")[0],
            "platform": "github",
            "default_branch": repo_info.default_branch,
            "language": repo_info.language,
            "size_kb": repo_info.size_kb,
            "stars": repo_info.stars,
            "forks": repo_info.forks,
            "open_issues": repo_info.open_issues,
            "visibility": "private" if repo_info.is_private else "public",
            "is_archived": repo_info.is_archived,
            "is_fork": repo_info.is_fork,
            "topics": repo_info.topics,
            "description": repo_info.description,
            "created_at": repo_info.created_at.isoformat() if repo_info.created_at else None,
            "updated_at": repo_info.updated_at.isoformat() if repo_info.updated_at else None,
            "pushed_at": repo_info.pushed_at.isoformat() if repo_info.pushed_at else None,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    def to_issue_entity_properties(self, issue: IssueInfo) -> Dict[str, Any]:
        """
        Convert IssueInfo to properties dict for CM Entity.

        Args:
            issue: IssueInfo dataclass

        Returns:
            Dict suitable for Entity.properties
        """
        return {
            "number": issue.number,
            "state": issue.state,
            "url": issue.url,
            "author": issue.author,
            "assignees": issue.assignees,
            "labels": issue.labels,
            "comments_count": issue.comments_count,
            "is_pull_request": issue.is_pull_request,
            "body": issue.body[:1000] if issue.body else "",  # Truncate long bodies
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
        }


# Singleton instance - lazy initialization
_github_service: Optional[GitHubService] = None


def get_github_service() -> GitHubService:
    """Get or create the GitHub service singleton."""
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service


def github_service() -> Optional[GitHubService]:
    """
    Get the GitHub service if available.

    Returns None if GITHUB_PAT is not configured.
    """
    try:
        return get_github_service()
    except (ImportError, ValueError) as e:
        print(f"[GitHub Service] Failed to initialize: {e}")
        return None
