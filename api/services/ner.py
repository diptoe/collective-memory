"""
Collective Memory Platform - NER Service

Named Entity Recognition using spaCy for automatic entity extraction.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Lazy load spaCy to avoid startup cost
_nlp = None


def _get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load('en_core_web_sm')
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model not found. Run: python -m spacy download en_core_web_sm"
            )
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not installed. "
                "Run: python -m spacy download en_core_web_sm"
            )
    return _nlp


@dataclass
class ExtractedEntity:
    """An entity extracted via NER."""
    name: str
    entity_type: str
    original_label: str
    start: int
    end: int
    confidence: float = 0.8


class NERService:
    """
    Named Entity Recognition service using spaCy.

    Maps spaCy entity labels to Collective Memory entity types:
    - PERSON -> Person
    - ORG -> Organization
    - GPE (geopolitical) -> Organization
    - PRODUCT -> Technology
    - WORK_OF_ART -> Document
    - EVENT -> Concept
    - LAW -> Document
    - LANGUAGE -> Technology
    """

    # Map spaCy labels to Collective Memory entity types
    LABEL_MAP = {
        'PERSON': 'Person',
        'ORG': 'Organization',
        'GPE': 'Organization',  # Geopolitical entity -> Organization
        'PRODUCT': 'Technology',
        'WORK_OF_ART': 'Document',
        'EVENT': 'Concept',
        'LAW': 'Document',
        'LANGUAGE': 'Technology',
        'NORP': 'Concept',  # Nationalities, religious/political groups
        'FAC': 'Organization',  # Facilities
        'LOC': 'Concept',  # Non-GPE locations
    }

    # Minimum entity name length
    MIN_NAME_LENGTH = 2

    def __init__(self):
        """Initialize NER service."""
        self._nlp = None

    @property
    def nlp(self):
        """Lazy load spaCy model."""
        if self._nlp is None:
            self._nlp = _get_nlp()
        return self._nlp

    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract named entities from text.

        Args:
            text: Text to extract entities from

        Returns:
            List of ExtractedEntity objects
        """
        if not text or not text.strip():
            return []

        doc = self.nlp(text)
        entities = []
        seen = set()

        for ent in doc.ents:
            # Skip unmapped labels
            if ent.label_ not in self.LABEL_MAP:
                continue

            # Skip short names
            if len(ent.text.strip()) < self.MIN_NAME_LENGTH:
                continue

            # Skip duplicates (case-insensitive)
            name_lower = ent.text.strip().lower()
            if name_lower in seen:
                continue
            seen.add(name_lower)

            entities.append(ExtractedEntity(
                name=ent.text.strip(),
                entity_type=self.LABEL_MAP[ent.label_],
                original_label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.8  # spaCy doesn't provide confidence scores
            ))

        return entities

    def extract_entities_dict(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities as dictionaries.

        Args:
            text: Text to extract entities from

        Returns:
            List of entity dictionaries
        """
        entities = self.extract_entities(text)
        return [
            {
                'name': e.name,
                'entity_type': e.entity_type,
                'original_label': e.original_label,
                'start': e.start,
                'end': e.end,
                'confidence': e.confidence,
            }
            for e in entities
        ]

    def extract_and_link(
        self,
        text: str,
        auto_create: bool = False
    ) -> Dict[str, Any]:
        """
        Extract entities and optionally create/link them in the knowledge graph.

        Args:
            text: Text to extract entities from
            auto_create: If True, create new entities that don't exist

        Returns:
            Dictionary with extracted, existing, created, and suggested entities
        """
        from sqlalchemy import func
        from api.models import Entity, db

        extracted = self.extract_entities(text)

        results = {
            'extracted': [],
            'existing': [],
            'created': [],
            'suggestions': [],
        }

        for entity_data in extracted:
            results['extracted'].append({
                'name': entity_data.name,
                'entity_type': entity_data.entity_type,
                'original_label': entity_data.original_label,
                'confidence': entity_data.confidence,
            })

            # Check if entity exists (case-insensitive name match)
            existing = Entity.query.filter(
                func.lower(Entity.name) == entity_data.name.lower()
            ).first()

            if existing:
                results['existing'].append(existing.to_dict())
            elif auto_create:
                # Create new entity
                new_entity = Entity(
                    name=entity_data.name,
                    entity_type=entity_data.entity_type,
                    source='spacy_ner',
                    confidence=entity_data.confidence
                )
                db.session.add(new_entity)
                results['created'].append({
                    'name': entity_data.name,
                    'entity_type': entity_data.entity_type,
                    'source': 'spacy_ner',
                    'confidence': entity_data.confidence,
                })
            else:
                # Add to suggestions
                results['suggestions'].append({
                    'name': entity_data.name,
                    'entity_type': entity_data.entity_type,
                    'original_label': entity_data.original_label,
                    'confidence': entity_data.confidence,
                })

        if auto_create and results['created']:
            try:
                db.session.commit()
                logger.info(f"Created {len(results['created'])} entities via NER")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating entities: {str(e)}")
                raise

        return results

    def get_supported_labels(self) -> Dict[str, str]:
        """Get mapping of supported spaCy labels to entity types."""
        return self.LABEL_MAP.copy()


# Global service instance
ner_service = NERService()
