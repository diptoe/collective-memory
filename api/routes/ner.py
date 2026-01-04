"""
Collective Memory Platform - NER Routes

Named Entity Recognition endpoints for extracting entities from text.
"""

from flask import request
from flask_restx import Api, Resource, Namespace, fields

from api.services import ner_service


def register_ner_routes(api: Api):
    """Register NER routes with the API."""

    ns = api.namespace(
        'ner',
        description='Named Entity Recognition operations',
        path='/ner'
    )

    # Define models for OpenAPI documentation
    extract_request = ns.model('ExtractRequest', {
        'text': fields.String(required=True, description='Text to extract entities from'),
        'auto_create': fields.Boolean(
            description='Automatically create entities that do not exist',
            default=False
        ),
    })

    response_model = ns.model('Response', {
        'success': fields.Boolean(description='Operation success status'),
        'msg': fields.String(description='Response message'),
        'data': fields.Raw(description='Response data'),
    })

    @ns.route('/extract')
    class NERExtract(Resource):
        @ns.doc('extract_entities')
        @ns.expect(extract_request)
        @ns.marshal_with(response_model)
        def post(self):
            """
            Extract named entities from text using spaCy NER.

            Returns extracted entities with their types and positions.
            Optionally creates new entities in the knowledge graph.
            """
            data = request.json

            if not data.get('text'):
                return {'success': False, 'msg': 'text is required'}, 400

            text = data['text']
            auto_create = data.get('auto_create', False)

            try:
                result = ner_service.extract_and_link(
                    text=text,
                    auto_create=auto_create
                )

                total_extracted = len(result['extracted'])
                existing_count = len(result['existing'])
                created_count = len(result['created'])
                suggestions_count = len(result['suggestions'])

                msg_parts = [f'Extracted {total_extracted} entities']
                if existing_count:
                    msg_parts.append(f'{existing_count} existing')
                if created_count:
                    msg_parts.append(f'{created_count} created')
                if suggestions_count:
                    msg_parts.append(f'{suggestions_count} suggested')

                return {
                    'success': True,
                    'msg': ', '.join(msg_parts),
                    'data': result
                }

            except RuntimeError as e:
                # spaCy model not loaded
                return {'success': False, 'msg': str(e)}, 500
            except Exception as e:
                return {'success': False, 'msg': f'Extraction error: {str(e)}'}, 500

    @ns.route('/labels')
    class NERLabels(Resource):
        @ns.doc('get_ner_labels')
        @ns.marshal_with(response_model)
        def get(self):
            """
            Get supported NER labels and their entity type mappings.

            Returns the mapping from spaCy labels to Collective Memory entity types.
            """
            return {
                'success': True,
                'msg': 'NER label mappings',
                'data': {
                    'label_map': ner_service.get_supported_labels(),
                    'supported_labels': list(ner_service.LABEL_MAP.keys()),
                    'target_types': list(set(ner_service.LABEL_MAP.values())),
                }
            }
