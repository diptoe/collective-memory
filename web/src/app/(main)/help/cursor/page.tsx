'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function CursorHelpPage() {
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
              src="/icons/cursor.svg"
              alt="Cursor"
              className="w-10 h-10"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
                (e.target as HTMLImageElement).parentElement!.innerHTML = '<span class="text-3xl">⌨️</span>';
              }}
            />
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Cursor Configuration
            </h1>
            <p className="text-cm-coffee">
              AI-powered code editor with MCP support
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
                Open Cursor Settings
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                Open Cursor and go to Settings → Features → MCP Servers, or create the config file directly:
              </p>
              <div className="ml-8 space-y-2">
                <div>
                  <p className="text-xs text-cm-coffee mb-1">macOS/Linux:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    ~/.cursor/mcp.json
                  </code>
                </div>
                <div>
                  <p className="text-xs text-cm-coffee mb-1">Windows:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    %USERPROFILE%\.cursor\mcp.json
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
                Create or edit the mcp.json file with:
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
                Restart Cursor
              </h3>
              <p className="text-sm text-cm-coffee ml-8">
                Close and reopen Cursor. The MCP server will be loaded when you start a new AI chat.
              </p>
            </div>

            {/* Step 4 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">4</span>
                Use the tools
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                In Cursor's AI chat (Cmd/Ctrl + L), you can now use Collective Memory tools:
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

        {/* Cursor-Specific Features */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Cursor-Specific Tips</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Context from Current File</h3>
              <p className="text-sm text-cm-coffee">
                Cursor automatically includes context from your current file. Combine this with
                Collective Memory to search for related patterns or documentation.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Multi-File Edits</h3>
              <p className="text-sm text-cm-coffee">
                Use <code className="bg-cm-sand/50 px-1 rounded">get_context</code> to retrieve relevant
                entities before making multi-file changes, ensuring consistency.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Recording Work</h3>
              <p className="text-sm text-cm-coffee">
                Use <code className="bg-cm-sand/50 px-1 rounded">start_session</code> and{' '}
                <code className="bg-cm-sand/50 px-1 rounded">record_milestone</code> to track significant
                coding sessions and achievements.
              </p>
            </div>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">MCP not loading?</h3>
              <p className="text-sm text-cm-coffee">
                Check that Cursor has MCP support enabled in Settings → Features.
                Some Cursor versions may require a paid plan for MCP.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Tools not available in chat?</h3>
              <p className="text-sm text-cm-coffee">
                Try starting a new chat session. MCP servers are loaded when a new chat begins.
                Check the Cursor output panel for any error messages.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Connection issues?</h3>
              <p className="text-sm text-cm-coffee">
                Verify your PAT in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
                Ensure the SSE server is accessible from your network.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
