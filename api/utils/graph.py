"""
Collective Memory Platform - Graph Traversal Utilities

Utilities for traversing the knowledge graph and building context.
"""
from typing import Optional, TYPE_CHECKING
from collections import deque

from api.models import Entity, Relationship

if TYPE_CHECKING:
    from api.models.user import User


class GraphTraversal:
    """
    Utilities for traversing the knowledge graph.

    Provides methods for:
    - Finding connected entities
    - Building context subgraphs
    - Path finding between entities
    """

    @staticmethod
    def get_neighbors(entity_key: str, max_hops: int = 1, user: 'User' = None) -> dict:
        """
        Get entities within N hops of the given entity.

        Args:
            entity_key: Starting entity key
            max_hops: Maximum hops to traverse
            user: Optional user for scope filtering

        Returns:
            dict with 'entities' and 'relationships' lists
        """
        from api.services.scope import scope_service

        visited_entities = {entity_key}
        visited_relationships = set()
        entities = []
        relationships = []

        # BFS traversal
        queue = deque([(entity_key, 0)])

        while queue:
            current_key, depth = queue.popleft()

            if depth >= max_hops:
                continue

            # Get relationships from this entity
            rels = Relationship.query.filter(
                (Relationship.from_entity_key == current_key) |
                (Relationship.to_entity_key == current_key)
            ).all()

            for rel in rels:
                if rel.relationship_key not in visited_relationships:
                    visited_relationships.add(rel.relationship_key)
                    relationships.append(rel)

                # Get the other entity
                other_key = rel.to_entity_key if rel.from_entity_key == current_key else rel.from_entity_key

                if other_key not in visited_entities:
                    visited_entities.add(other_key)
                    entity = Entity.get_by_key(other_key)
                    if entity:
                        # Check scope access if user provided
                        if user:
                            if not scope_service.can_access_scope(
                                user,
                                entity.scope_type,
                                entity.scope_key or entity.domain_key
                            ):
                                continue  # Skip entities user can't access
                        entities.append(entity)
                        queue.append((other_key, depth + 1))

        return {
            'entities': [e.to_dict() for e in entities],
            'relationships': [r.to_dict() for r in relationships]
        }

    @staticmethod
    def get_context_for_query(
        query_text: str,
        max_entities: int = 20,
        max_tokens: int = 4000,
        user: 'User' = None
    ) -> dict:
        """
        Get relevant context for a query.

        This is a simple implementation that:
        1. Searches for entities matching keywords in the query
        2. Expands to include directly connected entities
        3. Returns a subgraph suitable for context injection

        Args:
            query_text: The query to find context for
            max_entities: Maximum number of entities to return
            max_tokens: Approximate token budget (for future use)
            user: Optional user for scope filtering

        Returns:
            dict with 'entities', 'relationships', and 'context_text'
        """
        # Simple keyword extraction (split by spaces, filter short words)
        keywords = [w.lower() for w in query_text.split() if len(w) > 3]

        # Search for matching entities (with scope filtering)
        matching_entities = []
        for keyword in keywords[:5]:  # Limit keywords to prevent too many queries
            matches = Entity.search_by_name(keyword, limit=5, user=user)
            matching_entities.extend(matches)

        # Deduplicate
        seen_keys = set()
        unique_entities = []
        for entity in matching_entities:
            if entity.entity_key not in seen_keys:
                seen_keys.add(entity.entity_key)
                unique_entities.append(entity)

        # Limit to max_entities
        unique_entities = unique_entities[:max_entities]

        # Get relationships between matched entities
        entity_keys = [e.entity_key for e in unique_entities]
        relationships = Relationship.query.filter(
            (Relationship.from_entity_key.in_(entity_keys)) &
            (Relationship.to_entity_key.in_(entity_keys))
        ).all()

        # Build context text
        context_lines = ["## Relevant Context\n"]
        for entity in unique_entities:
            context_lines.append(f"- **{entity.name}** ({entity.entity_type}): {entity.properties}")

        if relationships:
            context_lines.append("\n## Relationships\n")
            for rel in relationships:
                from_entity = Entity.get_by_key(rel.from_entity_key)
                to_entity = Entity.get_by_key(rel.to_entity_key)
                if from_entity and to_entity:
                    context_lines.append(
                        f"- {from_entity.name} --[{rel.relationship_type}]--> {to_entity.name}"
                    )

        return {
            'entities': [e.to_dict() for e in unique_entities],
            'relationships': [r.to_dict() for r in relationships],
            'context_text': '\n'.join(context_lines),
            'entity_count': len(unique_entities),
            'relationship_count': len(relationships)
        }

    @staticmethod
    def get_subgraph(
        entity_keys: list[str],
        include_relationships: bool = True,
        user: 'User' = None
    ) -> dict:
        """
        Get a subgraph containing the specified entities and their relationships.

        Args:
            entity_keys: List of entity keys to include
            include_relationships: Whether to include relationships between entities
            user: Optional user for scope filtering

        Returns:
            dict with 'entities' and 'relationships'
        """
        from api.services.scope import scope_service

        entities = []
        accessible_keys = []

        for key in entity_keys:
            entity = Entity.get_by_key(key)
            if entity:
                # Check scope access if user provided
                if user:
                    if not scope_service.can_access_scope(
                        user,
                        entity.scope_type,
                        entity.scope_key or entity.domain_key
                    ):
                        continue  # Skip entities user can't access
                entities.append(entity)
                accessible_keys.append(key)

        relationships = []
        if include_relationships and accessible_keys:
            relationships = Relationship.query.filter(
                (Relationship.from_entity_key.in_(accessible_keys)) &
                (Relationship.to_entity_key.in_(accessible_keys))
            ).all()

        return {
            'entities': [e.to_dict() for e in entities],
            'relationships': [r.to_dict() for r in relationships]
        }
