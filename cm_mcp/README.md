# Collective Memory MCP Server

MCP (Model Context Protocol) server for AI collaboration through a shared knowledge graph. Each AI agent connecting to Collective Memory is recognized as an entity, enabling:

- **Attribution** - Track which AI created/modified information
- **Collaboration** - Multiple AIs sharing knowledge
- **Context** - RAG-enhanced responses from collective knowledge

---

## Quick Start

### 1. Install Dependencies

```bash
cd /path/to/collective-memory
pip install -e .

# For semantic search (optional)
pip install pgvector spacy
python -m spacy download en_core_web_sm
```

### 2. Configure for Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "collective-memory": {
      "command": "python",
      "args": ["-m", "cm_mcp"],
      "env": {
        "CM_API_URL": "http://localhost:5002",
        "CM_AGENT_ID": "claude-desktop-backend",
        "CM_PERSONA": "backend-code"
      }
    }
  }
}
```

**Restart Claude Desktop** after saving.

### 3. Configure for Claude Code

**Option A: CLI with JSON (recommended)**

```bash
claude mcp add-json collective-memory '{"command": "python3", "args": ["-m", "cm_mcp"], "env": {"PYTHONPATH": "/path/to/collective-memory", "CM_API_URL": "http://localhost:5002", "CM_AGENT_ID": "claude-code-backend", "CM_PERSONA": "backend-code"}}'
```

**Option B: CLI with flags**

```bash
claude mcp add collective-memory \
  -e PYTHONPATH=/path/to/collective-memory \
  -e CM_API_URL=http://localhost:5002 \
  -e CM_AGENT_ID=claude-code-backend \
  -e CM_PERSONA=backend-code \
  -- python3 -m cm_mcp
```

**Option C: Manual `.mcp.json`**

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "collective-memory": {
      "command": "python3",
      "args": ["-m", "cm_mcp"],
      "env": {
        "PYTHONPATH": "/path/to/collective-memory",
        "CM_API_URL": "http://localhost:5002",
        "CM_AGENT_ID": "claude-code-backend",
        "CM_PERSONA": "backend-code"
      }
    }
  }
}
```

**Verify installation:**

```bash
claude mcp list
```

---

## Agent Identity & Personas

Each AI connecting to Collective Memory **must** have a unique identity and should specify which **persona** it's acting as. This enables:

- Acting with the correct system prompt, personality, and capabilities
- Tracking who created entities and relationships
- Seeing which agents are currently collaborating
- Multi-agent coordination with specialized roles

### Available Personas

| Persona | Name | Model | Specialization |
|---------|------|-------|----------------|
| `backend-code` | Claude Backend | claude-3-opus | Python, Flask, SQLAlchemy, API design |
| `frontend-code` | Claude Frontend | claude-3-opus | React, TypeScript, Tailwind, accessibility |
| `architect` | Gemini Architect | gemini-pro | System design, scalability, trade-offs |
| `consultant` | Claude Consultant | claude-opus-4-5 | Strategy, stakeholder communication, tech evaluation |

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CM_AGENT_ID` | **Yes** | - | Unique identifier for this AI instance |
| `CM_PERSONA` | **Yes** | - | Persona role: `backend-code`, `frontend-code`, `architect`, `consultant` |
| `CM_AGENT_CAPABILITIES` | No | `search,create,update` | Comma-separated capabilities |
| `CM_API_URL` | No | `http://localhost:5002` | Collective Memory API URL |
| `CM_MCP_TIMEOUT` | No | `30` | Request timeout in seconds |
| `CM_MCP_DEBUG` | No | `false` | Enable debug logging |

#### Auto-Create Persona (Optional)

If the specified `CM_PERSONA` doesn't exist in the database, the MCP server will auto-create it using these optional variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CM_PERSONA_NAME` | `Auto-{role}` | Display name, e.g., "Claude Consultant" |
| `CM_PERSONA_MODEL` | `claude-3-opus` | Model ID, e.g., `claude-opus-4-5`, `gemini-pro` |
| `CM_PERSONA_COLOR` | `#6b7280` | UI color (hex) |

### Example Configurations

| Scenario | Agent ID | Persona |
|----------|----------|---------|
| Backend development | `claude-code-backend` | `backend-code` |
| Frontend development | `claude-code-frontend` | `frontend-code` |
| Architecture review | `claude-architect-main` | `architect` |
| CI/CD backend checks | `claude-ci-backend` | `backend-code` |

---

## Available Tools (15 total)

### Entity Operations (6 tools)

