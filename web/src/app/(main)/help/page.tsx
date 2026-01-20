'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/stores/auth-store';

// Client configuration data
const clients = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    icon: '/icons/claude_code.svg',
    description: 'Command-line AI assistant for software development',
    configPath: '~/.claude/settings.json',
  },
  {
    id: 'claude-desktop',
    name: 'Claude Desktop',
    icon: '/icons/claude_desktop.svg',
    description: 'Desktop application for interacting with Claude',
    configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
  },
  {
    id: 'cursor',
    name: 'Cursor',
    icon: '/icons/cursor.svg',
    description: 'AI-powered code editor',
    configPath: '~/.cursor/mcp.json',
  },
  {
    id: 'codex',
    name: 'Codex CLI',
    icon: '/icons/gpt_codex.svg',
    description: 'OpenAI\'s command-line coding assistant',
    configPath: '~/.codex/config.json',
  },
  {
    id: 'gemini-cli',
    name: 'Gemini CLI',
    icon: '/icons/gemini_cli.svg',
    description: 'Google\'s command-line AI assistant',
    configPath: '~/.gemini/settings.json',
  },
];

export default function HelpPage() {
  const { user } = useAuthStore();
  const apiUrl = typeof window !== 'undefined' ? window.location.origin.replace(':3000', ':5001') : 'http://localhost:5001';
  const pat = user?.pat || 'your-personal-access-token';

  return (
    <div className="h-full overflow-auto bg-cm-cream">
      <div className="p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal mb-2">
            Help & Configuration
          </h1>
          <p className="text-cm-coffee">
            Learn how to configure MCP clients to connect to Collective Memory
          </p>
        </div>

        {/* Quick Start */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Quick Start</h2>
          <p className="text-cm-coffee mb-4">
            To connect an AI client to Collective Memory, you need:
          </p>
          <ol className="list-decimal list-inside space-y-2 text-cm-charcoal mb-4">
            <li>Your Personal Access Token (PAT) from <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link></li>
            <li>The API URL: <code className="px-2 py-0.5 bg-cm-sand/50 rounded font-mono text-sm">{apiUrl}</code></li>
            <li>The MCP server configured in your client</li>
          </ol>

          {/* User's config snippet */}
          <div className="mt-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Your MCP Configuration</p>
            <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
{`{
  "mcpServers": {
    "collective-memory": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/diptoe/collective-memory", "cm-mcp"],
      "env": {
        "CM_API_URL": "${apiUrl}",
        "CM_PAT": "${pat}"
      }
    }
  }
}`}
            </pre>
            <p className="text-xs text-cm-coffee mt-2">
              Copy this snippet and adapt it for your specific client below.
            </p>
          </div>
        </section>

        {/* SSE Transport Option */}
        <section className="bg-cm-amber/10 border border-cm-amber/30 rounded-xl p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-cm-amber/20 flex items-center justify-center flex-shrink-0 text-2xl">
              🌐
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-cm-charcoal mb-2">SSE Transport (Remote Server)</h2>
              <p className="text-cm-coffee mb-3">
                For remote/hosted deployments, you can run the MCP server with SSE transport instead of requiring each client to run it locally.
                This eliminates the need for Python on client machines.
              </p>
              <Link
                href="/help/sse"
                className="inline-flex items-center gap-2 px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-terracotta/90 transition-colors text-sm"
              >
                <span>Configure SSE Transport</span>
                <span>→</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Client Configuration Guides */}
        <section className="mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Client Configuration Guides (stdio)</h2>
          <p className="text-sm text-cm-coffee mb-4">
            These guides show how to configure clients to run the MCP server locally using stdio transport (default).
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clients.map((client) => (
              <Link
                key={client.id}
                href={`/help/${client.id}`}
                className="bg-cm-ivory border border-cm-sand rounded-xl p-5 hover:shadow-md transition-shadow group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-cm-sand/50 flex items-center justify-center flex-shrink-0">
                    <img
                      src={client.icon}
                      alt={client.name}
                      className="w-8 h-8"
                      onError={(e) => {
                        // Fallback if icon doesn't exist
                        (e.target as HTMLImageElement).style.display = 'none';
                        (e.target as HTMLImageElement).parentElement!.innerHTML = '<span class="text-2xl">🤖</span>';
                      }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                      {client.name}
                    </h3>
                    <p className="text-sm text-cm-coffee mt-1">{client.description}</p>
                    <p className="text-xs text-cm-coffee/70 mt-2 font-mono truncate">
                      {client.configPath}
                    </p>
                  </div>
                  <span className="text-cm-terracotta opacity-0 group-hover:opacity-100 transition-opacity">
                    →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Additional Resources */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Additional Resources</h2>
          <ul className="space-y-3">
            <li>
              <Link
                href="/settings"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🔑</span>
                <span>Manage your Personal Access Token</span>
              </Link>
            </li>
            <li>
              <a
                href="https://github.com/diptoe/collective-memory"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>📚</span>
                <span>GitHub Repository & Documentation</span>
              </a>
            </li>
            <li>
              <a
                href="https://modelcontextprotocol.io/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🔗</span>
                <span>MCP Protocol Documentation</span>
              </a>
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
