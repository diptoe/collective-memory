"""
Collective Memory Platform - Activity Routes

API endpoints for activity tracking and dashboard data.
"""
from datetime import datetime, timedelta, timezone
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models.activity import Activity, ActivityType
from api.services.activity import activity_service


def register_activity_routes(api: Api):
    """Register activity routes with the API."""

    ns = api.namespace(
        'activities',
        description='Activity tracking and dashboard operations',
        path='/activities'
    )

    activity_model = ns.model('Activity', {
        'activity_key': fields.String(readonly=True, description='Unique activity identifier'),
        'activity_type': fields.String(description='Type of activity'),
        'actor': fields.String(description='Agent key or system'),
        'target_key': fields.String(description='Target object key'),
        'target_type': fields.String(description='Target type (entity, message, agent)'),
        'metadata': fields.Raw(description='Additional metadata'),
        'created_at': fields.DateTime(readonly=True),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class ActivityList(Resource):
        @ns.doc('list_activities')
        @ns.param('limit', 'Maximum results', type=int, default=50)
        @ns.param('type', 'Filter by activity type')
        @ns.param('hours', 'Look back this many hours', type=int)
        @ns.param('since', 'Activities after this ISO timestamp')
        @ns.param('until', 'Activities before this ISO timestamp')
        @ns.param('actor', 'Filter by actor (agent key)')
        @ns.marshal_with(response_model)
        def get(self):
            """List recent activities with optional filtering."""
            limit = request.args.get('limit', 50, type=int)
            activity_type = request.args.get('type')
            hours = request.args.get('hours', type=int)
            since_str = request.args.get('since')
            until_str = request.args.get('until')
            actor = request.args.get('actor')

            # Parse timestamps
            since = None
            until = None

            if since_str:
                try:
                    since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid since timestamp'}, 400

            if until_str:
                try:
                    until = datetime.fromisoformat(until_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid until timestamp'}, 400

            activities = activity_service.get_recent(
                limit=limit,
                activity_type=activity_type,
                hours=hours,
                since=since,
                until=until,
                actor=actor
            )

            return {
                'success': True,
                'msg': f'Found {len(activities)} activities',
                'data': {
                    'activities': [a.to_dict() for a in activities],
                    'count': len(activities)
                }
            }

    @ns.route('/summary')
    class ActivitySummary(Resource):
        @ns.doc('get_activity_summary')
        @ns.param('hours', 'Look back this many hours', type=int, default=24)
        @ns.param('since', 'Count activities after this ISO timestamp')
        @ns.param('until', 'Count activities before this ISO timestamp')
        @ns.marshal_with(response_model)
        def get(self):
            """Get aggregated activity counts by type."""
            hours = request.args.get('hours', 24, type=int)
            since_str = request.args.get('since')
            until_str = request.args.get('until')

            since = None
            until = None

            if since_str:
                try:
                    since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid since timestamp'}, 400

            if until_str:
                try:
                    until = datetime.fromisoformat(until_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid until timestamp'}, 400

            summary = activity_service.get_summary(
                hours=hours if not since else None,
                since=since,
                until=until
            )

            return {
                'success': True,
                'msg': 'Activity summary retrieved',
                'data': summary
            }

    @ns.route('/timeline')
    class ActivityTimeline(Resource):
        @ns.doc('get_activity_timeline')
        @ns.param('hours', 'Look back this many hours', type=int, default=24)
        @ns.param('bucket_minutes', 'Time bucket size in minutes', type=int, default=60)
        @ns.param('since', 'Start from this ISO timestamp')
        @ns.marshal_with(response_model)
        def get(self):
            """Get time-bucketed activity data for charts."""
            hours = request.args.get('hours', 24, type=int)
            bucket_minutes = request.args.get('bucket_minutes', 60, type=int)
            since_str = request.args.get('since')

            since = None
            if since_str:
                try:
                    since = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid since timestamp'}, 400

            timeline = activity_service.get_timeline(
                hours=hours,
                bucket_minutes=bucket_minutes,
                since=since
            )

            return {
                'success': True,
                'msg': f'Timeline with {len(timeline)} data points',
                'data': {
                    'timeline': timeline,
                    'hours': hours,
                    'bucket_minutes': bucket_minutes
                }
            }

    @ns.route('/types')
    class ActivityTypes(Resource):
        @ns.doc('list_activity_types')
        @ns.marshal_with(response_model)
        def get(self):
            """Get list of available activity types."""
            types = Activity.get_activity_types()

            return {
                'success': True,
                'msg': f'Found {len(types)} activity types',
                'data': {
                    'types': types
                }
            }

    @ns.route('/purge')
    class ActivityPurge(Resource):
        @ns.doc('purge_activities')
        @ns.marshal_with(response_model)
        def post(self):
            """Manually trigger purge of old activities."""
            try:
                deleted = activity_service.purge_old()
                return {
                    'success': True,
                    'msg': f'Purged {deleted} old activity records',
                    'data': {
                        'deleted': deleted,
                        'retention_days': Activity.RETENTION_DAYS
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
