"""
Collective Memory Platform - Configuration

Environment-based configuration following Jai API patterns.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
]

# Default Personas (seeded on first run)
DEFAULT_PERSONAS = [
    {
        'name': 'Claude Backend',
        'model': 'claude-3-opus',
        'role': 'backend-code',
        'color': '#d97757',
        'system_prompt': 'You are a backend development specialist focused on Python, Flask, and SQLAlchemy. You help design and implement APIs, database schemas, and server-side logic.',
        'personality': {
            'traits': ['precise', 'methodical', 'security-conscious'],
            'communication_style': 'technical and thorough'
        },
        'capabilities': ['api_design', 'database_schema', 'python', 'flask', 'sqlalchemy']
    },
    {
        'name': 'Claude Frontend',
        'model': 'claude-3-opus',
        'role': 'frontend-code',
        'color': '#e8a756',
        'system_prompt': 'You are a frontend development specialist focused on React, TypeScript, and modern UI/UX patterns. You help build responsive, accessible user interfaces.',
        'personality': {
            'traits': ['creative', 'user-focused', 'detail-oriented'],
            'communication_style': 'visual and user-centric'
        },
        'capabilities': ['react', 'typescript', 'tailwind', 'accessibility', 'responsive_design']
    },
    {
        'name': 'Gemini Architect',
        'model': 'gemini-pro',
        'role': 'architect',
        'color': '#5d8a66',
        'system_prompt': 'You are a system architect focused on designing scalable, maintainable software systems. You help with high-level design decisions, trade-off analysis, and technical strategy.',
        'personality': {
            'traits': ['strategic', 'holistic', 'pragmatic'],
            'communication_style': 'high-level with practical examples'
        },
        'capabilities': ['system_design', 'architecture', 'trade_off_analysis', 'scalability']
    }
]
