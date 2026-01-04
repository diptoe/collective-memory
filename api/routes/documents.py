"""
Collective Memory Platform - Document Routes

CRUD operations for documents with embedding support.
"""

from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Document, Entity, db
from api.services import embedding_service, document_processor


def register_document_routes(api: Api):
    """Register document routes with the API."""

    ns = api.namespace(
        'documents',
        description='Document operations with embedding support',
        path='/documents'
    )

    # Define models for OpenAPI documentation
    document_model = ns.model('Document', {
        'document_key': fields.String(readonly=True, description='Unique document identifier'),
        'title': fields.String(required=True, description='Document title'),
        'content': fields.String(required=True, description='Document content'),
        'content_type': fields.String(description='Content type (markdown, text)', default='markdown'),
        'metadata': fields.Raw(description='Additional metadata as JSON'),
        'source': fields.String(description='Source identifier'),
        'entity_key': fields.String(description='Linked entity key'),
        'has_embedding': fields.Boolean(readonly=True, description='Whether document has embedding'),
        'created_at': fields.DateTime(readonly=True),
        'updated_at': fields.DateTime(readonly=True),
    })

    document_create = ns.model('DocumentCreate', {
        'title': fields.String(required=True, description='Document title'),
        'content': fields.String(required=True, description='Document content'),
        'content_type': fields.String(description='Content type', default='markdown'),
        'metadata': fields.Raw(description='Additional metadata'),
        'source': fields.String(description='Source identifier'),
        'entity_key': fields.String(description='Linked entity key'),
        'generate_embedding': fields.Boolean(description='Generate embedding on create', default=False),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('')
    class DocumentList(Resource):
        @ns.doc('list_documents')
        @ns.param('type', 'Filter by content type')
        @ns.param('entity_key', 'Filter by linked entity')
        @ns.param('search', 'Search by title')
        @ns.param('limit', 'Maximum results', type=int, default=50)
        @ns.param('offset', 'Offset for pagination', type=int, default=0)
        @ns.marshal_with(response_model)
        def get(self):
            """List documents with optional filtering."""
            content_type = request.args.get('type')
            entity_key = request.args.get('entity_key')
            search = request.args.get('search')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)

            query = Document.query

            if content_type:
                query = query.filter_by(content_type=content_type)
            if entity_key:
                query = query.filter_by(entity_key=entity_key)
            if search:
                query = query.filter(Document.title.ilike(f'%{search}%'))

            total = query.count()
            documents = query.order_by(Document.created_at.desc()).limit(limit).offset(offset).all()

            return {
                'success': True,
                'msg': f'Found {total} documents',
                'data': {
                    'documents': [d.to_dict(include_content=False) for d in documents],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
            }

        @ns.doc('create_document')
        @ns.expect(document_create)
        @ns.marshal_with(response_model, code=201)
        def post(self):
            """Create a new document."""
            data = request.json

            if not data.get('title'):
                return {'success': False, 'msg': 'title is required'}, 400
            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Validate entity_key if provided
            if data.get('entity_key'):
                entity = Entity.get_by_key(data['entity_key'])
                if not entity:
                    return {'success': False, 'msg': 'Entity not found'}, 404

            document = Document(
                title=data['title'],
                content=data['content'],
                content_type=data.get('content_type', 'markdown'),
                extra_data=data.get('extra_data') or data.get('metadata', {}),
                source=data.get('source'),
                entity_key=data.get('entity_key')
            )

            try:
                # Generate embedding if requested
                if data.get('generate_embedding', False):
                    document.generate_embedding(embedding_service)

                document.save()
                return {
                    'success': True,
                    'msg': 'Document created',
                    'data': document.to_dict()
                }, 201
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:document_key>')
    @ns.param('document_key', 'Document identifier')
    class DocumentDetail(Resource):
        @ns.doc('get_document')
        @ns.param('include_content', 'Include full content', type=bool, default=True)
        @ns.marshal_with(response_model)
        def get(self, document_key):
            """Get a document by key."""
            include_content = request.args.get('include_content', 'true').lower() == 'true'

            document = Document.get_by_key(document_key)
            if not document:
                return {'success': False, 'msg': 'Document not found'}, 404

            return {
                'success': True,
                'msg': 'Document retrieved',
                'data': document.to_dict(include_content=include_content)
            }

        @ns.doc('update_document')
        @ns.expect(document_create)
        @ns.marshal_with(response_model)
        def put(self, document_key):
            """Update a document."""
            document = Document.get_by_key(document_key)
            if not document:
                return {'success': False, 'msg': 'Document not found'}, 404

            data = request.json

            # Validate entity_key if provided
            if data.get('entity_key'):
                entity = Entity.get_by_key(data['entity_key'])
                if not entity:
                    return {'success': False, 'msg': 'Entity not found'}, 404

            # Update fields
            if 'title' in data:
                document.title = data['title']
            if 'content' in data:
                document.content = data['content']
            if 'content_type' in data:
                document.content_type = data['content_type']
            if 'extra_data' in data:
                document.extra_data = data['extra_data']
            if 'metadata' in data:
                document.extra_data = data['metadata']
            if 'source' in data:
                document.source = data['source']
            if 'entity_key' in data:
                document.entity_key = data['entity_key']

            try:
                # Regenerate embedding if content changed and requested
                if data.get('generate_embedding', False):
                    document.generate_embedding(embedding_service)

                document.save()
                return {
                    'success': True,
                    'msg': 'Document updated',
                    'data': document.to_dict()
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

        @ns.doc('delete_document')
        @ns.marshal_with(response_model)
        def delete(self, document_key):
            """Delete a document."""
            document = Document.get_by_key(document_key)
            if not document:
                return {'success': False, 'msg': 'Document not found'}, 404

            try:
                document.delete()
                return {
                    'success': True,
                    'msg': 'Document deleted',
                    'data': None
                }
            except Exception as e:
                return {'success': False, 'msg': str(e)}, 500

    @ns.route('/<string:document_key>/embed')
    @ns.param('document_key', 'Document identifier')
    class DocumentEmbed(Resource):
        @ns.doc('embed_document')
        @ns.marshal_with(response_model)
        def post(self, document_key):
            """Generate embedding for a document."""
            document = Document.get_by_key(document_key)
            if not document:
                return {'success': False, 'msg': 'Document not found'}, 404

            try:
                document.generate_embedding(embedding_service)
                document.save()
                return {
                    'success': True,
                    'msg': 'Embedding generated',
                    'data': {
                        'document_key': document.document_key,
                        'has_embedding': True
                    }
                }
            except Exception as e:
                return {'success': False, 'msg': f'Embedding error: {str(e)}'}, 500

    @ns.route('/ingest')
    class DocumentIngest(Resource):
        @ns.doc('ingest_document')
        @ns.marshal_with(response_model, code=201)
        def post(self):
            """
            Process and embed a markdown document.

            Splits document into chunks and creates embeddings.
            Returns the main document with chunk metadata.
            """
            data = request.json

            if not data.get('title'):
                return {'success': False, 'msg': 'title is required'}, 400
            if not data.get('content'):
                return {'success': False, 'msg': 'content is required'}, 400

            # Validate entity_key if provided
            if data.get('entity_key'):
                entity = Entity.get_by_key(data['entity_key'])
                if not entity:
                    return {'success': False, 'msg': 'Entity not found'}, 404

            try:
                # Process document into chunks
                chunks = document_processor.process_markdown(
                    data['content'],
                    title=data['title'],
                    source=data.get('source')
                )

                # Create main document
                document = Document(
                    title=data['title'],
                    content=data['content'],
                    content_type=data.get('content_type', 'markdown'),
                    extra_data={
                        **data.get('metadata', {}),
                        'chunk_count': len(chunks),
                    },
                    source=data.get('source'),
                    entity_key=data.get('entity_key')
                )

                # Generate embedding for main document
                document.generate_embedding(embedding_service)
                document.save()

                return {
                    'success': True,
                    'msg': f'Document ingested with {len(chunks)} chunks',
                    'data': {
                        'document': document.to_dict(),
                        'chunks': document_processor.chunks_to_dict(chunks)
                    }
                }, 201

            except Exception as e:
                return {'success': False, 'msg': f'Ingest error: {str(e)}'}, 500
