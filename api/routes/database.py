"""
Collective Memory Platform - Database Routes

Admin endpoints for database statistics and health monitoring.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields
from sqlalchemy import text, inspect

from api.models.base import db
from api.services.auth import require_auth


def register_database_routes(api: Api):
    """Register database admin routes with the API."""

    ns = api.namespace(
        'database',
        description='Database administration and statistics',
        path='/database'
    )

    # Response models
    table_stats_model = ns.model('TableStats', {
        'table_name': fields.String(description='Database table name'),
        'row_count': fields.Integer(description='Number of rows'),
        'has_domain_key': fields.Boolean(description='Whether table has domain_key column'),
        'domain_filtered_count': fields.Integer(description='Count filtered by domain (if applicable)'),
    })

    response_model = ns.model('DatabaseStatsResponse', {
        'success': fields.Boolean(),
        'msg': fields.String(),
        'data': fields.Raw(),
    })

    @ns.route('/stats')
    class DatabaseStats(Resource):
        @ns.doc('get_database_stats')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Get database table statistics.

            System admins see all tables with total counts.
            Domain admins see domain-filtered counts for tables with domain_key.

            Query params:
            - domain_key: Filter counts by domain (system admin only)
            """
            from flask import g

            # Check authorization
            user = g.current_user
            if user.role not in ('admin', 'domain_admin'):
                return {'success': False, 'msg': 'Admin access required'}, 403

            # Get domain filter
            domain_key = request.args.get('domain_key')

            # Domain admins can only see their own domain
            if user.role == 'domain_admin':
                domain_key = user.domain_key

            # Get all table names from the database
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()

            stats = []
            total_rows = 0
            total_domain_rows = 0

            for table_name in sorted(table_names):
                # Skip internal/system tables
                if table_name.startswith('pg_') or table_name.startswith('sql_'):
                    continue

                # Get columns to check for domain_key
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                has_domain_key = 'domain_key' in columns

                # Get total count
                try:
                    result = db.session.execute(
                        text(f'SELECT COUNT(*) FROM "{table_name}"')
                    )
                    row_count = result.scalar() or 0
                except Exception:
                    row_count = -1  # Error reading table

                # Get domain-filtered count if applicable
                domain_filtered_count = None
                if has_domain_key and domain_key:
                    try:
                        result = db.session.execute(
                            text(f'SELECT COUNT(*) FROM "{table_name}" WHERE domain_key = :dk'),
                            {'dk': domain_key}
                        )
                        domain_filtered_count = result.scalar() or 0
                    except Exception:
                        domain_filtered_count = -1

                stats.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'has_domain_key': has_domain_key,
                    'domain_filtered_count': domain_filtered_count,
                })

                if row_count > 0:
                    total_rows += row_count
                if domain_filtered_count and domain_filtered_count > 0:
                    total_domain_rows += domain_filtered_count

            return {
                'success': True,
                'msg': 'Database statistics retrieved',
                'data': {
                    'tables': stats,
                    'total_tables': len(stats),
                    'total_rows': total_rows,
                    'total_domain_rows': total_domain_rows if domain_key else None,
                    'domain_key': domain_key,
                    'scope': 'domain' if domain_key else 'all',
                }
            }

    @ns.route('/health')
    class DatabaseHealth(Resource):
        @ns.doc('get_database_health')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """
            Check database connectivity and basic health.
            """
            from flask import g

            # Check authorization - admin only
            user = g.current_user
            if user.role not in ('admin', 'domain_admin'):
                return {'success': False, 'msg': 'Admin access required'}, 403

            try:
                # Test database connection
                result = db.session.execute(text('SELECT 1'))
                result.scalar()

                # Get database version
                version_result = db.session.execute(text('SELECT version()'))
                db_version = version_result.scalar()

                # Get database size (PostgreSQL specific)
                size_result = db.session.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                db_size = size_result.scalar()

                # Get connection info
                conn_result = db.session.execute(
                    text("SELECT current_database(), current_user")
                )
                conn_info = conn_result.fetchone()

                return {
                    'success': True,
                    'msg': 'Database is healthy',
                    'data': {
                        'status': 'healthy',
                        'database': conn_info[0] if conn_info else None,
                        'user': conn_info[1] if conn_info else None,
                        'version': db_version,
                        'size': db_size,
                    }
                }
            except Exception as e:
                return {
                    'success': False,
                    'msg': f'Database health check failed: {str(e)}',
                    'data': {
                        'status': 'unhealthy',
                        'error': str(e),
                    }
                }, 500
