"""
Collective Memory Platform - Test Data Factory

CMDataFactory provides lazy-loaded, session-scoped test fixtures
following Jai API patterns for practical scenario testing.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


class CMDataFactory:
    """
    Test data factory for Collective Memory platform.

    Features:
    - Lazy-loaded fixtures via properties
    - Session-scoped for test isolation
    - Get-or-create patterns
    - Cascade cleanup support
    - Realistic test data generation

    Usage:
        @pytest.fixture(scope='session')
        def factory(app):
            with app.app_context():
                factory = CMDataFactory()
                yield factory
                factory.cleanup()

        def test_entity_creation(factory):
            entity = factory.entity
            assert entity.name == 'Test Entity'
    """

    def __init__(self):
        """Initialize factory with empty caches."""
        self._entities: Dict[str, Any] = {}
        self._relationships: Dict[str, Any] = {}
        self._personas: Dict[str, Any] = {}
        self._conversations: Dict[str, Any] = {}
        self._chat_messages: Dict[str, Any] = {}
        self._agents: Dict[str, Any] = {}
        self._messages: Dict[str, Any] = {}

        # Track created objects for cleanup
        self._created_objects: List[Any] = []

    # ========== Entity Fixtures ==========

    @property
    def entity(self) -> 'Entity':
        """Get or create a default test entity (Person)."""
        return self.get_entity('default')

    @property
    def entity_person(self) -> 'Entity':
        """Get or create a test Person entity."""
        return self.get_entity('person')

    @property
    def entity_project(self) -> 'Entity':
        """Get or create a test Project entity."""
        return self.get_entity('project')

    @property
    def entity_technology(self) -> 'Entity':
        """Get or create a test Technology entity."""
        return self.get_entity('technology')

    @property
    def entity_organization(self) -> 'Entity':
        """Get or create a test Organization entity."""
        return self.get_entity('organization')

    def get_entity(self, key: str = 'default', **overrides) -> 'Entity':
        """
        Get or create an entity by key.

        Args:
            key: Unique identifier for this fixture
            **overrides: Override default values
        """
        if key in self._entities:
            return self._entities[key]

        from api.models import Entity

        defaults = self._entity_defaults(key)
        defaults.update(overrides)

        entity = Entity(**defaults)
        entity.save()

        self._entities[key] = entity
        self._created_objects.append(entity)
        return entity

    def _entity_defaults(self, key: str) -> dict:
        """Get default values for entity based on key."""
        templates = {
            'default': {
                'entity_type': 'Person',
                'name': 'Test Entity',
                'properties': {'role': 'tester'},
                'context_domain': 'test',
                'confidence': 1.0,
                'source': 'test-factory'
            },
            'person': {
                'entity_type': 'Person',
                'name': 'John Tester',
                'properties': {'email': 'john@test.com', 'role': 'developer'},
                'context_domain': 'work.testing',
                'confidence': 1.0,
                'source': 'test-factory'
            },
            'project': {
                'entity_type': 'Project',
                'name': 'Test Project',
                'properties': {'status': 'active', 'priority': 'high'},
                'context_domain': 'work.testing',
                'confidence': 1.0,
                'source': 'test-factory'
            },
            'technology': {
                'entity_type': 'Technology',
                'name': 'Python',
                'properties': {'version': '3.11', 'category': 'language'},
                'context_domain': 'technology',
                'confidence': 1.0,
                'source': 'test-factory'
            },
            'organization': {
                'entity_type': 'Organization',
                'name': 'Test Corp',
                'properties': {'industry': 'technology'},
                'context_domain': 'business',
                'confidence': 1.0,
                'source': 'test-factory'
            }
        }
        return templates.get(key, templates['default']).copy()

    def create_entity(self, entity_type: str, name: str, **kwargs) -> 'Entity':
        """
        Create a new entity with custom values.

        Always creates new, doesn't cache.
        """
        from api.models import Entity

        entity = Entity(
            entity_type=entity_type,
            name=name,
            properties=kwargs.get('properties', {}),
            context_domain=kwargs.get('context_domain', 'test'),
            confidence=kwargs.get('confidence', 1.0),
            source=kwargs.get('source', 'test-factory')
        )
        entity.save()

        self._created_objects.append(entity)
        return entity

    # ========== Relationship Fixtures ==========

    @property
    def relationship(self) -> 'Relationship':
        """Get or create a default test relationship."""
        return self.get_relationship('default')

    def get_relationship(self, key: str = 'default', **overrides) -> 'Relationship':
        """Get or create a relationship by key."""
        if key in self._relationships:
            return self._relationships[key]

        from api.models import Relationship

        # Ensure entities exist
        from_entity = overrides.pop('from_entity', None) or self.entity_person
        to_entity = overrides.pop('to_entity', None) or self.entity_project

        defaults = {
            'from_entity_key': from_entity.entity_key,
            'to_entity_key': to_entity.entity_key,
            'relationship_type': 'WORKS_ON',
            'properties': {'since': '2024'},
            'confidence': 1.0
        }
        defaults.update(overrides)

        relationship = Relationship(**defaults)
        relationship.save()

        self._relationships[key] = relationship
        self._created_objects.append(relationship)
        return relationship

    def create_relationship(self, from_entity: 'Entity', to_entity: 'Entity',
                           relationship_type: str, **kwargs) -> 'Relationship':
        """Create a new relationship between entities."""
        from api.models import Relationship

        relationship = Relationship(
            from_entity_key=from_entity.entity_key,
            to_entity_key=to_entity.entity_key,
            relationship_type=relationship_type,
            properties=kwargs.get('properties', {}),
            confidence=kwargs.get('confidence', 1.0)
        )
        relationship.save()

        self._created_objects.append(relationship)
        return relationship

    # ========== Persona Fixtures ==========

    @property
    def persona(self) -> 'Persona':
        """Get or create a default test persona."""
        return self.get_persona('default')

    @property
    def persona_backend(self) -> 'Persona':
        """Get or create a backend developer persona."""
        return self.get_persona('backend')

    @property
    def persona_frontend(self) -> 'Persona':
        """Get or create a frontend developer persona."""
        return self.get_persona('frontend')

    def get_persona(self, key: str = 'default', **overrides) -> 'Persona':
        """Get or create a persona by key."""
        if key in self._personas:
            return self._personas[key]

        from api.models import Persona

        defaults = self._persona_defaults(key)
        defaults.update(overrides)

        persona = Persona(**defaults)
        persona.save()

        self._personas[key] = persona
        self._created_objects.append(persona)
        return persona

    def _persona_defaults(self, key: str) -> dict:
        """Get default values for persona based on key."""
        templates = {
            'default': {
                'name': 'Test Persona',
                'model': 'test-model',
                'role': 'tester',
                'color': '#888888',
                'system_prompt': 'You are a test persona.',
                'personality': {'traits': ['helpful']},
                'capabilities': ['testing'],
                'status': 'active'
            },
            'backend': {
                'name': 'Test Backend',
                'model': 'claude-3-opus',
                'role': 'backend-code',
                'color': '#d97757',
                'system_prompt': 'You are a backend developer.',
                'personality': {'traits': ['technical', 'precise']},
                'capabilities': ['python', 'api', 'database'],
                'status': 'active'
            },
            'frontend': {
                'name': 'Test Frontend',
                'model': 'claude-3-opus',
                'role': 'frontend-code',
                'color': '#e8a756',
                'system_prompt': 'You are a frontend developer.',
                'personality': {'traits': ['creative', 'user-focused']},
                'capabilities': ['react', 'css', 'typescript'],
                'status': 'active'
            }
        }
        return templates.get(key, templates['default']).copy()

    # ========== Conversation Fixtures ==========

    @property
    def conversation(self) -> 'Conversation':
        """Get or create a default test conversation."""
        return self.get_conversation('default')

    def get_conversation(self, key: str = 'default', **overrides) -> 'Conversation':
        """Get or create a conversation by key."""
        if key in self._conversations:
            return self._conversations[key]

        from api.models import Conversation

        # Ensure persona exists
        persona = overrides.pop('persona', None) or self.persona

        defaults = {
            'persona_key': persona.persona_key,
            'summary': f'Test conversation with {persona.name}',
            'extracted_entities': [],
            'extra_data': {'source': 'test-factory'}
        }
        defaults.update(overrides)

        conversation = Conversation(**defaults)
        conversation.save()

        self._conversations[key] = conversation
        self._created_objects.append(conversation)
        return conversation

    # ========== Chat Message Fixtures ==========

    @property
    def chat_message(self) -> 'ChatMessage':
        """Get or create a default test chat message."""
        return self.get_chat_message('default')

    def get_chat_message(self, key: str = 'default', **overrides) -> 'ChatMessage':
        """Get or create a chat message by key."""
        if key in self._chat_messages:
            return self._chat_messages[key]

        from api.models import ChatMessage

        # Ensure conversation exists
        conversation = overrides.pop('conversation', None) or self.conversation

        defaults = {
            'conversation_key': conversation.conversation_key,
            'role': 'user',
            'content': 'This is a test message.',
            'extra_data': {}
        }
        defaults.update(overrides)

        message = ChatMessage(**defaults)
        message.save()

        self._chat_messages[key] = message
        self._created_objects.append(message)
        return message

    def create_chat_message(self, conversation: 'Conversation', role: str,
                            content: str, **kwargs) -> 'ChatMessage':
        """Create a new chat message."""
        from api.models import ChatMessage

        message = ChatMessage(
            conversation_key=conversation.conversation_key,
            persona_key=kwargs.get('persona_key'),
            role=role,
            content=content,
            extra_data=kwargs.get('extra_data', {})
        )
        message.save()

        self._created_objects.append(message)
        return message

    # ========== Agent Fixtures ==========

    @property
    def agent(self) -> 'Agent':
        """Get or create a default test agent."""
        return self.get_agent('default')

    def get_agent(self, key: str = 'default', **overrides) -> 'Agent':
        """Get or create an agent by key."""
        if key in self._agents:
            return self._agents[key]

        from api.models import Agent

        defaults = {
            'agent_id': f'test-agent-{key}',
            'role': 'tester',
            'capabilities': ['testing'],
            'status': {'state': 'idle'}
        }
        defaults.update(overrides)

        agent = Agent(**defaults)
        agent.save()

        self._agents[key] = agent
        self._created_objects.append(agent)
        return agent

    # ========== Inter-Agent Message Fixtures ==========

    @property
    def message(self) -> 'Message':
        """Get or create a default test inter-agent message."""
        return self.get_message('default')

    def get_message(self, key: str = 'default', **overrides) -> 'Message':
        """Get or create an inter-agent message by key."""
        if key in self._messages:
            return self._messages[key]

        from api.models import Message

        defaults = {
            'channel': 'test-channel',
            'from_agent': 'test-agent',
            'to_agent': None,
            'message_type': 'announcement',
            'content': {'text': 'Test message'},
            'priority': 'normal'
        }
        defaults.update(overrides)

        message = Message(**defaults)
        message.save()

        self._messages[key] = message
        self._created_objects.append(message)
        return message

    # ========== Scenario Builders ==========

    def create_project_scenario(self) -> dict:
        """
        Create a complete project scenario with related entities.

        Returns dict with all created objects for easy access.
        """
        # Create entities
        developer = self.create_entity('Person', 'Alice Developer',
                                       properties={'role': 'lead developer'})
        project = self.create_entity('Project', 'Phoenix',
                                     properties={'status': 'active'})
        technology = self.create_entity('Technology', 'Flask',
                                        properties={'version': '3.0'})
        company = self.create_entity('Organization', 'Acme Corp')

        # Create relationships
        works_on = self.create_relationship(developer, project, 'WORKS_ON')
        uses_tech = self.create_relationship(project, technology, 'USES_TECHNOLOGY')
        belongs_to = self.create_relationship(developer, company, 'BELONGS_TO')

        return {
            'developer': developer,
            'project': project,
            'technology': technology,
            'company': company,
            'relationships': [works_on, uses_tech, belongs_to]
        }

    def create_conversation_scenario(self) -> dict:
        """
        Create a complete conversation scenario with messages.

        Returns dict with all created objects.
        """
        persona = self.get_persona('backend')
        conversation = self.get_conversation('scenario', persona=persona)

        messages = [
            self.create_chat_message(conversation, 'user',
                                     'Help me design a REST API'),
            self.create_chat_message(conversation, 'assistant',
                                     'I recommend using Flask-RESTX...',
                                     persona_key=persona.persona_key),
            self.create_chat_message(conversation, 'user',
                                     'How should I structure the endpoints?'),
        ]

        return {
            'persona': persona,
            'conversation': conversation,
            'messages': messages
        }

    def create_multi_agent_scenario(self) -> dict:
        """
        Create a multi-agent collaboration scenario.

        Returns dict with agents and messages.
        """
        backend_agent = self.get_agent('backend',
                                       agent_id='backend-code',
                                       role='backend-code',
                                       capabilities=['python', 'api'])
        frontend_agent = self.get_agent('frontend',
                                        agent_id='frontend-code',
                                        role='frontend-code',
                                        capabilities=['react', 'typescript'])

        # Create inter-agent messages
        handoff = self.get_message('handoff',
                                   channel='coordination',
                                   from_agent='backend-code',
                                   to_agent='frontend-code',
                                   message_type='handoff',
                                   content={'task': 'API integration ready'})

        return {
            'backend_agent': backend_agent,
            'frontend_agent': frontend_agent,
            'messages': [handoff]
        }

    # ========== Cleanup ==========

    def cleanup(self):
        """
        Clean up all created objects.

        Deletes in reverse order to handle foreign key constraints.
        """
        from api.models.base import db

        # Delete in reverse order
        for obj in reversed(self._created_objects):
            try:
                db.session.delete(obj)
            except Exception:
                pass  # Already deleted or detached

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Clear caches
        self._entities.clear()
        self._relationships.clear()
        self._personas.clear()
        self._conversations.clear()
        self._chat_messages.clear()
        self._agents.clear()
        self._messages.clear()
        self._created_objects.clear()

    def reset(self):
        """Alias for cleanup."""
        self.cleanup()
