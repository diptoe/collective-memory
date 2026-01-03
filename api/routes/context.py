"""
Collective Memory Platform - Context Routes

Context injection queries for the knowledge graph.
"""
from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.utils.graph import GraphTraversal


def register_context_routes(api: Api):
    """Register context routes with the API."""

    ns = api.namespace(
        'context',
        description='Context injection operations',
        path='/context'
    )

    # Define models for OpenAPI documentation
    context_query = ns.model('ContextQuery', {
        'query': fields.String(required=True, description='Query text to find context for'),
        'max_entities': fields.Integer(description='Maximum entities to return', default=20),
        'max_tokens': fields.Integer(description='Approximate token budget', default=4000),
    })

    subgraph_query = ns.model('SubgraphQuery', {
        'entity_keys': fields.List(fields.String, required=True, description='Entity keys to include'),
        'include_relationships': fields.Boolean(description='Include relationships', default=True),
    })

    neighbors_query = ns.model('NeighborsQuery', {
        'entity_key': fields.String(required=True, description='Starting entity key'),
        'max_hops': fields.Integer(description='Maximum hops to traverse', default=1),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('/query')
    class ContextQuery(Resource):
        @ns.doc('query_context')
        @ns.expect(context_query)
        @ns.marshal_with(response_model)
        def post(self):
            """
            Get relevant context for a query.

            Searches the knowledge graph for entities and relationships
            relevant to the query text. Returns a context suitable for
            injection into AI model prompts.
            """
            data = request.json

            if not data.get('query'):
                return {'success': False, 'msg': 'query is required'}, 400

            max_entities = data.get('max_entities', 20)
            max_tokens = data.get('max_tokens', 4000)

            result = GraphTraversal.get_context_for_query(
                data['query'],
                max_entities=max_entities,
                max_tokens=max_tokens
            )

            return {
                'success': True,
                'msg': f"Found {result['entity_count']} entities, {result['relationship_count']} relationships",
                'data': result
            }

    @ns.route('/subgraph')
    class SubgraphQuery(Resource):
        @ns.doc('get_subgraph')
        @ns.expect(subgraph_query)
        @ns.marshal_with(response_model)
        def post(self):
            """
            Get a subgraph containing specific entities.

            Returns the specified entities and their relationships.
            """
            data = request.json

            if not data.get('entity_keys'):
                return {'success': False, 'msg': 'entity_keys is required'}, 400

            include_relationships = data.get('include_relationships', True)

            result = GraphTraversal.get_subgraph(
                data['entity_keys'],
                include_relationships=include_relationships
            )

            return {
                'success': True,
                'msg': f"Retrieved {len(result['entities'])} entities",
                'data': result
            }

    @ns.route('/neighbors')
    class NeighborsQuery(Resource):
        @ns.doc('get_neighbors')
        @ns.expect(neighbors_query)
        @ns.marshal_with(response_model)
        def post(self):
            """
            Get neighboring entities within N hops.

            Traverses the graph from the starting entity and returns
            all entities and relationships within the specified hop distance.
            """
            data = request.json

            if not data.get('entity_key'):
                return {'success': False, 'msg': 'entity_key is required'}, 400

            max_hops = data.get('max_hops', 1)

            result = GraphTraversal.get_neighbors(
                data['entity_key'],
                max_hops=max_hops
            )

            return {
                'success': True,
                'msg': f"Found {len(result['entities'])} neighboring entities",
                'data': result
            }
