"""
Collective Memory Platform - Domain Routes

Admin endpoints for domain management.
"""
from flask import request, g
from flask_restx import Api, Resource, Namespace, fields

from api.models import Domain, User, db
from api.services.auth import require_admin
from api.services.activity import activity_service


def get_user_domain_key() -> str | None:
    """Get the current user's domain_key for multi-tenancy filtering."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.domain_key
    return None


def get_user_key() -> str | None:
    """Get the current user's user_key for activity tracking."""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.user_key
    return None


def register_domain_routes(api: Api):
    """Register domain routes with the API."""

    ns = api.namespace(
        'domains',
        description='Domain management (admin only)',
        path='/domains'
    )

    # Define models for OpenAPI documentation
    domain_model = ns.model('Domain', {
        'domain_key': fields.String(readonly=True, description='Unique domain identifier'),
        'name': fields.String(description='Domain display name'),
        'slug': fields.String(description='Domain slug (usually email domain)'),
        'description': fields.String(description='Domain description'),
        'owner_key': fields.String(description='Owner user key'),
        'status': fields.String(description='Domain status: active, suspended'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    create_domain_model = ns.model('CreateDomainRequest', {
        'name': fields.String(required=True, description='Domain display name'),
        'slug': fields.String(required=True, description='Domain slug (e.g., email domain)'),
        'description': fields.String(description='Domain description'),
        'owner_key': fields.String(description='Owner user key (optional)'),
    })

    update_domain_model = ns.model('UpdateDomainRequest', {
        'name': fields.String(description='Domain display name'),
        'description': fields.String(description='Domain description'),
        'owner_key': fields.String(description='Owner user key (null to remove)'),
        'status': fields.String(description='Domain status: active, suspended'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class DomainList(Resource):
        @ns.doc('list_domains')
        @require_admin
        def get(self):
            """List all domains."""
            status = request.args.get('status')

            query = Domain.query

            if status:
                query = query.filter(Domain.status == status)

            domains = query.order_by(Domain.name).all()

            # Get user counts per domain
            domain_data = []
            for domain in domains:
                d = domain.to_dict()
                d['user_count'] = User.query.filter_by(domain_key=domain.domain_key).count()
                domain_data.append(d)

            return {
                'success': True,
                'msg': f'Found {len(domains)} domains',
                'data': {
                    'domains': domain_data
                }
            }

        @ns.doc('create_domain')
        @ns.expect(create_domain_model)
        @require_admin
        def post(self):
            """Create a new domain."""
            data = request.json or {}

            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400
            if not data.get('slug'):
                return {'success': False, 'msg': 'slug is required'}, 400

            slug = data['slug'].lower().strip()

            # Check if slug already exists
            if Domain.get_by_slug(slug):
                return {'success': False, 'msg': 'Domain with this slug already exists'}, 409

            # Validate owner if provided
            owner_key = data.get('owner_key')
            if owner_key:
                owner = User.get_by_key(owner_key)
                if not owner:
                    return {'success': False, 'msg': 'Owner not found'}, 404

            try:
                domain = Domain(
                    name=data['name'].strip(),
                    slug=slug,
                    description=data.get('description'),
                    owner_key=owner_key,
                    status='active',
                )
                domain.save()

                # Record activity
                activity_service.record_create(
                    actor=g.current_user.user_key,
                    entity_type='Domain',
                    entity_key=domain.domain_key,
                    entity_name=domain.name,
                    changes={'slug': slug, 'owner_key': owner_key},
                    domain_key=get_user_domain_key(),
                    user_key=get_user_key()
                )

                return {
                    'success': True,
                    'msg': 'Domain created successfully',
                    'data': {
                        'domain': domain.to_dict()
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:domain_key>')
    @ns.param('domain_key', 'Domain identifier')
    class DomainDetail(Resource):
        @ns.doc('get_domain')
        @require_admin
        def get(self, domain_key):
            """Get domain details."""
            domain = Domain.get_by_key(domain_key)
            if not domain:
                return {'success': False, 'msg': 'Domain not found'}, 404

            domain_data = domain.to_dict()
            domain_data['user_count'] = User.query.filter_by(domain_key=domain.domain_key).count()

            # Get owner info if exists
            if domain.owner_key:
                owner = User.get_by_key(domain.owner_key)
                if owner:
                    domain_data['owner'] = {
                        'user_key': owner.user_key,
                        'display_name': owner.display_name,
                        'email': owner.email,
                    }

            return {
                'success': True,
                'msg': 'Domain retrieved',
                'data': {
                    'domain': domain_data
                }
            }

        @ns.doc('update_domain')
        @ns.expect(update_domain_model)
        @require_admin
        def put(self, domain_key):
            """Update domain."""
            domain = Domain.get_by_key(domain_key)
            if not domain:
                return {'success': False, 'msg': 'Domain not found'}, 404

            data = request.json or {}
            changes = {}

            if 'name' in data:
                changes['name'] = {'old': domain.name, 'new': data['name']}
                domain.name = data['name'].strip()

            if 'description' in data:
                changes['description'] = {'old': domain.description, 'new': data['description']}
                domain.description = data['description']

            if 'owner_key' in data:
                new_owner_key = data['owner_key']
                if new_owner_key:
                    owner = User.get_by_key(new_owner_key)
                    if not owner:
                        return {'success': False, 'msg': 'Owner not found'}, 404
                changes['owner_key'] = {'old': domain.owner_key, 'new': new_owner_key}
                domain.owner_key = new_owner_key

            if 'status' in data:
                if data['status'] not in ('active', 'suspended'):
                    return {'success': False, 'msg': 'Invalid status'}, 400
                changes['status'] = {'old': domain.status, 'new': data['status']}
                domain.status = data['status']

            try:
                domain.save()

                # Record activity
                if changes:
                    activity_service.record_update(
                        actor=g.current_user.user_key,
                        entity_type='Domain',
                        entity_key=domain.domain_key,
                        entity_name=domain.name,
                        changes=changes,
                        domain_key=get_user_domain_key(),
                        user_key=get_user_key()
                    )

                return {
                    'success': True,
                    'msg': 'Domain updated',
                    'data': {
                        'domain': domain.to_dict()
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:domain_key>/users')
    @ns.param('domain_key', 'Domain identifier')
    class DomainUsers(Resource):
        @ns.doc('get_domain_users')
        @require_admin
        def get(self, domain_key):
            """List users in a domain."""
            domain = Domain.get_by_key(domain_key)
            if not domain:
                return {'success': False, 'msg': 'Domain not found'}, 404

            users = User.query.filter_by(domain_key=domain_key).order_by(User.email).all()

            return {
                'success': True,
                'msg': f'Found {len(users)} users in domain',
                'data': {
                    'domain': domain.to_dict(),
                    'users': [u.to_dict() for u in users]
                }
            }

    @ns.route('/stats')
    class DomainStats(Resource):
        @ns.doc('get_domain_stats')
        @require_admin
        def get(self):
            """Get domain statistics."""
            total = Domain.query.count()
            active = Domain.query.filter_by(status='active').count()
            suspended = Domain.query.filter_by(status='suspended').count()
            with_owner = Domain.query.filter(Domain.owner_key.isnot(None)).count()

            # Users with/without domains
            users_with_domain = User.query.filter(User.domain_key.isnot(None)).count()
            users_without_domain = User.query.filter(User.domain_key.is_(None)).count()

            return {
                'success': True,
                'msg': 'Domain stats retrieved',
                'data': {
                    'total': total,
                    'active': active,
                    'suspended': suspended,
                    'with_owner': with_owner,
                    'users_with_domain': users_with_domain,
                    'users_without_domain': users_without_domain,
                }
            }
