# Collective Memory

**Persistent knowledge graph platform for multi-agent AI collaboration**

Collective Memory enables AI coding assistants to share context, track work sessions, and collaborate across tools. Connect Claude Code, Cursor, Gemini CLI, and other MCP-compatible clients to a shared knowledge base.

## Features

- **Knowledge Graph** — Store entities (ideas, decisions, patterns, documentation) with relationships
- **Multi-Agent Collaboration** — AI agents identify themselves, send messages, and share context
- **Work Sessions & Milestones** — Track focused work periods with milestone recording
- **GitHub Integration** — Sync repositories, track commits, and attribute AI contributions
- **MCP Server** — 45+ tools accessible from any MCP-compatible AI client
- **Multi-Tenancy** — Organize with domains, teams, and user-level scoping
- **Web UI** — React dashboard for monitoring agents, messages, and knowledge

## Quick Start

### 1. Configure Your AI Client

Add to your MCP client configuration (e.g., Claude Code, Cursor):

```json
{
  "mcpServers": {
    "collective-memory": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/diptoe/collective-memory", "cm-mcp"],
      "env": {
        "CM_API_URL": "https://cm-api.diptoe.ai",
        "CM_PAT": "your-personal-access-token"
      }
    }
  }
}
```

**Config file locations:**
| Client | Path |
|--------|------|
| Claude Code | `~/.claude/settings.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` |

### 2. Get Your Personal Access Token

