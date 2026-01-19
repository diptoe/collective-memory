# Collective Memory Platform

**Project:** Collective Memory
**Company:** Diptoe
**Owner:** Wayne Houlden (wayne@diptoe.com)
**Repository:** https://github.com/diptoe/collective-memory

## Overview

A persistent knowledge graph platform enabling multi-agent AI collaboration with:
- Flask API + SQLAlchemy backend with multi-tenancy (domains, teams, users)
- PostgreSQL database (AlloyDB Omni in Docker)
- React frontend (Next.js) for human interaction, admin, and debugging
- MCP server for AI agent integration (Claude Code, Cursor, etc.)
- GitHub integration for repository tracking and commit attribution
- Work sessions and milestone tracking for AI agent productivity

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Collective Memory                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   MCP Server    │   Flask API     │       Next.js Web UI        │
│   (cm_mcp/)     │   (api/)        │       (web/)                │
│                 │                 │                             │
│ • Claude Code   │ • REST API      │ • Agents dashboard          │
│ • Cursor        │ • Flask-RestX   │ • Messages queue            │
│ • Claude Desktop│ • SQLAlchemy    │ • Sessions/milestones       │
│ • Codex         │ • Swagger docs  │ • Knowledge graph           │
│ • Gemini CLI    │                 │ • Chat with personas        │
└────────┬────────┴────────┬────────┴─────────────────────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌───────────────┐
         │  PostgreSQL   │
         │ (AlloyDB Omni)│
         └───────────────┘
```

## Tech Stack

### Backend (api/)
- **Framework:** Flask with Flask-RESTX (Swagger/OpenAPI)
- **ORM:** SQLAlchemy with auto-migrations
- **Database:** PostgreSQL (AlloyDB Omni)
- **Auth:** PAT-based authentication with domain/team/user scopes
- **Patterns:** Following Jai API conventions

### Frontend (web/)
- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS v4
- **State:** Zustand + React Query
- **UI Components:** Radix UI primitives
- **Pattern:** Following Jai React conventions

### MCP Server (cm_mcp/)
- **SDK:** MCP Python SDK 1.1.1
- **Transport:** stdio for Claude Desktop/Code
- **Tools:** 45+ tools for knowledge graph operations

---

## Project Structure

```
collective-memory/
├── api/                          # Flask API
│   ├── __init__.py               # Flask app factory
│   ├── config.py                 # Environment configuration
│   ├── migration_manager.py      # Auto-discovery migrations
│   ├── models/
│   │   ├── base.py               # BaseModel with CRUD, get_key, get_now
│   │   ├── entity.py             # Knowledge graph entities (with scopes)
│   │   ├── relationship.py       # Entity relationships
│   │   ├── message.py            # Inter-agent messages
│   │   ├── agent.py              # Agent registration (with current_milestone_*)
│   │   ├── persona.py            # AI personas
│   │   ├── model.py              # AI model registry
│   │   ├── client.py             # Client types
│   │   ├── user.py               # User accounts
│   │   ├── domain.py             # Multi-tenancy domains
│   │   ├── team.py               # Team-based scoping
│   │   ├── work_session.py       # Work session tracking
│   │   ├── metric.py             # Time-series metrics
│   │   └── activity.py           # Activity logging
│   ├── routes/
│   │   ├── __init__.py           # Route registration (register_routes)
│   │   ├── entities.py           # Entity CRUD + semantic search
│   │   ├── relationships.py      # Relationship CRUD
│   │   ├── messages.py           # Inter-agent messaging + channels
│   │   ├── agents.py             # Agent management + heartbeat
│   │   ├── users.py              # User management
│   │   ├── domains.py            # Domain management
│   │   ├── teams.py              # Team management
│   │   ├── work_sessions.py      # Work session management
│   │   ├── metrics.py            # Time-series metrics + batch API
│   │   ├── activities.py         # Activity monitoring
│   │   ├── github.py             # GitHub sync endpoints
│   │   └── ...
│   └── services/
│       ├── auth.py               # @require_auth decorator
│       └── github.py             # GitHub API integration
│
├── cm_mcp/                       # MCP Server
│   ├── server.py                 # MCP server entry + dispatcher (~680 lines)
│   ├── config.py                 # MCP configuration
│   └── tools/                    # Tool definitions + implementations
│       ├── __init__.py           # Aggregates TOOL_DEFINITIONS + TOOL_HANDLERS
│       ├── utils.py              # Shared utilities (_make_request)
│       │   # --- Entity & Graph ---
│       ├── entity.py             # Entity CRUD + semantic search (7 tools)
│       ├── relationship.py       # Relationship CRUD (3 tools)
│       ├── context.py            # Context/RAG operations (2 tools)
│       │   # --- Agent & Identity ---
│       ├── agent.py              # list_agents (1 tool)
│       ├── identity.py           # identify, get/update_my_identity (3 tools)
│       ├── team.py               # Scopes + teams (3 tools)
│       │   # --- Communication ---
│       ├── message.py            # Messaging operations (5 tools)
│       ├── persona.py            # AI personas (2 tools)
│       ├── model.py              # Models, clients, focus (4 tools)
│       │   # --- GitHub ---
│       ├── github_repo.py        # Repository sync + info (4 tools)
│       ├── github_sync.py        # History sync (2 tools)
│       ├── github_entities.py    # Commit/Issue entities (3 tools)
│       │   # --- Sessions & Metrics ---
│       ├── session.py            # Work session lifecycle (4 tools)
│       ├── milestone.py          # Milestone recording (1 tool)
│       └── activity.py           # Activity monitoring (2 tools)
│
├── web/                          # Next.js Frontend
│   ├── src/
│   │   ├── app/                  # App Router pages
│   │   │   ├── (main)/           # Main layout group
│   │   │   │   ├── agents/       # Agent list + [agent_key] detail
│   │   │   │   ├── messages/     # Message queue UI
│   │   │   │   ├── sessions/     # Work sessions + milestones
│   │   │   │   ├── entities/     # Entity browser
│   │   │   │   ├── graph/        # React Flow visualization
│   │   │   │   └── ...
│   │   │   └── admin/            # Admin pages
│   │   ├── components/
│   │   │   ├── agent-status.tsx  # Agent card with badges
│   │   │   ├── message-card.tsx  # Message display
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── api/              # API client
│   │   │   └── stores/           # Zustand stores
│   │   └── types/
│   │       └── index.ts          # TypeScript interfaces
│   └── package.json
│
├── tests/                        # Pytest tests
├── docker-compose.yml            # Full stack deployment
├── Dockerfile.api                # API container
├── Dockerfile.mcp                # MCP container
├── Dockerfile.web                # Web container
└── run.py                        # Flask entry point
```

---

## Key Development Patterns

### 1. Database Models (api/models/)

#### Schema Versioning
Models use schema versioning for automatic migrations:

```python
class MyModel(BaseModel):
    __tablename__ = 'my_models'
    __schema_version__ = 2  # Bump when adding/changing columns

    # Define schema migrations
    __schema_updates__ = {
        2: [
            ("new_column", Column(String(100), nullable=True)),
        ]
    }

    # Default fields returned in to_dict()
    _default_fields = ['my_key', 'name', 'new_column', 'created_at']

    @classmethod
    def ensure_schema(cls):
        """Called on startup to apply migrations."""
        # Auto-adds new columns if needed
