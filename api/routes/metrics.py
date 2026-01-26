"""
Collective Memory Platform - Metrics Routes

API endpoints for time-series metrics storage and retrieval.
"""
from datetime import datetime, timezone
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models.metric import Metric, MetricTypes
from api.models.base import db
from api.services.auth import require_auth, require_write_access


def register_metric_routes(api: Api):
    """Register metric routes with the API."""

    ns = api.namespace(
        'metrics',
        description='Time-series metrics storage and retrieval',
        path='/metrics'
    )

    metric_model = ns.model('Metric', {
        'metric_key': fields.String(readonly=True, description='Unique metric identifier'),
        'entity_key': fields.String(required=True, description='Entity this metric belongs to'),
        'metric_type': fields.String(required=True, description='Type of metric'),
        'value': fields.Float(required=True, description='Numeric value'),
        'recorded_at': fields.DateTime(description='When the metric was recorded'),
        'extra': fields.Raw(description='Additional context'),
        'tags': fields.List(fields.String, description='Optional tags'),
        'created_at': fields.DateTime(readonly=True),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    batch_metric_model = ns.model('BatchMetric', {
        'metric_type': fields.String(required=True, description='Type of metric'),
        'value': fields.Float(required=True, description='Numeric value'),
        'extra': fields.Raw(description='Additional context'),
        'tags': fields.List(fields.String, description='Optional tags'),
    })

    batch_request_model = ns.model('BatchMetricsRequest', {
        'entity_key': fields.String(required=True, description='Entity for all metrics'),
        'metrics': fields.List(fields.Nested(batch_metric_model), required=True, description='Metrics to record'),
        'recorded_at': fields.DateTime(description='Shared timestamp for all metrics'),
    })

    @ns.route('')
    class MetricList(Resource):
        @ns.doc('list_metrics')
        @ns.param('entity_key', 'Filter by entity key', required=True)
        @ns.param('metric_type', 'Filter by metric type')
        @ns.param('limit', 'Maximum results', type=int, default=100)
        @ns.param('offset', 'Pagination offset', type=int, default=0)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """Get metrics for an entity, optionally filtered by type."""
            entity_key = request.args.get('entity_key')
            if not entity_key:
                return {'success': False, 'msg': 'entity_key is required'}, 400

            metric_type = request.args.get('metric_type')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            metrics = Metric.get_for_entity(
                entity_key=entity_key,
                metric_type=metric_type,
                limit=limit,
                offset=offset
            )

            return {
                'success': True,
                'msg': f'Found {len(metrics)} metrics',
                'data': {
                    'metrics': [m.to_dict() for m in metrics],
                    'count': len(metrics)
                }
            }

        @ns.doc('create_metric')
        @ns.expect(metric_model)
        @ns.marshal_with(response_model)
        @require_write_access
        def post(self):
            """Record a single metric value. Requires write access."""
            data = request.get_json()

            entity_key = data.get('entity_key')
            metric_type = data.get('metric_type')
            value = data.get('value')

            if not entity_key or not metric_type or value is None:
                return {'success': False, 'msg': 'entity_key, metric_type, and value are required'}, 400

            try:
                recorded_at = None
                if data.get('recorded_at'):
                    recorded_at = datetime.fromisoformat(data['recorded_at'].replace('Z', '+00:00'))

                metric = Metric.record(
                    entity_key=entity_key,
                    metric_type=metric_type,
                    value=float(value),
                    recorded_at=recorded_at,
                    extra=data.get('extra'),
                    tags=data.get('tags')
                )
                db.session.commit()

                return {
                    'success': True,
                    'msg': 'Metric recorded',
                    'data': {'metric': metric.to_dict()}
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/batch')
    class MetricBatch(Resource):
        @ns.doc('batch_metrics')
        @ns.expect(batch_request_model)
        @ns.marshal_with(response_model)
        @require_write_access
        def post(self):
            """
            Record multiple metrics for an entity at once. Requires write access.

            All metrics share the same entity_key and recorded_at timestamp.
            Useful for recording all milestone metrics together.
            """
            data = request.get_json()

            entity_key = data.get('entity_key')
            metrics_data = data.get('metrics', [])

            if not entity_key:
                return {'success': False, 'msg': 'entity_key is required'}, 400

            if not metrics_data:
                return {'success': False, 'msg': 'metrics array is required'}, 400

            try:
                # Shared timestamp for all metrics
                recorded_at = None
                if data.get('recorded_at'):
                    recorded_at = datetime.fromisoformat(data['recorded_at'].replace('Z', '+00:00'))
                else:
                    recorded_at = datetime.now(timezone.utc)

                created_metrics = []
                for m in metrics_data:
                    metric_type = m.get('metric_type')
                    value = m.get('value')

                    if not metric_type or value is None:
                        continue  # Skip invalid entries

                    metric = Metric.record(
                        entity_key=entity_key,
                        metric_type=metric_type,
                        value=float(value),
                        recorded_at=recorded_at,
                        extra=m.get('extra'),
                        tags=m.get('tags')
                    )
                    created_metrics.append(metric)

                db.session.commit()

                return {
                    'success': True,
                    'msg': f'Recorded {len(created_metrics)} metrics',
                    'data': {
                        'metrics': [m.to_dict() for m in created_metrics],
                        'count': len(created_metrics)
                    }
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/latest')
    class MetricLatest(Resource):
        @ns.doc('get_latest_metric')
        @ns.param('entity_key', 'Entity key', required=True)
        @ns.param('metric_type', 'Metric type', required=True)
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """Get the most recent metric of a type for an entity."""
            entity_key = request.args.get('entity_key')
            metric_type = request.args.get('metric_type')

            if not entity_key or not metric_type:
                return {'success': False, 'msg': 'entity_key and metric_type are required'}, 400

            metric = Metric.get_latest(entity_key=entity_key, metric_type=metric_type)

            if not metric:
                return {
                    'success': True,
                    'msg': 'No metric found',
                    'data': {'metric': None}
                }

            return {
                'success': True,
                'msg': 'Found metric',
                'data': {'metric': metric.to_dict()}
            }

    @ns.route('/time-series')
    class MetricTimeSeries(Resource):
        @ns.doc('get_time_series')
        @ns.param('entity_key', 'Entity key', required=True)
        @ns.param('metric_type', 'Metric type', required=True)
        @ns.param('start_date', 'Start date (ISO format)')
        @ns.param('end_date', 'End date (ISO format)')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """Get time series data for charting."""
            entity_key = request.args.get('entity_key')
            metric_type = request.args.get('metric_type')
            start_str = request.args.get('start_date')
            end_str = request.args.get('end_date')

            if not entity_key or not metric_type:
                return {'success': False, 'msg': 'entity_key and metric_type are required'}, 400

            start_date = None
            end_date = None

            if start_str:
                try:
                    start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid start_date format'}, 400

            if end_str:
                try:
                    end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                except ValueError:
                    return {'success': False, 'msg': 'Invalid end_date format'}, 400

            metrics = Metric.get_time_series(
                entity_key=entity_key,
                metric_type=metric_type,
                start_date=start_date,
                end_date=end_date
            )

            return {
                'success': True,
                'msg': f'Found {len(metrics)} data points',
                'data': {
                    'time_series': [m.to_dict() for m in metrics],
                    'count': len(metrics)
                }
            }
