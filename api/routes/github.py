"""
Collective Memory Platform - GitHub Routes

GitHub integration endpoints for repository sync and data retrieval.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields
from datetime import datetime, timezone

from api.models import Entity, RepositoryStats, Commit, Metric, MetricTypes, db
from api.services.github import github_service, store_commits, store_repository_metrics
from api.services.auth import require_auth_strict
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
        @require_auth_strict
        def post(self):
            """
            Sync a GitHub repository to the knowledge graph. Requires authentication.

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
                        domain_key=f'github.{repo_info.full_name.split("/")[0]}',
                        confidence=1.0,
                        source='github-api',
                    )
                    db.session.add(entity)
                    msg = f'Repository {repo_info.full_name} created successfully'

                db.session.commit()

                # Store metrics snapshot
                metrics_result = store_repository_metrics(entity_key, repo_info)

                # Optionally sync commits (if requested)
                commits_result = None
                if data.get('sync_commits', True):
                    owner, repo = repo_info.full_name.split('/')
                    commits = gh.get_commits(owner, repo, limit=100)
                    commits_result = store_commits(entity_key, commits)

                return {
                    'success': True,
                    'msg': msg,
                    'data': {
                        'entity': entity.to_dict(),
                        'metrics': metrics_result,
                        'commits': commits_result,
                    }
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
        @require_auth_strict
        def post(self):
            """
            Sync repository commit stats to time-series table. Requires authentication.

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

    # ========== Stored Commits Routes ==========

    @ns.route('/commits/<path:entity_key>')
    @ns.param('entity_key', 'Repository entity key')
    class StoredCommits(Resource):
        @ns.doc('get_stored_commits')
        @ns.param('limit', 'Maximum commits to return', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        def get(self, entity_key):
            """Get stored commits for a repository."""
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            try:
                commits = Commit.get_by_repository(entity_key, limit=limit, offset=offset)
                total = Commit.query.filter_by(repository_key=entity_key).count()

                return {
                    'success': True,
                    'msg': f'Retrieved {len(commits)} commits',
                    'data': {
                        'commits': [c.to_dict() for c in commits],
                        'count': len(commits),
                        'total': total,
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/commits/ai-assisted')
    class AIAssistedCommits(Resource):
        @ns.doc('get_ai_assisted_commits')
        @ns.param('repository_key', 'Filter by repository entity key')
        @ns.param('limit', 'Maximum commits to return', type=int, default=100)
        @ns.marshal_with(response_model)
        def get(self):
            """Get commits with AI co-authors."""
            repository_key = request.args.get('repository_key')
            limit = request.args.get('limit', 100, type=int)

            try:
                commits = Commit.get_ai_assisted(repository_key=repository_key, limit=limit)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(commits)} AI-assisted commits',
                    'data': {
                        'commits': [c.to_dict() for c in commits],
                        'count': len(commits),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/commits/by-author/<path:author_email>')
    @ns.param('author_email', 'Author email address')
    class CommitsByAuthor(Resource):
        @ns.doc('get_commits_by_author')
        @ns.param('limit', 'Maximum commits to return', type=int, default=100)
        @ns.marshal_with(response_model)
        def get(self, author_email):
            """Get commits by author email."""
            limit = request.args.get('limit', 100, type=int)

            try:
                commits = Commit.get_by_author(author_email, limit=limit)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(commits)} commits by {author_email}',
                    'data': {
                        'commits': [c.to_dict() for c in commits],
                        'count': len(commits),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    # ========== Metrics Routes ==========

    @ns.route('/metrics/<path:entity_key>')
    @ns.param('entity_key', 'Entity key to get metrics for')
    class EntityMetrics(Resource):
        @ns.doc('get_entity_metrics')
        @ns.param('metric_type', 'Filter by metric type (e.g., stars, forks)')
        @ns.param('limit', 'Maximum metrics to return', type=int, default=100)
        @ns.marshal_with(response_model)
        def get(self, entity_key):
            """Get metrics for an entity."""
            metric_type = request.args.get('metric_type')
            limit = request.args.get('limit', 100, type=int)

            try:
                metrics = Metric.get_for_entity(entity_key, metric_type=metric_type, limit=limit)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(metrics)} metrics',
                    'data': {
                        'metrics': [m.to_dict() for m in metrics],
                        'count': len(metrics),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/metrics/<path:entity_key>/timeseries')
    @ns.param('entity_key', 'Entity key')
    class MetricsTimeSeries(Resource):
        @ns.doc('get_metrics_timeseries')
        @ns.param('metric_type', 'Metric type (required)', required=True)
        @ns.param('days', 'Number of days of history', type=int, default=90)
        @ns.marshal_with(response_model)
        def get(self, entity_key):
            """Get time series data for a metric."""
            metric_type = request.args.get('metric_type')
            days = request.args.get('days', 90, type=int)

            if not metric_type:
                return {
                    'success': False,
                    'msg': 'metric_type is required',
                    'data': None
                }, 400

            try:
                from datetime import timedelta
                start_date = datetime.now(timezone.utc) - timedelta(days=days)
                metrics = Metric.get_time_series(entity_key, metric_type, start_date=start_date)

                return {
                    'success': True,
                    'msg': f'Retrieved {len(metrics)} data points',
                    'data': {
                        'metric_type': metric_type,
                        'series': [
                            {
                                'timestamp': m.recorded_at.isoformat(),
                                'value': m.value,
                            }
                            for m in metrics
                        ],
                        'count': len(metrics),
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500

    @ns.route('/metrics/<path:entity_key>/latest')
    @ns.param('entity_key', 'Entity key')
    class LatestMetrics(Resource):
        @ns.doc('get_latest_metrics')
        @ns.marshal_with(response_model)
        def get(self, entity_key):
            """Get latest value for each metric type."""
            try:
                # Get latest for common metrics
                metric_types = [
                    MetricTypes.STARS,
                    MetricTypes.FORKS,
                    MetricTypes.OPEN_ISSUES,
                    MetricTypes.SIZE_KB,
                ]

                latest = {}
                for mt in metric_types:
                    metric = Metric.get_latest(entity_key, mt)
                    if metric:
                        latest[mt] = {
                            'value': metric.value,
                            'recorded_at': metric.recorded_at.isoformat(),
                        }

                return {
                    'success': True,
                    'msg': f'Retrieved {len(latest)} latest metrics',
                    'data': {
                        'entity_key': entity_key,
                        'metrics': latest,
                    }
                }

            except Exception as e:
                return {
                    'success': False,
                    'msg': str(e),
                    'data': None
                }, 500