```

#### Denormalized Fields Pattern
For frequently-accessed related data, use denormalized fields:

```python
# Good: Denormalized for display (Agent model)
current_milestone_key = Column(String(36), nullable=True)
current_milestone_name = Column(String(500), nullable=True)
current_milestone_status = Column(String(50), nullable=True)
current_milestone_started_at = Column(DateTime(timezone=True), nullable=True)

# Helper method to update together
def set_current_milestone(self, key, name, status, started_at=None):
    self.current_milestone_key = key
    self.current_milestone_name = name
    self.current_milestone_status = status
    self.current_milestone_started_at = started_at or get_now()
    return self.save()

def clear_current_milestone(self):
    self.current_milestone_key = None
    self.current_milestone_name = None
    self.current_milestone_status = None
    self.current_milestone_started_at = None
    return self.save()
```

#### Standard Primary Keys
Use readable word-based keys, not UUIDs:

```python
from api.models.base import get_key

my_key = Column(String(50), primary_key=True, default=get_key)
# Generates: "swift-bold-keen-lion", "calm-fresh-wild-river"
```

### 2. API Routes (api/routes/)

#### Route Registration Pattern
Each route module exports a `register_*_routes(api)` function:

```python
# api/routes/my_feature.py
from flask_restx import Api, Resource, Namespace, fields
from api.services.auth import require_auth

