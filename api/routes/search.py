"""
Collective Memory Platform - Search Routes

Semantic and hybrid search endpoints.
"""

from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.models import Entity, Document
from api.services import embedding_service


def register_search_routes(api: Api):
    """Register search routes with the API."""

    ns = api.namespace(
        'search',
        description='Semantic and hybrid search operations',
        path='/search'
    )

    # Define models for OpenAPI documentation
    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('/semantic')
    class SemanticSearch(Resource):
        @ns.doc('semantic_search')
        @ns.param('query', 'Natural language search query', required=True)
        @ns.param('type', 'Filter entities by type (Person, Project, etc.)')
        @ns.param('limit', 'Maximum results per category', type=int, default=10)
        @ns.param('include_entities', 'Include entity results', type=bool, default=True)
        @ns.param('include_documents', 'Include document results', type=bool, default=True)
        @ns.marshal_with(response_model)
        def get(self):
            """
            Semantic search across entities and documents.

            Uses OpenAI embeddings for semantic similarity matching.
            """
            query = request.args.get('query')
            if not query:
                return {'success': False, 'msg': 'query parameter is required'}, 400

            entity_type = request.args.get('type')
            limit = request.args.get('limit', 10, type=int)
            include_entities = request.args.get('include_entities', 'true').lower() == 'true'
            include_documents = request.args.get('include_documents', 'true').lower() == 'true'

            try:
                # Generate query embedding
                query_embedding = embedding_service.get_embedding(query)

                results = {
                    'query': query,
                    'entities': [],
                    'documents': [],
                }

                # Search entities
                if include_entities:
                    try:
                        entities = Entity.search_semantic(
                            query_embedding,
                            limit=limit,
                            entity_type=entity_type
                        )
                        results['entities'] = [e.to_dict() for e in entities]
                    except RuntimeError as e:
                        # pgvector not available
                        results['entities_error'] = str(e)

                # Search documents
                if include_documents:
                    try:
                        documents = Document.search_semantic(
                            query_embedding,
                            limit=limit
                        )
                        results['documents'] = [
                            d.to_dict(include_content=False)
                            for d in documents
                        ]
                    except RuntimeError as e:
                        # pgvector not available
                        results['documents_error'] = str(e)

                return {
                    'success': True,
                    'msg': f'Found {len(results["entities"])} entities and {len(results["documents"])} documents',
                    'data': results
                }

            except Exception as e:
                return {'success': False, 'msg': f'Search error: {str(e)}'}, 500

    @ns.route('/hybrid')
    class HybridSearch(Resource):
        @ns.doc('hybrid_search')
        @ns.param('query', 'Search query (used for both keyword and semantic)', required=True)
        @ns.param('type', 'Filter entities by type')
        @ns.param('limit', 'Maximum results', type=int, default=10)
        @ns.marshal_with(response_model)
        def get(self):
            """
            Hybrid search combining keyword and semantic matching.

            Keyword matches are weighted higher for exact name matches.
            """
            query = request.args.get('query')
            if not query:
                return {'success': False, 'msg': 'query parameter is required'}, 400

            entity_type = request.args.get('type')
            limit = request.args.get('limit', 10, type=int)

            try:
                # Generate query embedding
                query_embedding = embedding_service.get_embedding(query)

                # Hybrid search
                entities = Entity.search_hybrid(
                    keyword=query,
                    query_embedding=query_embedding,
                    limit=limit
                )

                # Filter by type if specified
                if entity_type:
                    entities = [e for e in entities if e.entity_type == entity_type]

                return {
                    'success': True,
                    'msg': f'Found {len(entities)} entities',
                    'data': {
                        'query': query,
                        'entities': [e.to_dict() for e in entities],
                    }
                }

            except Exception as e:
                return {'success': False, 'msg': f'Search error: {str(e)}'}, 500
