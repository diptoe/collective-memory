'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function ClaudeDesktopHelpPage() {
  const { user } = useAuthStore();
  const [copiedSSE, setCopiedSSE] = useState(false);
  const [copiedStdio, setCopiedStdio] = useState(false);

  const pat = user?.pat || 'your-personal-access-token';

  // SSE config (recommended) - no Python needed
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

  // Stdio config (alternative) - requires Python/uvx
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
        {/* Breadcrumb */}
        <nav className="mb-4">
          <Link href="/help" className="text-cm-coffee hover:text-cm-terracotta transition-colors">
            ← Back to Help
          </Link>
        </nav>

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <div className="w-16 h-16 rounded-xl bg-cm-sand/50 flex items-center justify-center">
            <img
              src="/icons/claude_desktop.svg"
              alt="Claude Desktop"
              className="w-10 h-10"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
                (e.target as HTMLImageElement).parentElement!.innerHTML = '<span class="text-3xl">🖥️</span>';
              }}
            />
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Claude Desktop Configuration
            </h1>
            <p className="text-cm-coffee">
              Desktop application for interacting with Claude
            </p>
          </div>
        </div>

        {/* SSE Configuration (Recommended) */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">SSE Configuration</h2>
            <span className="px-2 py-0.5 bg-cm-success/20 text-cm-success text-xs font-medium rounded">Recommended</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            Connect to the hosted SSE server — no Python installation required.
          </p>

          <div className="space-y-6">
            {/* Step 1 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">1</span>
                Locate the configuration file
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                The Claude Desktop configuration file is located at:
              </p>
              <div className="ml-8 space-y-2">
                <div>
                  <p className="text-xs text-cm-coffee mb-1">macOS:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    ~/Library/Application Support/Claude/claude_desktop_config.json
                  </code>
                </div>
                <div>
                  <p className="text-xs text-cm-coffee mb-1">Windows:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    %APPDATA%\Claude\claude_desktop_config.json
                  </code>
                </div>
                <div>
                  <p className="text-xs text-cm-coffee mb-1">Linux:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    ~/.config/Claude/claude_desktop_config.json
                  </code>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">2</span>
                Add the MCP server configuration
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                Create or edit the file with the following configuration:
              </p>
              <div className="ml-8 relative">
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

            {/* Step 3 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">3</span>
                Restart Claude Desktop
              </h3>
              <p className="text-sm text-cm-coffee ml-8">
                Quit Claude Desktop completely (check the system tray/menu bar) and reopen it.
                The MCP server will be loaded automatically.
              </p>
            </div>

            {/* Step 4 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">4</span>
                Verify the connection
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                In Claude Desktop, you should see the MCP tools icon (🔌) in the chat interface.
                Click it to see available Collective Memory tools, or ask:
              </p>
              <code className="block ml-8 p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                "Use the identify tool to register yourself with Collective Memory"
              </code>
            </div>
          </div>
        </section>

        {/* Alternative: stdio (Local) */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Alternative: Local stdio Setup</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Run the MCP server locally using uvx. Requires Python 3.10+ and uv installed.
          </p>
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
          <p className="text-xs text-cm-coffee mt-2">
            Install uv with <code className="bg-cm-sand/50 px-1 rounded">pip install uv</code> if needed.
          </p>
        </section>

        {/* Quick Open Commands */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Quick Open Commands</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Use these commands to quickly open the config directory:
          </p>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-cm-coffee mb-1">macOS (Terminal):</p>
              <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                open ~/Library/Application\ Support/Claude/
              </code>
            </div>
            <div>
              <p className="text-xs text-cm-coffee mb-1">Windows (PowerShell):</p>
              <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                explorer $env:APPDATA\Claude
              </code>
            </div>
            <div>
              <p className="text-xs text-cm-coffee mb-1">Linux (Terminal):</p>
              <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                xdg-open ~/.config/Claude/
              </code>
            </div>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">MCP tools not appearing?</h3>
              <p className="text-sm text-cm-coffee">
                Ensure the JSON file is valid (no trailing commas, proper quotes).
                Try using a JSON validator to check for syntax errors.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Authentication errors?</h3>
              <p className="text-sm text-cm-coffee">
                Verify your PAT is correct in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
                Make sure there are no extra spaces or newlines in the token.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Python not found? (stdio only)</h3>
              <p className="text-sm text-cm-coffee">
                Install Python 3.10+ and ensure it's in your PATH. Install uv with{' '}
                <code className="bg-cm-sand/50 px-1 rounded">pip install uv</code>.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