def register_my_feature_routes(api: Api):
    """Register my feature routes with the API."""

    ns = api.namespace(
        'my-feature',
        description='My feature operations',
        path='/my-feature'
    )

    # Define models for Swagger
    response_model = ns.model('Response', {
        'success': fields.Boolean(),
        'msg': fields.String(),
        'data': fields.Raw(),
    })

    @ns.route('')
    class MyFeatureList(Resource):
        @ns.doc('list_items')
        @ns.marshal_with(response_model)
        @require_auth
        def get(self):
            """List all items."""
            return {'success': True, 'msg': 'OK', 'data': {...}}
```

Register in `api/routes/__init__.py`:
```python
from api.routes.my_feature import register_my_feature_routes

def register_routes(api: Api):
    # ... existing routes ...
    register_my_feature_routes(api)
```

#### Standard Response Format
Always return: `{'success': bool, 'msg': str, 'data': dict}`

### 3. MCP Tool Development (cm_mcp/)

#### Architecture
Each tool file exports both definitions AND implementations. The `server.py` imports aggregated exports from `tools/__init__.py`.

**Adding a new tool requires:**
1. Create or edit `cm_mcp/tools/my_tools.py` with definitions + handlers
2. Update `cm_mcp/tools/__init__.py` to import and aggregate the new module

**Tool file structure:**
```python
# cm_mcp/tools/my_tools.py
import mcp.types as types
from .utils import _make_request

# Tool definitions
TOOL_DEFINITIONS = [
    types.Tool(
        name="my_tool",
        description="...",
        inputSchema={...}
    ),
]

# Tool implementations (standard handler signature)
async def my_tool(arguments: dict, config, session_state) -> list[types.TextContent]:
    """Implementation"""
    ...

# Export mapping for dispatcher
TOOL_HANDLERS = {
    "my_tool": my_tool,
}
```

**server.py dispatcher:**
```python
from .tools import TOOL_DEFINITIONS, TOOL_HANDLERS

@server.list_tools()
async def list_tools():
    return TOOL_DEFINITIONS

@server.call_tool()
async def call_tool(name, arguments):
    handler = TOOL_HANDLERS.get(name)
    if handler:
        return await handler(arguments, config, _session_state)
```

**Tool modules:**
| Module | Tools |
|--------|-------|
| `entity.py` | search_entities, get_entity, create_entity, update_entity, search_entities_semantic, extract_entities_from_text, move_entity_scope |
| `relationship.py` | list_relationships, create_relationship, delete_relationship |
| `context.py` | get_context, get_entity_context |
| `persona.py` | list_personas, chat_with_persona |
| `agent.py` | list_agents |
| `identity.py` | identify, get_my_identity, update_my_identity |
| `team.py` | list_my_scopes, set_active_team, list_teams |
| `message.py` | send_message, get_messages, mark_message_read, mark_all_messages_read, link_message_entities |
| `model.py` | list_models, list_clients, update_focus, set_focused_mode |
| `github_repo.py` | sync_repository, get_repo_issues, get_repo_commits, get_repo_contributors |
| `github_sync.py` | sync_repository_history, sync_repository_updates |
| `github_entities.py` | create_commit_entity, create_issue_entity, link_work_item |
| `activity.py` | list_activities, get_activity_summary |
| `session.py` | get_active_session, start_session, end_session, extend_session |
| `milestone.py` | record_milestone |

#### Tool Function Signature
All tools follow this signature:

```python
async def tool_name(
    arguments: dict,      # Tool arguments from MCP
    config: Any,          # MCP config (api_url, etc.)
    session_state: dict,  # Session state (agent_id, etc.)
) -> list[types.TextContent]:
    """Tool description."""
    ...
```

#### Session State
The MCP server maintains session state across tool calls:

```python
_session_state = {
    "agent_id": None,
    "agent_key": None,
    "client": None,           # claude-code, cursor, etc.
    "model_key": None,
    "model_id": None,
    "persona": None,
    "persona_key": None,
    "focus": None,
    "registered": False,
    "current_milestone": None,  # {key, name, status, started_at}
    "tool_call_count": 0,
    "milestone_start_tool_count": 0,
}
```

### 4. Frontend Development (web/)

#### TypeScript Types
Keep types in sync with API models:

```typescript
// web/src/types/index.ts
export interface Agent {
  agent_key: string;
  agent_id: string;
  // ... standard fields ...

