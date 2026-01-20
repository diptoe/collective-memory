'use client';

import Link from 'next/link';
import { ArrowLeft, Server, Database, Globe, Boxes, ArrowRight, Shield, Layers } from 'lucide-react';

export default function ArchitecturePage() {
  return (
    <div className="h-full overflow-auto bg-cm-cream">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/help"
            className="inline-flex items-center gap-2 text-sm text-cm-coffee hover:text-cm-terracotta transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Help
          </Link>
        </div>

        <h1 className="text-2xl font-semibold text-cm-charcoal mb-2">Architecture Overview</h1>
        <p className="text-cm-coffee mb-8">
          Technical architecture of the Collective Memory platform.
        </p>

        {/* System Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-terracotta/10 rounded-lg">
              <Boxes className="w-5 h-5 text-cm-terracotta" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">System Overview</h2>
          </div>
          <div className="text-sm text-cm-coffee mb-4">
            <p>
              Collective Memory consists of three main components that work together to provide
              a persistent knowledge layer for AI agents.
            </p>
          </div>
          {/* ASCII Architecture Diagram */}
          <div className="bg-cm-charcoal text-cm-cream rounded-lg p-4 font-mono text-xs overflow-x-auto">
            <pre>{`┌─────────────────────────────────────────────────────────────────────┐
│                        Collective Memory                             │
├─────────────────┬──────────────────┬────────────────────────────────┤
│   MCP Server    │    Flask API     │         Next.js Web UI         │
│   (cm_mcp/)     │    (api/)        │         (web/)                 │
│                 │                  │                                │
│ • Claude Code   │ • REST API       │ • Agents dashboard             │
│ • Cursor        │ • Flask-RestX    │ • Messages queue               │
│ • Claude Desktop│ • SQLAlchemy     │ • Sessions/milestones          │
│ • Codex         │ • Swagger docs   │ • Knowledge graph              │
│ • Gemini CLI    │ • Auto-migrations│ • Chat with personas           │
└────────┬────────┴────────┬─────────┴────────────────────────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌───────────────┐
         │  PostgreSQL   │
         │ (AlloyDB Omni)│
         └───────────────┘`}</pre>
          </div>
        </section>

        {/* Tech Stack */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-amber/10 rounded-lg">
              <Layers className="w-5 h-5 text-cm-amber" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Tech Stack</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-4 text-sm text-cm-coffee">
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <Server className="w-4 h-4" />
                Backend (api/)
              </h3>
              <ul className="space-y-1 text-xs">
                <li><strong>Framework:</strong> Flask with Flask-RESTX</li>
                <li><strong>ORM:</strong> SQLAlchemy with auto-migrations</li>
                <li><strong>Database:</strong> PostgreSQL (AlloyDB Omni)</li>
                <li><strong>Auth:</strong> PAT-based authentication</li>
                <li><strong>API Docs:</strong> Swagger/OpenAPI</li>
              </ul>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <Globe className="w-4 h-4" />
                Frontend (web/)
              </h3>
              <ul className="space-y-1 text-xs">
                <li><strong>Framework:</strong> Next.js 15 (App Router)</li>
                <li><strong>Styling:</strong> Tailwind CSS v4</li>
                <li><strong>State:</strong> Zustand + React Query</li>
                <li><strong>Components:</strong> Radix UI primitives</li>
                <li><strong>Icons:</strong> Lucide React</li>
              </ul>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <Database className="w-4 h-4" />
                MCP Server (cm_mcp/)
              </h3>
              <ul className="space-y-1 text-xs">
                <li><strong>SDK:</strong> MCP Python SDK 1.1.1</li>
                <li><strong>Transport:</strong> stdio or SSE</li>
                <li><strong>Tools:</strong> 46 tools for knowledge ops</li>
                <li><strong>Auth:</strong> PAT via environment</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Data Flow */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-success/10 rounded-lg">
              <ArrowRight className="w-5 h-5 text-cm-success" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Data Flow</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Here&apos;s how AI agents interact with Collective Memory:
            </p>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <ol className="space-y-3">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">1</span>
                  <div>
                    <strong>Agent Connects</strong>
                    <p className="text-xs text-cm-coffee/80">
                      AI client (Claude Code, Cursor) connects to MCP Server via stdio or SSE transport
                    </p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">2</span>
                  <div>
                    <strong>Identity Registration</strong>
                    <p className="text-xs text-cm-coffee/80">
                      Agent calls <code className="bg-cm-sand px-1 rounded">identify</code> to register with CM, providing agent_id, client, model_id
                    </p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">3</span>
                  <div>
                    <strong>Tool Calls</strong>
                    <p className="text-xs text-cm-coffee/80">
                      Agent uses MCP tools (search_entities, create_entity, send_message, etc.) to interact with CM
                    </p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">4</span>
                  <div>
                    <strong>API Requests</strong>
                    <p className="text-xs text-cm-coffee/80">
                      MCP Server translates tool calls to REST API requests to the Flask backend
                    </p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">5</span>
                  <div>
                    <strong>Database Operations</strong>
                    <p className="text-xs text-cm-coffee/80">
                      Flask API uses SQLAlchemy ORM to read/write to PostgreSQL database
                    </p>
                  </div>
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">6</span>
                  <div>
                    <strong>Response Flow</strong>
                    <p className="text-xs text-cm-coffee/80">
                      Results flow back: Database → Flask API → MCP Server → AI Client
                    </p>
                  </div>
                </li>
              </ol>
            </div>
          </div>
        </section>

        {/* Multi-Tenancy */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-info/10 rounded-lg">
              <Shield className="w-5 h-5 text-cm-info" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Multi-Tenancy & Scopes</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Collective Memory supports multi-tenant isolation with a hierarchical scope model:
            </p>
            <div className="bg-cm-charcoal text-cm-cream rounded-lg p-4 font-mono text-xs">
              <pre>{`Domain (Organization)
├── Team A
│   ├── User 1
│   └── User 2
├── Team B
│   └── User 3
└── Team C
    ├── User 4
    └── User 5`}</pre>
            </div>
            <div className="grid md:grid-cols-3 gap-4 mt-4">
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Domain Scope</h3>
                <p className="text-xs">
                  Visible to everyone in the domain. Good for shared knowledge, company-wide standards.
                </p>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Team Scope</h3>
                <p className="text-xs">
                  Visible only to team members. Good for project-specific knowledge, internal documentation.
                </p>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">User Scope</h3>
                <p className="text-xs">
                  Private to the individual user. Good for personal notes, drafts, experiments.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* MCP Integration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-terracotta/10 rounded-lg">
              <Boxes className="w-5 h-5 text-cm-terracotta" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">MCP Integration</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              The MCP (Model Context Protocol) server enables AI clients to interact with Collective Memory.
              Tools appear as <code className="bg-cm-sand px-1 rounded">mcp__collective-memory__*</code> in Claude.
            </p>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Transport Options</h3>
              <div className="grid md:grid-cols-2 gap-4 mt-2">
                <div>
                  <h4 className="font-medium text-cm-charcoal text-xs mb-1">stdio (Recommended)</h4>
                  <p className="text-xs">
                    Direct process communication. Used by Claude Code, Cursor, VS Code extensions.
                    Simple setup, single user per process.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-cm-charcoal text-xs mb-1">SSE (Server-Sent Events)</h4>
                  <p className="text-xs">
                    HTTP-based transport. Used by web clients like Claude.ai.
                    Supports multi-user with per-session PAT.
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4 mt-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Tool Categories (46 Total)</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                <span>Entity Management (7)</span>
                <span>Relationships (3)</span>
                <span>Context/RAG (2)</span>
                <span>Personas (2)</span>
                <span>Agent Discovery (1)</span>
                <span>Agent Identity (3)</span>
                <span>Team & Scope (3)</span>
                <span>Messaging (5)</span>
                <span>Model Management (4)</span>
                <span>GitHub Repository (4)</span>
                <span>GitHub Sync (2)</span>
                <span>GitHub Work Items (3)</span>
                <span>Activity Monitoring (2)</span>
                <span>Work Sessions (5)</span>
                <span>Milestones (2)</span>
              </div>
            </div>
          </div>
        </section>

        {/* Database Schema */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-amber/10 rounded-lg">
              <Database className="w-5 h-5 text-cm-amber" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Core Database Tables</h2>
          </div>
          <div className="text-sm text-cm-coffee">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Multi-Tenancy</h3>
                <ul className="space-y-1 text-xs font-mono">
                  <li>domains</li>
                  <li>teams</li>
                  <li>users</li>
                  <li>team_members</li>
                </ul>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Knowledge Graph</h3>
                <ul className="space-y-1 text-xs font-mono">
                  <li>entities</li>
                  <li>relationships</li>
                </ul>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Agents & Messaging</h3>
                <ul className="space-y-1 text-xs font-mono">
                  <li>agents</li>
                  <li>messages</li>
                  <li>message_reads</li>
                </ul>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Sessions & Metrics</h3>
                <ul className="space-y-1 text-xs font-mono">
                  <li>work_sessions</li>
                  <li>milestones</li>
                  <li>activities</li>
                  <li>metrics</li>
                </ul>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">AI Configuration</h3>
                <ul className="space-y-1 text-xs font-mono">
                  <li>personas</li>
                  <li>models</li>
                  <li>clients</li>
                </ul>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Projects & GitHub</h3>
                <ul className="space-y-1 text-xs font-mono">
                  <li>projects</li>
                  <li>repositories</li>
                  <li>project_repositories</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Deployment */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-success/10 rounded-lg">
              <Server className="w-5 h-5 text-cm-success" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Deployment Options</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Local Development</h3>
                <div className="font-mono text-xs bg-cm-charcoal text-cm-cream rounded p-2 mt-2">
                  <pre>{`# Start API
python run.py

# Start Frontend
cd web && npm run dev

# MCP via Claude config`}</pre>
                </div>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Docker Deployment</h3>
                <div className="font-mono text-xs bg-cm-charcoal text-cm-cream rounded p-2 mt-2">
                  <pre>{`# Full stack
docker-compose up -d

# Includes:
# - API container
# - Web container
# - MCP container
# - PostgreSQL`}</pre>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Next Steps */}
        <section className="bg-cm-sand/30 border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Next Steps</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <Link
              href="/help/tools"
              className="block p-4 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Tool Reference</h3>
              <p className="text-sm text-cm-coffee mt-1">
                Complete documentation for all 46 MCP tools.
              </p>
            </Link>
            <Link
              href="/help/claude-code"
              className="block p-4 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Claude Code Setup</h3>
              <p className="text-sm text-cm-coffee mt-1">
                Configure Claude Code to connect to Collective Memory.
              </p>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
