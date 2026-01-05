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


class TestMessageRead:
    """Tests for per-agent message read tracking."""

    @pytest.mark.model
    def test_message_read_creation(self, factory):
        """Test creating a message read record."""
        msg = factory.message
        read = factory.create_message_read(msg, 'agent-1')
        assert read is not None
        assert read.message_key == msg.message_key
        assert read.agent_id == 'agent-1'
        assert read.read_at is not None

    @pytest.mark.model
    def test_mark_read_idempotent(self, factory):
        """Test that marking read twice returns same record."""
        msg = factory.message
        read1 = factory.mark_message_read_by(msg, 'agent-2')
        read2 = factory.mark_message_read_by(msg, 'agent-2')
        assert read1.read_key == read2.read_key

    @pytest.mark.model
    def test_has_read(self, factory):
        """Test checking if agent has read message."""
        from api.models import MessageRead

        msg = factory.message
        assert not MessageRead.has_read(msg.message_key, 'agent-3')

        factory.mark_message_read_by(msg, 'agent-3')
        assert MessageRead.has_read(msg.message_key, 'agent-3')

    @pytest.mark.model
    def test_per_agent_read_tracking(self, factory):
        """Test that each agent has independent read status."""
        msg = factory.message

        # Mark read by agent-a only
        factory.mark_message_read_by(msg, 'agent-a')

        # agent-a has read, agent-b has not
        assert msg.is_read_by('agent-a')
        assert not msg.is_read_by('agent-b')

    @pytest.mark.model
    def test_get_readers(self, factory):
        """Test getting list of agents who read a message."""
        msg = factory.message
        factory.mark_message_read_by(msg, 'reader-1')
        factory.mark_message_read_by(msg, 'reader-2')

        readers = msg.get_readers()
        assert 'reader-1' in readers
        assert 'reader-2' in readers
        assert len(readers) == 2

    @pytest.mark.model
    def test_to_dict_with_for_agent(self, factory):
        """Test message to_dict with per-agent read status."""
        msg = factory.message
        factory.mark_message_read_by(msg, 'agent-x')

        # For agent-x (has read)
        dict_x = msg.to_dict(for_agent='agent-x')
        assert dict_x['is_read'] is True

        # For agent-y (has not read)
        dict_y = msg.to_dict(for_agent='agent-y')
        assert dict_y['is_read'] is False

    @pytest.mark.model
    def test_get_unread_for_agent(self, factory):
        """Test getting unread messages for an agent."""
        from api.models import Message

        # Create two messages
        msg1 = factory.get_message('unread-test-1', channel='test')
        msg2 = factory.get_message('unread-test-2', channel='test')

        # Agent reads only msg1
        factory.mark_message_read_by(msg1, 'reader-agent')

        # Get unread for agent
        unread = Message.get_unread_for_agent('reader-agent', channel='test', limit=10)
        unread_keys = [m.message_key for m in unread]

        assert msg2.message_key in unread_keys
        assert msg1.message_key not in unread_keys

    @pytest.mark.model
    def test_mark_all_read_for_agent(self, factory):
        """Test marking multiple messages as read."""
        from api.models import MessageRead

        msg1 = factory.get_message('batch-1')
        msg2 = factory.get_message('batch-2')
        msg3 = factory.get_message('batch-3')

        keys = [msg1.message_key, msg2.message_key, msg3.message_key]
        count = MessageRead.mark_all_read_for_agent('batch-reader', keys)

        assert count == 3
        assert MessageRead.has_read(msg1.message_key, 'batch-reader')
        assert MessageRead.has_read(msg2.message_key, 'batch-reader')
        assert MessageRead.has_read(msg3.message_key, 'batch-reader')


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
