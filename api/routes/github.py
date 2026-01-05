"""
Collective Memory Platform - GitHub Routes

GitHub integration endpoints for repository sync and data retrieval.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields
from datetime import datetime, timezone

from api.models import Entity, RepositoryStats, db
from api.services.github import github_service
from collections import defaultdict


def register_github_routes(api: Api):
    """Register GitHub routes with the API."""

    ns = api.namespace(
        'github',
        description='GitHub integration operations',
        path='/github'
    )

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    sync_model = ns.model('SyncRequest', {
        'repository_url': fields.String(required=True, description='GitHub repository URL'),
    })

    @ns.route('/sync')
    class GitHubSync(Resource):
        @ns.doc('sync_repository')
        @ns.expect(sync_model)
        @ns.marshal_with(response_model)
        def post(self):
            """
            Sync a GitHub repository to the knowledge graph.

            Fetches current repository data from GitHub and updates or creates
            a Repository entity with the latest information.
            """
            data = request.get_json() or {}
            repository_url = data.get('repository_url')

            if not repository_url:
                return {
                    'success': False,
                    'msg': 'repository_url is required',
                    'data': None
                }, 400

            gh = github_service()
            print(f"[GitHub Route] github_service() returned: {gh}")
            if not gh:
                import os
                print(f"[GitHub Route] GITHUB_PAT set: {bool(os.getenv('GITHUB_PAT'))}")
                return {
                    'success': False,
                    'msg': 'GitHub integration not configured. Set GITHUB_PAT environment variable.',
                    'data': None
                }, 503

            try:
                # Get repository info from GitHub
                repo_info = gh.get_repository_from_url(repository_url)
                properties = gh.to_entity_properties(repo_info)

                # Generate entity key from full_name
                entity_key = f"repo:{repo_info.full_name.lower().replace('/', ':')}"

                # Check if entity exists
                entity = Entity.query.filter_by(entity_key=entity_key).first()

                if entity:
                    # Update existing entity
                    entity.name = repo_info.name
                    entity.properties = properties
                    entity.updated_at = datetime.now(timezone.utc)
                    msg = f'Repository {repo_info.full_name} synced successfully'
                else:
                    # Create new entity
                    entity = Entity(
                        entity_key=entity_key,
                        entity_type='Repository',
                        name=repo_info.name,
                        properties=properties,
                        context_domain=f'github.{repo_info.full_name.split("/")[0]}',
                        confidence=1.0,
                        source='github-api',
                    )
                    db.session.add(entity)
                    msg = f'Repository {repo_info.full_name} created successfully'

                db.session.commit()

                return {
                    'success': True,
                    'msg': msg,
                    'data': {'entity': entity.to_dict()}
                }

            except Exception as e:
                db.session.rollback()
                return {
                    'success': False,
                    'msg': f'Failed to sync repository: {str(e)}',
                    'data': None
                }, 500

    @ns.route('/repo/<path:owner_repo>')
    @ns.param('owner_repo', 'Repository in owner/repo format')
    class GitHubRepository(Resource):
        @ns.doc('get_repository')
        @ns.marshal_with(response_model)
        def get(self, owner_repo):
            """Get repository information from GitHub."""
            gh = github_service()
            if not gh:
                return {
                    'success': False,
                    'msg': 'GitHub integration not configured',
                    'data': None
                }, 503

            try:
                parts = owner_repo.split('/')
                if len(parts) != 2:
                    return {
                        'success': False,
                        'msg': 'Invalid format. Use owner/repo',
                        'data': None
                    }, 400

                owner, repo = parts
                repo_info = gh.get_repository(owner, repo)

                return {
                    'success': True,
                    'msg': 'Repository retrieved',
                    'data': {
                        'repository': gh.to_entity_properties(repo_info),
                        'name': repo_info.name,
                        'full_name': repo_info.full_name,
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/repo/<path:owner_repo>/issues')
    @ns.param('owner_repo', 'Repository in owner/repo format')
    class GitHubIssues(Resource):
        @ns.doc('get_issues')
        @ns.param('state', 'Issue state: open, closed, all', default='open')
        @ns.param('limit', 'Maximum issues to return', type=int, default=30)
        @ns.marshal_with(response_model)
        def get(self, owner_repo):
            """Get issues from a GitHub repository."""
            gh = github_service()
            if not gh:
                return {
                    'success': False,
                    'msg': 'GitHub integration not configured',
                    'data': None
                }, 503

            try:
                parts = owner_repo.split('/')
                if len(parts) != 2:
                    return {
                        'success': False,
                        'msg': 'Invalid format. Use owner/repo',
                        'data': None
                    }, 400

                owner, repo = parts
                state = request.args.get('state', 'open')
                limit = request.args.get('limit', 30, type=int)

                issues = gh.get_issues(owner, repo, state=state, limit=limit)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(issues)} issues',
                    'data': {
                        'issues': [gh.to_issue_entity_properties(i) for i in issues],
                        'count': len(issues),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/repo/<path:owner_repo>/commits')
    @ns.param('owner_repo', 'Repository in owner/repo format')
    class GitHubCommits(Resource):
        @ns.doc('get_commits')
        @ns.param('limit', 'Maximum commits to return', type=int, default=30)
        @ns.param('branch', 'Branch name')
        @ns.marshal_with(response_model)
        def get(self, owner_repo):
            """Get commits from a GitHub repository."""
            gh = github_service()
            if not gh:
                return {
                    'success': False,
                    'msg': 'GitHub integration not configured',
                    'data': None
                }, 503

            try:
                parts = owner_repo.split('/')
                if len(parts) != 2:
                    return {
                        'success': False,
                        'msg': 'Invalid format. Use owner/repo',
                        'data': None
                    }, 400

                owner, repo = parts
                limit = request.args.get('limit', 30, type=int)
                branch = request.args.get('branch')

                commits = gh.get_commits(owner, repo, limit=limit, branch=branch)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(commits)} commits',
                    'data': {
                        'commits': [
                            {
                                'sha': c.sha[:7],
                                'message': c.message.split('\n')[0],
                                'author': c.author_name,
                                'date': c.date.isoformat() if c.date else None,
                                'additions': c.additions,
                                'deletions': c.deletions,
                                'co_authors': c.co_authors,
                            }
                            for c in commits
                        ],
                        'count': len(commits),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/repo/<path:owner_repo>/contributors')
    @ns.param('owner_repo', 'Repository in owner/repo format')
    class GitHubContributors(Resource):
        @ns.doc('get_contributors')
        @ns.param('limit', 'Maximum contributors to return', type=int, default=30)
        @ns.marshal_with(response_model)
        def get(self, owner_repo):
            """Get contributors from a GitHub repository."""
            gh = github_service()
            if not gh:
                return {
                    'success': False,
                    'msg': 'GitHub integration not configured',
                    'data': None
                }, 503

            try:
                parts = owner_repo.split('/')
                if len(parts) != 2:
                    return {
                        'success': False,
                        'msg': 'Invalid format. Use owner/repo',
                        'data': None
                    }, 400

                owner, repo = parts
                limit = request.args.get('limit', 30, type=int)

                contributors = gh.get_contributors(owner, repo, limit=limit)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(contributors)} contributors',
                    'data': {
                        'contributors': [
                            {
                                'login': c.login,
                                'name': c.name,
                                'avatar_url': c.avatar_url,
                                'commits': c.commits,
                            }
                            for c in contributors
                        ],
                        'count': len(contributors),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/stats/sync')
    class GitHubStatsSync(Resource):
        @ns.doc('sync_repository_stats')
        @ns.expect(sync_model)
        @ns.marshal_with(response_model)
        def post(self):
            """
            Sync repository commit stats to time-series table.

            Fetches recent commits and aggregates daily statistics
            for charting and analysis.
            """
            data = request.get_json() or {}
            repository_url = data.get('repository_url')
            days = data.get('days', 90)  # Default to 90 days of history

            if not repository_url:
                return {
                    'success': False,
                    'msg': 'repository_url is required',
                    'data': None
                }, 400

            gh = github_service()
            if not gh:
                return {
                    'success': False,
                    'msg': 'GitHub integration not configured',
                    'data': None
                }, 503

            try:
                # Get repository info to find entity_key
                repo_info = gh.get_repository_from_url(repository_url)
                entity_key = f"repo:{repo_info.full_name.lower().replace('/', ':')}"

                # Fetch commits (up to 500 for stats)
                owner, repo = repo_info.full_name.split('/')
                commits = gh.get_commits(owner, repo, limit=min(days * 5, 500))

                # Aggregate by date
                daily_stats = defaultdict(lambda: {
                    'commits_count': 0,
                    'additions': 0,
                    'deletions': 0,
                    'files_changed': 0,
                    'authors': set(),
                    'ai_assisted': 0,
                })

                for c in commits:
                    if c.date:
                        date_key = c.date.date()
                        stats = daily_stats[date_key]
                        stats['commits_count'] += 1
                        stats['additions'] += c.additions or 0
                        stats['deletions'] += c.deletions or 0
                        stats['files_changed'] += c.files_changed or 0
                        if c.author_name:
                            stats['authors'].add(c.author_name)
                        if c.co_authors:
                            stats['ai_assisted'] += 1

                # Upsert stats records
                records_updated = 0
                for date_key, stats in daily_stats.items():
                    existing = RepositoryStats.query.filter_by(
                        entity_key=entity_key,
                        date=date_key
                    ).first()

                    if existing:
                        existing.commits_count = stats['commits_count']
                        existing.additions = stats['additions']
                        existing.deletions = stats['deletions']
                        existing.files_changed = stats['files_changed']
                        existing.unique_authors = len(stats['authors'])
                        existing.ai_assisted_commits = stats['ai_assisted']
                    else:
                        new_stat = RepositoryStats(
                            entity_key=entity_key,
                            date=date_key,
                            commits_count=stats['commits_count'],
                            additions=stats['additions'],
                            deletions=stats['deletions'],
                            files_changed=stats['files_changed'],
                            unique_authors=len(stats['authors']),
                            ai_assisted_commits=stats['ai_assisted'],
                        )
                        db.session.add(new_stat)
                    records_updated += 1

                db.session.commit()

                return {
                    'success': True,
                    'msg': f'Synced {records_updated} daily stats records for {repo_info.full_name}',
                    'data': {
                        'entity_key': entity_key,
                        'days_synced': records_updated,
                        'commits_processed': len(commits),
                    }
                }

            except Exception as e:
                db.session.rollback()
                return {
                    'success': False,
                    'msg': f'Failed to sync stats: {str(e)}',
                    'data': None
                }, 500

    @ns.route('/stats/<path:entity_key>')
    @ns.param('entity_key', 'Repository entity key (e.g., repo:owner:name)')
    class GitHubStats(Resource):
        @ns.doc('get_repository_stats')
        @ns.param('days', 'Number of days of history', type=int, default=90)
        @ns.marshal_with(response_model)
        def get(self, entity_key):
            """Get historical stats for a repository."""
            days = request.args.get('days', 90, type=int)

            try:
                # Query stats ordered by date
                from datetime import timedelta
                cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

                stats = RepositoryStats.query.filter(
                    RepositoryStats.entity_key == entity_key,
                    RepositoryStats.date >= cutoff
                ).order_by(RepositoryStats.date.asc()).all()

                return {
                    'success': True,
                    'msg': f'Retrieved {len(stats)} days of stats',
                    'data': {
                        'stats': [s.to_dict() for s in stats],
                        'count': len(stats),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500
