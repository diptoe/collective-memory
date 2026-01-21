"""
Collective Memory Platform - Model Routes

CRUD operations for AI models.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Model, Client, db
from api.services.auth import require_admin


def register_model_routes(api: Api):
    """Register model routes with the API."""

    ns = api.namespace(
        'models',
        description='AI model operations',
        path='/models'
    )

    # Define models for OpenAPI documentation
    model_schema = ns.model('Model', {
        'model_key': fields.String(readonly=True, description='Unique model identifier'),
        'name': fields.String(required=True, description='Human-readable model name'),
        'provider': fields.String(required=True, description='Provider: anthropic, openai, google'),
        'model_id': fields.String(required=True, description='API model identifier'),
        'capabilities': fields.List(fields.String, description='Model capabilities'),
        'context_window': fields.Integer(description='Context window size'),
        'max_output_tokens': fields.Integer(description='Maximum output tokens'),
        'description': fields.String(description='Model description'),
        'status': fields.String(description='Status: active, deprecated, disabled'),
        'client_key': fields.String(description='Linked client key'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    model_create = ns.model('ModelCreate', {
        'name': fields.String(required=True, description='Human-readable model name'),
        'provider': fields.String(required=True, description='Provider: anthropic, openai, google'),
        'model_id': fields.String(required=True, description='API model identifier'),
        'capabilities': fields.List(fields.String, description='Model capabilities'),
        'context_window': fields.Integer(description='Context window size'),
        'max_output_tokens': fields.Integer(description='Maximum output tokens'),
        'description': fields.String(description='Model description'),
        'status': fields.String(description='Status: active, deprecated, disabled', default='active'),
        'client_key': fields.String(description='Linked client key (e.g., client-claude-code)'),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    def _expand_model(model: Model) -> dict:
        """Expand model to include client info."""
        data = model.to_dict()
        if model.client_key and model.client:
            data['client'] = {
                'client_key': model.client.client_key,
                'name': model.client.name,
                'publisher': model.client.publisher,
            }
        return data

    @ns.route('')
    class ModelList(Resource):
        @ns.doc('list_models')
        @ns.param('provider', 'Filter by provider (anthropic, openai, google)')
        @ns.param('client_key', 'Filter by client key')
        @ns.param('status', 'Filter by status', default='active')
        @ns.param('limit', 'Maximum results', type=int, default=100)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.param('expand', 'Include related objects (client)', type=bool, default=True)
        @ns.marshal_with(response_model)
        def get(self):
            """List AI models with optional filtering."""
            provider = request.args.get('provider')
            client_key = request.args.get('client_key')
            status = request.args.get('status', 'active')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            expand = request.args.get('expand', 'true').lower() == 'true'

            query = Model.query

            if provider:
                query = query.filter_by(provider=provider)
            if client_key:
                # Support both formats: client-claude-code and claude-code
                if not client_key.startswith('client-'):
                    client_key = f'client-{client_key}'
                query = query.filter_by(client_key=client_key)
            if status:
                query = query.filter_by(status=status)

            total = query.count()
            models = query.limit(limit).offset(offset).all()

            return {
                'success': True,
                'msg': f'Found {total} models',
                'data': {
                    'models': [_expand_model(m) if expand else m.to_dict() for m in models],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

        @ns.doc('create_model')
        @ns.expect(model_create)
        @ns.marshal_with(response_model, code=201)
        @require_admin
        def post(self):
            """Create a new AI model. Requires admin role."""
            data = request.json

            if not data.get('name'):
                return {'success': False, 'msg': 'name is required'}, 400
            if not data.get('provider'):
                return {'success': False, 'msg': 'provider is required'}, 400
            if not data.get('model_id'):
                return {'success': False, 'msg': 'model_id is required'}, 400

            # Check for duplicate model_id
            existing = Model.get_by_model_id(data['model_id'])
            if existing:
                return {'success': False, 'msg': f"Model with model_id '{data['model_id']}' already exists"}, 400

            # Validate client_key if provided
            client_key = data.get('client_key')
            if client_key:
                if not client_key.startswith('client-'):
                    client_key = f'client-{client_key}'
                client = Client.get_by_key(client_key)
                if not client:
                    return {'success': False, 'msg': f"Client not found: '{client_key}'"}, 400

            model = Model(
                name=data['name'],
                provider=data['provider'],
                model_id=data['model_id'],
                capabilities=data.get('capabilities', []),
                context_window=data.get('context_window'),
                max_output_tokens=data.get('max_output_tokens'),
                description=data.get('description'),
                status=data.get('status', 'active'),
                client_key=client_key
            )

            try:
                model.save()
                return {
                    'success': True,
                    'msg': 'Model created',
                    'data': _expand_model(model)
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/providers')
    class ModelProviders(Resource):
        @ns.doc('list_providers')
        @ns.marshal_with(response_model)
        def get(self):
            """Get all distinct providers with model counts."""
            from sqlalchemy import func

            results = db.session.query(
                Model.provider,
                func.count(Model.model_key).label('count')
            ).filter_by(status='active').group_by(Model.provider).order_by(Model.provider).all()

            providers = [
                {'provider': row.provider, 'count': row.count}
                for row in results
            ]

            return {
                'success': True,
                'msg': f'Found {len(providers)} providers',
                'data': {
                    'providers': providers
                }
            }

    @ns.route('/by-provider/<string:provider>')
    @ns.param('provider', 'Provider name (anthropic, openai, google)')
    class ModelsByProvider(Resource):
        @ns.doc('get_models_by_provider')
        @ns.marshal_with(response_model)
        def get(self, provider):
            """Get all models for a specific provider."""
            models = Model.get_by_provider(provider)

            return {
                'success': True,
                'msg': f'Found {len(models)} models for provider {provider}',
                'data': {
                    'models': [_expand_model(m) for m in models]
                }
            }

    @ns.route('/by-model-id/<string:model_id>')
    @ns.param('model_id', 'API model identifier (e.g., claude-opus-4-5-20251101)')
    class ModelByModelId(Resource):
        @ns.doc('get_model_by_model_id')
        @ns.marshal_with(response_model)
        def get(self, model_id):
            """Get a model by its API model_id.

            This allows AI agents to look up their model by the identifier they know
            (e.g., claude-opus-4-5-20251101) rather than needing the database key.
            """
            model = Model.get_by_model_id(model_id)
            if not model:
                return {'success': False, 'msg': f"Model not found: '{model_id}'"}, 404

            return {
                'success': True,
                'msg': 'Model retrieved',
                'data': _expand_model(model)
            }

    @ns.route('/<string:model_key>')
    @ns.param('model_key', 'Model identifier')
    class ModelDetail(Resource):
        @ns.doc('get_model')
        @ns.marshal_with(response_model)
        def get(self, model_key):
            """Get a model by key."""
            model = Model.get_by_key(model_key)
            if not model:
                return {'success': False, 'msg': 'Model not found'}, 404

            return {
                'success': True,
                'msg': 'Model retrieved',
                'data': _expand_model(model)
            }

        @ns.doc('update_model')
        @ns.expect(model_create)
        @ns.marshal_with(response_model)
        @require_admin
        def put(self, model_key):
            """Update a model. Requires admin role."""
            model = Model.get_by_key(model_key)
            if not model:
                return {'success': False, 'msg': 'Model not found'}, 404

            data = request.json

            # Check for duplicate model_id if being changed
            if data.get('model_id') and data['model_id'] != model.model_id:
                existing = Model.get_by_model_id(data['model_id'])
                if existing:
                    return {'success': False, 'msg': f"Model with model_id '{data['model_id']}' already exists"}, 400

            # Validate client_key if provided
            if 'client_key' in data:
                client_key = data['client_key']
                if client_key:
                    if not client_key.startswith('client-'):
                        client_key = f'client-{client_key}'
                    client = Client.get_by_key(client_key)
                    if not client:
                        return {'success': False, 'msg': f"Client not found: '{client_key}'"}, 400
                    data['client_key'] = client_key

            model.update_from_dict(data)

            try:
                model.save()
                return {
                    'success': True,
                    'msg': 'Model updated',
                    'data': _expand_model(model)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_model')
        @ns.marshal_with(response_model)
        @require_admin
        def delete(self, model_key):
            """Delete a model. Requires admin role."""
            model = Model.get_by_key(model_key)
            if not model:
                return {'success': False, 'msg': 'Model not found'}, 404

            try:
                model.delete()
                return {
                    'success': True,
                    'msg': 'Model deleted',
                    'data': None
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:model_key>/deprecate')
    @ns.param('model_key', 'Model identifier')
    class ModelDeprecate(Resource):
        @ns.doc('deprecate_model')
        @ns.marshal_with(response_model)
        @require_admin
        def post(self, model_key):
            """Mark a model as deprecated. Requires admin role."""
            model = Model.get_by_key(model_key)
            if not model:
                return {'success': False, 'msg': 'Model not found'}, 404

            try:
                model.archive()
                return {
                    'success': True,
                    'msg': 'Model deprecated',
                    'data': _expand_model(model)
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500
