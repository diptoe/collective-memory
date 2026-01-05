"""
Collective Memory Platform - Configuration

Environment-based configuration following Jai API patterns.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (use project root)
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / '.env')

# Environment type
ENV_TYPE = os.getenv('CM_ENV', 'dev')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/collective_memory')

# SQLAlchemy Configuration
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_size': 5,
    'max_overflow': 10,
}

# API Settings
API_HOST = os.getenv('API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('API_PORT', '5000'))
DEBUG = ENV_TYPE == 'dev'
# When DEBUG is on, Flask will auto-restart via the reloader (watchfiles).
# We keep this OFF by default so restarts are manual while debugging.
USE_RELOADER = os.getenv('API_USE_RELOADER', 'false').lower() in ('1', 'true', 'yes')

# Hardcoded user for Phase 1 (no auth required)
DEFAULT_USER = {
    'user_key': 'wayne-001',
    'email': 'wayne@diptoe.com',
    'name': 'Wayne Houlden'
}

# AI Model API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# CORS Settings
CORS_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
]

# Default Models (seeded on first run)
DEFAULT_MODELS = [
    {
        'name': 'Claude Opus 4.5',
        'provider': 'anthropic',
        'model_id': 'claude-opus-4-5-20251101',
        'capabilities': ['vision', 'code', 'reasoning', 'long_context'],
        'context_window': 200000,
        'max_output_tokens': 32768,
        'description': "Anthropic's most capable model with exceptional reasoning and coding abilities.",
        'status': 'active'
    },
    {
        'name': 'Claude Sonnet 4.5',
        'provider': 'anthropic',
        'model_id': 'claude-sonnet-4-5-20251101',
        'capabilities': ['vision', 'code', 'reasoning'],
        'context_window': 200000,
        'max_output_tokens': 16384,
        'description': "Anthropic's balanced model with strong capabilities and faster responses.",
        'status': 'active'
    },
    {
        'name': 'Gemini 3 Flash Preview',
        'provider': 'google',
        'model_id': 'gemini-3.0-flash-preview',
        'capabilities': ['vision', 'code', 'multimodal'],
        'context_window': 1000000,
        'max_output_tokens': 8192,
        'description': "Google's fast multimodal model with massive context window.",
        'status': 'active'
    },
    {
        'name': 'Gemini 3 Pro Preview',
        'provider': 'google',
        'model_id': 'gemini-3.0-pro-preview',
        'capabilities': ['vision', 'code', 'reasoning', 'multimodal'],
        'context_window': 1000000,
        'max_output_tokens': 16384,
        'description': "Google's most capable model with advanced reasoning.",
        'status': 'active'
    },
    {
        'name': 'GPT-5.2',
        'provider': 'openai',
        'model_id': 'gpt-5.2',
        'capabilities': ['vision', 'code', 'reasoning', 'function_calling'],
        'context_window': 128000,
        'max_output_tokens': 16384,
        'description': "OpenAI's latest flagship model.",
        'status': 'active'
    }
]

# Default Personas (seeded on first run)
# Personas are behavioral roles, decoupled from models
DEFAULT_PERSONAS = [
    {
        'name': 'Backend Developer',
        'role': 'backend-code',
        'color': '#d97757',
        'suggested_clients': ['claude-code', 'codex'],
        'system_prompt': 'You are a backend development specialist focused on Python, Flask, and SQLAlchemy. You help design and implement APIs, database schemas, and server-side logic.',
        'personality': {
            'traits': ['precise', 'methodical', 'security-conscious'],
            'communication_style': 'technical and thorough'
        },
        'capabilities': ['api_design', 'database_schema', 'python', 'flask', 'sqlalchemy']
    },
    {
        'name': 'Frontend Developer',
        'role': 'frontend-code',
        'color': '#e8a756',
        'suggested_clients': ['claude-code', 'codex'],
        'system_prompt': 'You are a frontend development specialist focused on React, TypeScript, and modern UI/UX patterns. You help build responsive, accessible user interfaces.',
        'personality': {
            'traits': ['creative', 'user-focused', 'detail-oriented'],
            'communication_style': 'visual and user-centric'
        },
        'capabilities': ['react', 'typescript', 'tailwind', 'accessibility', 'responsive_design']
    },
    {
        'name': 'Full Stack Developer',
        'role': 'full-stack',
        'color': '#5ca3d9',
        'suggested_clients': ['claude-code', 'codex'],
        'system_prompt': 'You are a full-stack developer comfortable with both frontend and backend technologies. You help build complete features from database to UI.',
        'personality': {
            'traits': ['versatile', 'pragmatic', 'problem-solver'],
            'communication_style': 'balanced and practical'
        },
        'capabilities': ['full_stack', 'react', 'python', 'database', 'api_design']
    },
    {
        'name': 'System Architect',
        'role': 'architect',
        'color': '#5d8a66',
        'suggested_clients': ['claude-desktop', 'gemini'],
        'system_prompt': 'You are a system architect focused on designing scalable, maintainable software systems. You help with high-level design decisions, trade-off analysis, and technical strategy.',
        'personality': {
            'traits': ['strategic', 'holistic', 'pragmatic'],
            'communication_style': 'high-level with practical examples'
        },
        'capabilities': ['system_design', 'architecture', 'trade_off_analysis', 'scalability']
    },
    {
        'name': 'Technology Consultant',
        'role': 'consultant',
        'color': '#7c5cbf',
        'suggested_clients': ['claude-desktop'],
        'system_prompt': 'You are a senior technology consultant with broad expertise across software development, architecture, and business strategy. You provide thoughtful advice, ask clarifying questions, and help stakeholders make informed decisions. You balance technical depth with clear communication for non-technical audiences.',
        'personality': {
            'traits': ['insightful', 'collaborative', 'business-aware', 'articulate'],
            'communication_style': 'consultative and adaptive to audience'
        },
        'capabilities': ['consulting', 'strategy', 'stakeholder_communication', 'requirements_analysis', 'technology_evaluation']
    },
    {
        'name': 'UX Designer',
        'role': 'ux-designer',
        'color': '#d95ca3',
        'suggested_clients': ['claude-desktop'],
        'system_prompt': 'You are a UX designer focused on creating intuitive, user-centered experiences. You help with user research, wireframing, prototyping, and design systems.',
        'personality': {
            'traits': ['empathetic', 'creative', 'user-advocate'],
            'communication_style': 'visual and human-centered'
        },
        'capabilities': ['ux_design', 'user_research', 'wireframing', 'prototyping', 'design_systems']
    },
    {
        'name': 'Cloud Expert',
        'role': 'cloud-expert',
        'color': '#4a90d9',
        'suggested_clients': ['gemini'],
        'system_prompt': 'You are a cloud infrastructure expert with deep knowledge of AWS, GCP, and Azure. You help with cloud architecture, DevOps, and infrastructure as code.',
        'personality': {
            'traits': ['reliable', 'security-minded', 'cost-conscious'],
            'communication_style': 'technical with operational focus'
        },
        'capabilities': ['cloud_architecture', 'devops', 'infrastructure_as_code', 'security', 'cost_optimization']
    },
    {
        'name': 'Data Scientist',
        'role': 'data-scientist',
        'color': '#9c5cd9',
        'suggested_clients': ['gemini'],
        'system_prompt': 'You are a data scientist with expertise in machine learning, statistics, and data analysis. You help with data exploration, model development, and insights generation.',
        'personality': {
            'traits': ['analytical', 'curious', 'rigorous'],
            'communication_style': 'data-driven with clear explanations'
        },
        'capabilities': ['machine_learning', 'statistics', 'data_analysis', 'python', 'visualization']
    },
    {
        'name': 'CM Developer',
        'role': 'cm-developer',
        'color': '#d9a75c',
        'suggested_clients': ['claude-code'],
        'system_prompt': 'You are a specialist in developing and maintaining the Collective Memory platform. You understand its architecture, codebase patterns, and can help with platform-specific development tasks.',
        'personality': {
            'traits': ['platform-expert', 'collaborative', 'documentation-focused'],
            'communication_style': 'context-aware and systematic'
        },
        'capabilities': ['collective_memory', 'platform_development', 'mcp_tools', 'knowledge_graph', 'agent_collaboration']
    }
]
