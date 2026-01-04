"""
Collective Memory Platform - Model Tests

Tests for SQLAlchemy models using CMDataFactory.
"""
import pytest


class TestEntity:
    """Tests for Entity model."""

    @pytest.mark.model
    def test_entity_creation(self, factory):
        """Test creating an entity via factory."""
        entity = factory.entity
        assert entity is not None
        assert entity.entity_key is not None
        assert entity.name == 'Test Entity'
        assert entity.entity_type == 'Person'

    @pytest.mark.model
    def test_entity_person(self, factory):
        """Test creating a person entity."""
        person = factory.entity_person
        assert person.entity_type == 'Person'
        assert person.name == 'John Tester'
        assert person.properties.get('email') == 'john@test.com'

    @pytest.mark.model
    def test_entity_project(self, factory):
        """Test creating a project entity."""
        project = factory.entity_project
        assert project.entity_type == 'Project'
        assert project.name == 'Test Project'

    @pytest.mark.model
    def test_entity_custom(self, factory):
        """Test creating a custom entity."""
        entity = factory.create_entity(
            'Document',
            'API Specification',
            properties={'format': 'OpenAPI'}
        )
        assert entity.entity_type == 'Document'
        assert entity.name == 'API Specification'


class TestRelationship:
    """Tests for Relationship model."""

    @pytest.mark.model
    def test_relationship_creation(self, factory):
        """Test creating a relationship."""
        rel = factory.relationship
        assert rel is not None
        assert rel.relationship_type == 'WORKS_ON'

    @pytest.mark.model
    def test_custom_relationship(self, factory):
        """Test creating a custom relationship."""
        person = factory.entity_person
        tech = factory.entity_technology

        rel = factory.create_relationship(
            person, tech, 'KNOWS_TECHNOLOGY',
            properties={'proficiency': 'expert'}
        )
        assert rel.relationship_type == 'KNOWS_TECHNOLOGY'
        assert rel.from_entity_key == person.entity_key
        assert rel.to_entity_key == tech.entity_key


class TestPersona:
    """Tests for Persona model."""

    @pytest.mark.model
    def test_persona_creation(self, factory):
        """Test creating a persona."""
        persona = factory.persona
        assert persona is not None
        assert persona.name == 'Test Persona'
        assert persona.status == 'active'

    @pytest.mark.model
    def test_persona_backend(self, factory):
        """Test backend developer persona."""
        persona = factory.persona_backend
        assert persona.role == 'backend-code'
        assert 'python' in persona.capabilities


class TestConversation:
    """Tests for Conversation model."""

    @pytest.mark.model
    def test_conversation_creation(self, factory):
        """Test creating a conversation."""
        conv = factory.conversation
        assert conv is not None
        assert conv.persona_key is not None

    @pytest.mark.model
    def test_chat_message_creation(self, factory):
        """Test creating a chat message."""
        msg = factory.chat_message
        assert msg is not None
        assert msg.role == 'user'
        assert msg.content == 'This is a test message.'


class TestAgent:
    """Tests for Agent model."""

    @pytest.mark.model
    def test_agent_creation(self, factory):
        """Test creating an agent."""
        agent = factory.agent
        assert agent is not None
        assert agent.agent_id == 'test-agent-default'


class TestMessage:
    """Tests for inter-agent Message model."""

    @pytest.mark.model
    def test_message_creation(self, factory):
        """Test creating an inter-agent message."""
        msg = factory.message
        assert msg is not None
        assert msg.channel == 'test-channel'
        assert msg.message_type == 'announcement'


class TestScenarios:
    """Tests for scenario builders."""

    @pytest.mark.scenario
    def test_project_scenario(self, project_scenario):
        """Test project scenario setup."""
        assert project_scenario['developer'] is not None
        assert project_scenario['project'] is not None
        assert project_scenario['technology'] is not None
        assert project_scenario['company'] is not None
        assert len(project_scenario['relationships']) == 3

    @pytest.mark.scenario
    def test_conversation_scenario(self, conversation_scenario):
        """Test conversation scenario setup."""
        assert conversation_scenario['persona'] is not None
        assert conversation_scenario['conversation'] is not None
        assert len(conversation_scenario['messages']) == 3

    @pytest.mark.scenario
    def test_multi_agent_scenario(self, multi_agent_scenario):
        """Test multi-agent scenario setup."""
        assert multi_agent_scenario['backend_agent'] is not None
        assert multi_agent_scenario['frontend_agent'] is not None
        assert len(multi_agent_scenario['messages']) == 1
