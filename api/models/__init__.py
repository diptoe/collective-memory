"""
Collective Memory Platform - Models

All SQLAlchemy models for the knowledge graph and collaboration system.
"""
from api.models.base import db, BaseModel, get_key, get_uuid, get_now
from api.models.key import Key
from api.models.entity import Entity
from api.models.relationship import Relationship
from api.models.document import Document
from api.models.message import Message
from api.models.message_read import MessageRead
from api.models.model import Model
from api.models.client import ClientType, CLIENT_PERSONA_AFFINITIES, get_client_types, get_client_affinities, is_valid_client
from api.models.agent import Agent
from api.models.agent_checkpoint import AgentCheckpoint
from api.models.persona import Persona
from api.models.conversation import Conversation
from api.models.chat_message import ChatMessage
from api.models.table import Table
from api.models.table_status import TableStatus
from api.models.repository_stats import RepositoryStats
from api.models.commit import Commit
from api.models.metric import Metric, MetricTypes
from api.models.activity import Activity, ActivityType
from api.models.user import User
from api.models.session import Session
from api.models.domain import Domain
from api.models.team import Team, TeamMembership
from api.models.work_session import WorkSession
from api.models.project import Project
from api.models.team_project import TeamProject
from api.models.repository import Repository
from api.models.project_repository import ProjectRepository

__all__ = [
    'db',
    'BaseModel',
    'get_key',
    'get_uuid',
    'get_now',
    'Key',
    'Entity',
    'Relationship',
    'Document',
    'Message',
    'MessageRead',
    'Model',
    'ClientType',
    'CLIENT_PERSONA_AFFINITIES',
    'get_client_types',
    'get_client_affinities',
    'is_valid_client',
    'Agent',
    'AgentCheckpoint',
    'Persona',
    'Conversation',
    'ChatMessage',
    'Table',
    'TableStatus',
    'RepositoryStats',
    'Commit',
    'Metric',
    'MetricTypes',
    'Activity',
    'ActivityType',
    'User',
    'Session',
    'Domain',
    'Team',
    'TeamMembership',
    'WorkSession',
    'Project',
    'TeamProject',
    'Repository',
    'ProjectRepository',
]