| Tool | Description |
|------|-------------|
| `search_entities` | Search entities by name or type (keyword matching) |
| `search_entities_semantic` | Natural language semantic search using vector embeddings |
| `get_entity` | Get detailed entity information by key |
| `create_entity` | Create a new entity (Person, Project, Technology, etc.) |
| `update_entity` | Update entity name, type, or properties |
| `extract_entities_from_text` | Extract entities from text using NER (spaCy) |

### Relationship Operations (2 tools)

| Tool | Description |
|------|-------------|
| `list_relationships` | List relationships, optionally filtered by entity |
| `create_relationship` | Create a relationship (WORKS_ON, KNOWS, USES, etc.) |

### Context/RAG Operations (2 tools)

| Tool | Description |
|------|-------------|
| `get_context` | Get relevant context for a query (primary RAG tool) |
| `get_entity_context` | Get all relationships around a specific entity |

### Persona Operations (2 tools)

| Tool | Description |
|------|-------------|
| `list_personas` | List available AI personas with their specializations |
| `chat_with_persona` | Chat with a specific persona |

### Agent Collaboration (3 tools)

| Tool | Description |
|------|-------------|
| `list_agents` | List all AI agents collaborating in the collective memory |
| `get_my_identity` | Get your current agent ID, persona, and registration status |
| `update_my_identity` | Change your agent ID and/or persona during a session |

---

## Entity Types

- `Person` - People, team members, contacts
- `Project` - Projects, initiatives, products
- `Technology` - Technologies, tools, frameworks
- `Organization` - Companies, teams, groups
- `Document` - Documents, notes, references
- `Concept` - Abstract concepts, ideas

## Relationship Types

- `WORKS_ON` - Person works on Project
- `KNOWS` - Person knows Person
- `USES` - Project/Person uses Technology
- `CREATED` - Person/Agent created Project/Document
- `BELONGS_TO` - Entity belongs to Organization
- `RELATED_TO` - General relationship

---

## Usage Examples

Once configured, Claude can use the knowledge graph:

**Check your identity:**
> "What's my identity in the collective memory?"

**See who's collaborating:**
> "List all agents connected to the collective memory"

**Search for entities:**
> "Search for all Python-related technologies in my knowledge graph"

**Create with attribution:**
> "Create an entity for the new React dashboard project"
> *(Entity will be tagged with `source: agent:claude-code-wayne`)*

**Get context:**
> "What do you know about the Jai platform from the collective memory?"

**Extract entities from conversation:**
> "Extract entities from: 'Yesterday I met with Sarah from Acme Corp to discuss the new React dashboard'"

---

## Multi-Agent Collaboration Example

With multiple Claude instances configured with different personas:

```bash
# Backend specialist (Claude Desktop)
CM_AGENT_ID=claude-desktop-backend
CM_PERSONA=backend-code

# Frontend specialist (Claude Code)
CM_AGENT_ID=claude-code-frontend
CM_PERSONA=frontend-code

# Architect for reviews (Claude API)
CM_AGENT_ID=claude-architect-review
CM_PERSONA=architect
```

Each persona:
- Has its own system prompt and personality
- Acts according to its specialization
- Sees what other agents have contributed
- Tracks attribution on entities it creates

---

## Troubleshooting

### Server not appearing in Claude

1. Check config file syntax (valid JSON)
2. Restart Claude Desktop completely
3. Verify paths are absolute
4. Check `CM_API_URL` points to running API

### "CM_AGENT_ID is required" error

Set both `CM_AGENT_ID` and `CM_PERSONA` in your MCP config:

```json
"env": {
  "CM_AGENT_ID": "your-unique-agent-id",
  "CM_PERSONA": "backend-code"
}
```

### Connection errors

```bash
# Test API is running
curl http://localhost:5002/api/health

# Run server manually to see errors
CM_AGENT_ID=test CM_PERSONA=backend-code python -m cm_mcp
```

### Debug mode

Set `CM_MCP_DEBUG=true` to see detailed logs in stderr.

---

## Architecture

```
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│Claude Desktop │ │  Claude Code  │ │  Claude Code  │ │  Claude API   │
│  consultant   │ │ backend-code  │ │ frontend-code │ │   architect   │
│ (Opus 4.5)    │ │   (Opus)      │ │    (Opus)     │ │  (Gemini)     │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       MCP Server (cm_mcp)                            │
│  • Registers agent with persona on startup                           │
│  • Resolves persona → system prompt, personality, model              │
│  • Tracks agent source on all entity/relationship creation           │
│  • Provides 15 tools for knowledge graph operations                  │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Collective Memory API                           │
│  • Knowledge graph (entities/relationships)                          │
│  • Personas (backend-code, frontend-code, architect, consultant)     │
│  • Agent registry & heartbeats                                       │
│  • Semantic search (pgvector)                                        │
│  • NER extraction (spaCy)                                            │
└──────────────────────────────────────────────────────────────────────┘
```
