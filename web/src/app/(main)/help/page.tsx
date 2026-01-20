'use client';

import Link from 'next/link';
import { useState } from 'react';
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
  const [copiedSSE, setCopiedSSE] = useState(false);
  const [copiedStdio, setCopiedStdio] = useState(false);

  const pat = user?.pat || 'your-personal-access-token';

  // SSE config (recommended)
  const sseConfigSnippet = `{
  "mcpServers": {
    "collective-memory": {
      "type": "sse",
      "url": "https://cm-sse.diptoe.ai/sse",
      "headers": {
        "Authorization": "Bearer ${pat}"
      }
    }
  }
}`;

  // Stdio config (alternative)
  const stdioConfigSnippet = `{
  "mcpServers": {
    "collective-memory": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/diptoe/collective-memory", "cm-mcp"],
      "env": {
        "CM_PAT": "${pat}"
      }
    }
  }
}`;

  const copySSEConfig = async () => {
    await navigator.clipboard.writeText(sseConfigSnippet);
    setCopiedSSE(true);
    setTimeout(() => setCopiedSSE(false), 2000);
  };

  const copyStdioConfig = async () => {
    await navigator.clipboard.writeText(stdioConfigSnippet);
    setCopiedStdio(true);
    setTimeout(() => setCopiedStdio(false), 2000);
  };

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
            <li>Choose a transport method: <strong>SSE</strong> (recommended) or <strong>stdio</strong></li>
            <li>Add the MCP server configuration to your client</li>
          </ol>
        </section>

        {/* SSE Configuration (Recommended) */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">Option 1: SSE Transport</h2>
            <span className="px-2 py-0.5 bg-cm-success/20 text-cm-success text-xs font-medium rounded">Recommended</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            Connect to the hosted SSE server at <code className="bg-cm-sand/50 px-1 rounded">cm-sse.diptoe.ai</code>.
            No Python installation required — works immediately with any MCP client.
          </p>

          <div className="mb-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Configuration snippet:</p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
                {sseConfigSnippet}
              </pre>
              <button
                onClick={copySSEConfig}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedSSE ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="bg-cm-sand/30 rounded-lg p-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Benefits:</p>
            <ul className="text-sm text-cm-coffee space-y-1">
              <li>• No local dependencies (Python, uv, etc.)</li>
              <li>• Works on any platform immediately</li>
              <li>• Automatic updates — always uses latest MCP server</li>
              <li>• Lower resource usage on your machine</li>
            </ul>
          </div>
        </section>

        {/* Stdio Configuration (Alternative) */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Option 2: stdio Transport (Local)</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Run the MCP server locally using <code className="bg-cm-sand/50 px-1 rounded">uvx</code>.
            Requires Python 3.10+ and uv installed on your machine.
          </p>

          <div className="mb-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Configuration snippet:</p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
                {stdioConfigSnippet}
              </pre>
              <button
                onClick={copyStdioConfig}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedStdio ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="bg-cm-sand/30 rounded-lg p-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Requirements:</p>
            <ul className="text-sm text-cm-coffee space-y-1">
              <li>• Python 3.10 or higher</li>
              <li>• uv package manager: <code className="bg-cm-sand/50 px-1 rounded">pip install uv</code></li>
            </ul>
          </div>
        </section>

        {/* Client Configuration Guides */}
        <section className="mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Client-Specific Guides</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Click on your client for detailed setup instructions with both SSE and stdio options.
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
              <Link
                href="/help/sse"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🌐</span>
                <span>SSE Transport Details & Self-Hosting</span>
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
