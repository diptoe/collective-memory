"""
Collective Memory Platform - Conversation Tests

Tests for conversation and message operations.
"""
import pytest
import json


class TestConversationCreation:
    """Tests for creating conversations."""

    @pytest.mark.conversation
    def test_create_conversation(self, api_client, factory):
        """Test creating a new conversation."""
        persona = factory.persona

        response = api_client.post(
            '/api/conversations',
            data=json.dumps({'persona_key': persona.persona_key}),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['persona_key'] == persona.persona_key

    @pytest.mark.conversation
    def test_create_conversation_with_title(self, api_client, factory):
        """Test creating conversation with custom title."""
        persona = factory.persona

        response = api_client.post(
            '/api/conversations',
            data=json.dumps({
                'persona_key': persona.persona_key,
                'title': 'My Custom Chat'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['title'] == 'My Custom Chat'

    @pytest.mark.conversation
    def test_create_conversation_with_initial_message(self, api_client, factory):
        """Test creating conversation with initial message."""
        persona = factory.persona

        response = api_client.post(
            '/api/conversations',
            data=json.dumps({
                'persona_key': persona.persona_key,
                'initial_message': 'Hello, this is my first message!'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True

        # Verify message was created
        conv_key = data['data']['conversation_key']
        messages_response = api_client.get(f'/api/conversations/{conv_key}/messages')
        messages_data = messages_response.get_json()
        assert len(messages_data['data']['messages']) == 1
        assert messages_data['data']['messages'][0]['content'] == 'Hello, this is my first message!'

    @pytest.mark.conversation
    def test_create_conversation_missing_persona(self, api_client):
        """Test creating conversation without persona fails."""
        response = api_client.post(
            '/api/conversations',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'persona_key is required' in data['msg']

    @pytest.mark.conversation
    def test_create_conversation_invalid_persona(self, api_client):
        """Test creating conversation with invalid persona fails."""
        response = api_client.post(
            '/api/conversations',
            data=json.dumps({'persona_key': 'invalid-persona-key'}),
            content_type='application/json'
        )

        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'Persona not found' in data['msg']


class TestConversationListing:
    """Tests for listing conversations."""

    @pytest.mark.conversation
    def test_list_conversations(self, api_client, factory):
        """Test listing all conversations."""
        # Create a conversation
        conv = factory.conversation

        response = api_client.get('/api/conversations')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'conversations' in data['data']

    @pytest.mark.conversation
    def test_list_conversations_by_persona(self, api_client, factory):
        """Test filtering conversations by persona."""
        conv = factory.conversation

        response = api_client.get(
            f'/api/conversations?persona_key={conv.persona_key}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # All returned conversations should have matching persona
        for c in data['data']['conversations']:
            assert c['persona_key'] == conv.persona_key

    @pytest.mark.conversation
    def test_list_conversations_with_limit(self, api_client, factory):
        """Test limiting conversation results."""
        # Create multiple conversations using get_conversation with unique keys
        for i in range(5):
            factory.get_conversation(key=f'conv-{i}')

        response = api_client.get('/api/conversations?limit=3')

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['conversations']) <= 3


class TestConversationDetail:
    """Tests for conversation detail operations."""

    @pytest.mark.conversation
    def test_get_conversation(self, api_client, factory):
        """Test getting conversation details."""
        conv = factory.conversation

        response = api_client.get(f'/api/conversations/{conv.conversation_key}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['conversation_key'] == conv.conversation_key

    @pytest.mark.conversation
    def test_get_conversation_with_messages(self, api_client, factory):
        """Test getting conversation includes messages."""
        scenario = factory.create_conversation_scenario()
        conv = scenario['conversation']

        response = api_client.get(
            f'/api/conversations/{conv.conversation_key}?include_messages=true'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'messages' in data['data']
        assert len(data['data']['messages']) > 0

    @pytest.mark.conversation
    def test_get_nonexistent_conversation(self, api_client):
        """Test getting non-existent conversation returns 404."""
        response = api_client.get('/api/conversations/nonexistent-key')

        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False

    @pytest.mark.conversation
    def test_update_conversation(self, api_client, factory):
        """Test updating conversation metadata."""
        conv = factory.conversation

        response = api_client.put(
            f'/api/conversations/{conv.conversation_key}',
            data=json.dumps({
                'title': 'Updated Title',
                'summary': 'This is a summary'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Updated Title'

    @pytest.mark.conversation
    def test_delete_conversation(self, api_client, factory):
        """Test deleting a conversation."""
        conv = factory.conversation

        response = api_client.delete(f'/api/conversations/{conv.conversation_key}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify it's deleted
        get_response = api_client.get(f'/api/conversations/{conv.conversation_key}')
        assert get_response.status_code == 404


class TestMessages:
    """Tests for message operations."""

    @pytest.mark.conversation
    def test_send_message(self, api_client, factory):
        """Test sending a message to conversation."""
        conv = factory.conversation

        response = api_client.post(
            f'/api/conversations/{conv.conversation_key}/messages',
            data=json.dumps({'content': 'Hello, world!'}),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['content'] == 'Hello, world!'
        assert data['data']['role'] == 'user'

    @pytest.mark.conversation
    def test_send_message_with_role(self, api_client, factory):
        """Test sending a message with specific role."""
        conv = factory.conversation

        response = api_client.post(
            f'/api/conversations/{conv.conversation_key}/messages',
            data=json.dumps({
                'content': 'I am the assistant',
                'role': 'assistant'
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['role'] == 'assistant'

    @pytest.mark.conversation
    def test_send_message_with_extra_data(self, api_client, factory):
        """Test sending a message with extra metadata."""
        conv = factory.conversation

        response = api_client.post(
            f'/api/conversations/{conv.conversation_key}/messages',
            data=json.dumps({
                'content': 'Message with metadata',
                'extra_data': {'source': 'test', 'priority': 'high'}
            }),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['extra_data']['source'] == 'test'

    @pytest.mark.conversation
    def test_send_message_empty_content(self, api_client, factory):
        """Test sending empty message fails."""
        conv = factory.conversation

        response = api_client.post(
            f'/api/conversations/{conv.conversation_key}/messages',
            data=json.dumps({'content': ''}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    @pytest.mark.conversation
    def test_get_messages(self, api_client, factory):
        """Test getting messages from conversation."""
        scenario = factory.create_conversation_scenario()
        conv = scenario['conversation']

        response = api_client.get(
            f'/api/conversations/{conv.conversation_key}/messages'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'messages' in data['data']
        assert 'total' in data['data']

    @pytest.mark.conversation
    def test_get_messages_with_pagination(self, api_client, factory):
        """Test message pagination."""
        conv = factory.conversation

        # Add several messages
        for i in range(10):
            factory.create_chat_message(conv, role='user', content=f'Message {i}')

        response = api_client.get(
            f'/api/conversations/{conv.conversation_key}/messages?limit=5&offset=2'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['messages']) <= 5

    @pytest.mark.conversation
    def test_clear_conversation_deletes_all_messages(self, api_client, factory):
        """DELETE /conversations/<key>/clear removes all messages but keeps the conversation."""
        conv = factory.conversation

        # Add some messages
        for i in range(3):
            factory.create_chat_message(conv, role='user', content=f'Message {i}')

        # Sanity check: messages exist
        before = api_client.get(f'/api/conversations/{conv.conversation_key}')
        assert before.status_code == 200
        assert len(before.get_json()['data']['messages']) >= 3

        # Clear messages
        clear_resp = api_client.delete(f'/api/conversations/{conv.conversation_key}/clear')
        assert clear_resp.status_code == 200
        clear_data = clear_resp.get_json()
        assert clear_data['success'] is True
        assert clear_data['data']['conversation_key'] == conv.conversation_key
        assert clear_data['data']['deleted'] == 3
        assert clear_data['data']['message_count'] == 0

        # Conversation still exists and messages are gone
        after = api_client.get(f'/api/conversations/{conv.conversation_key}')
        assert after.status_code == 200
        assert len(after.get_json()['data']['messages']) == 0

        # Messages endpoint also returns 0
        after_messages = api_client.get(f'/api/conversations/{conv.conversation_key}/messages')
        assert after_messages.status_code == 200
        after_messages_data = after_messages.get_json()
        assert after_messages_data['success'] is True
        assert after_messages_data['data']['total'] == 0


class TestConversationScenarios:
    """Tests for complete conversation scenarios."""

    @pytest.mark.scenario
    def test_full_conversation_flow(self, api_client, factory):
        """Test complete conversation flow: create, message, retrieve."""
        persona = factory.persona

        # Create conversation
        create_response = api_client.post(
            '/api/conversations',
            data=json.dumps({'persona_key': persona.persona_key}),
            content_type='application/json'
        )
        assert create_response.status_code == 201
        conv_key = create_response.get_json()['data']['conversation_key']

        # Send messages
        for msg in ['Hello', 'How are you?', 'Goodbye']:
            msg_response = api_client.post(
                f'/api/conversations/{conv_key}/messages',
                data=json.dumps({'content': msg}),
                content_type='application/json'
            )
            assert msg_response.status_code == 201

        # Retrieve conversation with messages
        get_response = api_client.get(f'/api/conversations/{conv_key}')
        assert get_response.status_code == 200
        data = get_response.get_json()
        assert len(data['data']['messages']) == 3

    @pytest.mark.scenario
    def test_conversation_scenario_fixture(self, conversation_scenario):
        """Test conversation scenario provides expected data."""
        assert conversation_scenario['persona'] is not None
        assert conversation_scenario['conversation'] is not None
        assert len(conversation_scenario['messages']) >= 1

        # Messages belong to the conversation
        for msg in conversation_scenario['messages']:
            assert msg.conversation_key == conversation_scenario['conversation'].conversation_key
