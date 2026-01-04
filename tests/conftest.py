"""
Collective Memory Platform - Pytest Configuration

Provides fixtures for testing the API and models.
"""
import pytest
import os
from typing import Generator

# Set test environment before importing app
os.environ['CM_ENV'] = 'test'
os.environ['DATABASE_URL'] = os.environ.get(
    'TEST_DATABASE_URL',
    'postgresql://postgres:Q57SZI@localhost:5432/collective_memory_test'
)


@pytest.fixture(scope='session')
def app():
    """
    Create application for testing.

    Session-scoped to reuse across all tests.
    """
    from api import create_app

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
    })

    yield app


@pytest.fixture(scope='session')
def db(app):
    """
    Set up database for testing.

    Creates all tables at start of session.
    """
    from api.models import db as _db

    with app.app_context():
        # Create all tables
        _db.create_all()

        yield _db


@pytest.fixture(scope='function')
def factory(app, db) -> Generator:
    """
    Provide CMDataFactory for test data creation.

    Function-scoped with automatic cleanup.
    """
    from tests.fixtures import CMDataFactory

    with app.app_context():
        factory = CMDataFactory()
        yield factory
        factory.cleanup()


@pytest.fixture(scope='function')
def client(app):
    """
    Provide Flask test client.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def api_client(app):
    """
    Provide Flask test client with JSON headers.
    """
    with app.test_client() as client:
        # Set default headers for API calls
        client.environ_base['CONTENT_TYPE'] = 'application/json'
        yield client


# ========== Model Fixtures ==========

@pytest.fixture
def entity(factory):
    """Provide a test entity."""
    return factory.entity


@pytest.fixture
def entity_person(factory):
    """Provide a test Person entity."""
    return factory.entity_person


@pytest.fixture
def entity_project(factory):
    """Provide a test Project entity."""
    return factory.entity_project


@pytest.fixture
def relationship(factory):
    """Provide a test relationship."""
    return factory.relationship


@pytest.fixture
def persona(factory):
    """Provide a test persona."""
    return factory.persona


@pytest.fixture
def conversation(factory):
    """Provide a test conversation."""
    return factory.conversation


@pytest.fixture
def chat_message(factory):
    """Provide a test chat message."""
    return factory.chat_message


@pytest.fixture
def agent(factory):
    """Provide a test agent."""
    return factory.agent


@pytest.fixture
def message(factory):
    """Provide a test inter-agent message."""
    return factory.message


# ========== Scenario Fixtures ==========

@pytest.fixture
def project_scenario(factory):
    """
    Provide a complete project scenario.

    Includes: developer, project, technology, company, and relationships.
    """
    return factory.create_project_scenario()


@pytest.fixture
def conversation_scenario(factory):
    """
    Provide a complete conversation scenario.

    Includes: persona, conversation, and messages.
    """
    return factory.create_conversation_scenario()


@pytest.fixture
def multi_agent_scenario(factory):
    """
    Provide a multi-agent collaboration scenario.

    Includes: backend and frontend agents with messages.
    """
    return factory.create_multi_agent_scenario()


# ========== Utility Fixtures ==========

@pytest.fixture
def json_headers():
    """Provide JSON content type headers."""
    return {'Content-Type': 'application/json'}