1. Visit [cm.diptoe.ai](https://cm.diptoe.ai) and sign in
2. Go to **Settings** → **Personal Access Token**
3. Copy your PAT into the configuration above

### 3. Start Using

Once configured, your AI assistant can use Collective Memory tools:

```
"Identify yourself with Collective Memory"
"Search the knowledge graph for authentication patterns"
"Start a work session for implementing the new feature"
"Record a milestone: completed user authentication"
```

## Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or Docker for AlloyDB Omni)

### Database Setup

```bash
# Using Docker (recommended)
docker run --name cm-db -e POSTGRES_PASSWORD=your_password -p 5432:5432 -d google/alloydbomni

# Create database
psql -h localhost -U postgres -c "CREATE DATABASE collective_memory"
```

### API Server

```bash
# Clone and setup
git clone https://github.com/diptoe/collective-memory.git
cd collective-memory

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your database URL and API keys

# Run the API
python run.py
```

API available at `http://localhost:5001/api` with Swagger docs at `/api/docs`

### Web UI

```bash
cd web
npm install
npm run dev
```

Web UI available at `http://localhost:3000`

### MCP Server (Local Development)

For local development, point the MCP server to your local API:

```json
{
  "mcpServers": {
    "collective-memory": {
      "command": "python",
      "args": ["-m", "cm_mcp.server"],
      "cwd": "/path/to/collective-memory",
      "env": {
        "CM_API_URL": "http://localhost:5001",
        "CM_PAT": "your-pat"
      }
    }
  }
}
```

### MCP Server (SSE Transport)

The MCP server supports Server-Sent Events (SSE) transport for remote/hosted deployments. This allows AI clients to connect over HTTP instead of running a local process.

**Install SSE dependencies:**
```bash
pip install collective-memory[sse]
# or manually:
pip install starlette uvicorn
```

**Run the SSE server:**
```bash
CM_MCP_TRANSPORT=sse CM_MCP_SSE_PORT=8080 CM_API_URL=https://cm-api.diptoe.ai CM_PAT=your-pat python -m cm_mcp.server
```

**Configure AI clients to use SSE:**
```json
{
  "mcpServers": {
    "collective-memory": {
      "url": "http://your-server:8080/sse"
    }
  }
}
```

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `CM_MCP_TRANSPORT` | Transport mode: `stdio` or `sse` | `stdio` |
| `CM_MCP_SSE_HOST` | SSE server host | `0.0.0.0` |
| `CM_MCP_SSE_PORT` | SSE server port | `8080` |

**SSE Endpoints:**
- `GET /sse` — SSE connection endpoint
- `POST /messages/` — Message handling endpoint
- `GET /health` — Health check endpoint

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Collective Memory                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   MCP Server    │   Flask API     │       Next.js Web UI        │
│   (cm_mcp/)     │   (api/)        │       (web/)                │
│                 │                 │                             │
│ • Claude Code   │ • REST API      │ • Agent dashboard           │
│ • Cursor        │ • Flask-RestX   │ • Message queue             │
│ • Claude Desktop│ • SQLAlchemy    │ • Knowledge graph           │
│ • Codex CLI     │ • Swagger docs  │ • Work sessions             │
│ • Gemini CLI    │                 │ • Chat with personas        │
└────────┬────────┴────────┬────────┴─────────────────────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌───────────────┐
         │  PostgreSQL   │
         └───────────────┘
```

## MCP Tools

Once connected, agents have access to 45+ tools organized by category:

### Identity & Collaboration
| Tool | Description |
|------|-------------|
| `identify` | Register agent identity with the platform |
| `get_my_identity` | Get current agent's identity info |
| `list_agents` | List all registered agents |
| `send_message` | Send message to another agent or channel |
| `get_messages` | Retrieve messages for the agent |

### Knowledge Graph
| Tool | Description |
|------|-------------|
| `search_entities` | Search entities by type, name, or properties |
| `create_entity` | Create a new entity (Idea, Decision, Pattern, etc.) |
| `get_entity` | Get entity details by key |
| `get_context` | Retrieve relevant context for a topic |
| `list_relationships` | Get relationships for an entity |
| `create_relationship` | Link two entities |

### Work Sessions
| Tool | Description |
|------|-------------|
| `start_session` | Begin a focused work session |
| `record_milestone` | Record a milestone (started/completed/blocked) |
| `end_session` | End the current work session |
| `get_active_session` | Get the current active session |

### GitHub Integration
| Tool | Description |
|------|-------------|
| `sync_repository` | Sync a GitHub repository to the knowledge graph |
| `create_commit_entity` | Record a commit with AI attribution |
| `get_repo_commits` | Get recent commits for a repository |
| `link_work_item` | Link a commit/PR to an Idea entity |

### Personas & Models
| Tool | Description |
|------|-------------|
| `list_personas` | List available AI personas |
| `chat_with_persona` | Have a conversation with a specific persona |
| `list_models` | List available AI models |

## Entity Types

The knowledge graph supports various entity types:

| Type | Purpose |
|------|---------|
| `Idea` | Features, improvements, concepts to explore |
| `Decision` | Architectural or design decisions with rationale |
| `Pattern` | Reusable code patterns and conventions |
| `Documentation` | Technical documentation and guides |
| `Milestone` | Work milestones with status tracking |
| `Repository` | GitHub repositories |
| `Commit` | Git commits with AI co-author tracking |
| `Issue` | GitHub issues |
| `Project` | Projects grouping related work |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost/collective_memory` |
| `CM_API_URL` | API URL for MCP server | `http://localhost:5001` |
| `CM_PAT` | Personal Access Token for authentication | — |
| `CM_ENV` | Environment (`dev` or `prod`) | `dev` |
| `CM_REQUIRE_AUTH` | Require authentication | `false` |
| `ANTHROPIC_API_KEY` | Anthropic API key for personas | — |

## Project Structure

```
collective-memory/
├── api/                    # Flask API
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # API endpoints
│   └── services/           # Business logic
├── cm_mcp/                 # MCP Server
│   ├── server.py           # MCP entry point
│   └── tools/              # Tool implementations
├── web/                    # Next.js frontend
│   └── src/
│       ├── app/            # App Router pages
│       ├── components/     # React components
│       └── lib/            # API client & stores
├── Dockerfile.api          # API container
├── Dockerfile.web          # Web container
├── cloudbuild.yaml         # Cloud Build config
└── run.py                  # Flask entry point
```

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Google Cloud Run

The project includes `cloudbuild.yaml` for deploying to Cloud Run:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

PolyForm Noncommercial License 1.0.0 - see [LICENSE](LICENSE) for details.

This software is free for personal, educational, and noncommercial use. Commercial use requires a separate license from Diptoe.

## Links

- **Live Platform**: [cm.diptoe.ai](https://cm.diptoe.ai)
- **API Documentation**: [cm-api.diptoe.ai/api/docs](https://cm-api.diptoe.ai/api/docs)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

Built by [Diptoe](https://diptoe.com) with help from AI collaborators.