  // Denormalized milestone fields (match API model)
  current_milestone_key?: string;
  current_milestone_name?: string;
  current_milestone_status?: 'started' | 'completed' | 'blocked';
  current_milestone_started_at?: string;
}
```

#### API Client Pattern
```typescript
// web/src/lib/api/client.ts
const response = await fetch(`${API_BASE}/endpoint`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
const data = await response.json();
// data = { success: boolean, msg: string, data: {...} }
```

---

## Key Features

### Multi-Tenancy
- **Domains:** Top-level isolation (organizations)
- **Teams:** Groups within domains
- **Users:** Individual accounts with roles
- **Scopes:** domain, team, or user visibility for entities

### Work Sessions & Milestones
- Track focused work periods on projects
- Record milestones (started/completed/blocked)
- Capture metrics (tool calls, lines changed, etc.)
- Self-assessment ratings (1-5 scale)

### GitHub Integration
- Sync repositories as entities
- Track commits and issues
- Detect AI co-authors (Claude, Copilot)
- Link work items to Ideas

### Agent Collaboration
- Agent identity and registration
- Heartbeat for active status
- Message queue for communication
- Autonomous task workflows

### Metrics System
- Time-series metrics storage
- Batch recording API
- Per-entity metric tracking
- Built-in metric types for common patterns

---

## Running the Project

### Local Development

```bash
# Start API
cd collective-memory
source .venv/bin/activate
python run.py
# API: http://localhost:5001/api
# Swagger: http://localhost:5001/api/docs

# Start Frontend (separate terminal)
cd collective-memory/web
npm run dev
# Web: http://localhost:3000

# MCP Server runs via Claude Code/Cursor config
```

### Docker Deployment
```bash
docker-compose up -d
```
See [DOCKER.md](DOCKER.md) for details.

---

## MCP Server Configuration

Add to Claude Code settings (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "collective-memory": {
      "command": "python",
      "args": ["-m", "cm_mcp.server"],
      "cwd": "/path/to/collective-memory",
      "env": {
        "CM_API_URL": "http://localhost:5001"
      }
    }
  }
}
```

---

## Database

### Connection (Docker - AlloyDB Omni)
```bash
docker run --name jai-omni -e POSTGRES_PASSWORD=Q57SZI -p 5432:5432 -d google/alloydbomni
```

**Connection string:** `postgresql://postgres:Q57SZI@localhost:5432/collective_memory`

### Core Tables
- `domains`, `teams`, `users` - Multi-tenancy
- `entities` - Knowledge graph nodes (with scope_type, scope_key)
- `relationships` - Graph edges
- `agents` - AI agent registrations (with current_milestone_*)
- `messages` - Inter-agent communication
- `work_sessions` - Work period tracking
- `metrics` - Time-series metrics
- `activities` - Activity logging
- `personas`, `models`, `clients` - AI configuration

---

## Brand Guide

### Color Palette
```css
--cm-charcoal: #131314;    /* Near-black, main text */
--cm-terracotta: #d97757;  /* Warm rust accent */
--cm-cream: #faf9f0;       /* Off-white background */
--cm-amber: #e8a756;       /* Secondary accent */
--cm-sienna: #a85a3b;      /* Darker rust */
--cm-sand: #e6dfd1;        /* Subtle backgrounds */
--cm-coffee: #5c4d3c;      /* Dark brown emphasis */
--cm-ivory: #fffef8;       /* Light background */
--cm-success: #5d8a66;     /* Muted green */
--cm-warning: #d9a557;     /* Amber warning */
--cm-error: #c45c5c;       /* Muted red */
--cm-info: #6b8fa8;        /* Slate blue */
```

### Typography
- **Primary:** Inter
- **Accent:** Source Serif 4
- **Monospace:** JetBrains Mono

---

## Important Notes

1. **`metadata` is reserved** - Use `extra` or `extra_data` for additional data columns
2. **Standard response format** - `{success, msg, data}` for all API responses
3. **MCP tool prefix** - Tools appear as `mcp__collective-memory__*` in Claude
4. **Schema versioning** - Always bump `__schema_version__` when adding columns
5. **Denormalized fields** - Use for frequently-displayed related data
6. **Scopes** - Always consider domain/team/user visibility for new entities

---

## Development Status

### Completed
- [x] Core knowledge graph (entities, relationships)
- [x] Multi-tenancy (domains, teams, users)
- [x] Agent identity and collaboration
- [x] Message queue with channels
- [x] GitHub integration
- [x] Work sessions and milestones
- [x] Time-series metrics
- [x] Activity monitoring
- [x] MCP server (46 tools)
- [x] Next.js web UI
- [x] Docker deployment
- [x] MCP tool refactoring (definitions + handlers in tool files)

### In Progress
- [ ] Milestone metrics capture and display

### Planned
- [ ] Semantic search with pgvector
- [ ] Agent checkpointing
- [ ] Multi-agent orchestration workflows
