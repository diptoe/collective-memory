'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function GeminiCliHelpPage() {
  const { user } = useAuthStore();
  const [copiedSSE, setCopiedSSE] = useState(false);
  const [copiedStdio, setCopiedStdio] = useState(false);

  const pat = user?.pat || 'your-personal-access-token';

  // SSE config (recommended) - no Python needed
  const sseConfigSnippet = `{
  "mcpServers": {
    "collective-memory": {
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
              src="/icons/gemini_cli.svg"
              alt="Gemini CLI"
              className="w-10 h-10"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
                (e.target as HTMLImageElement).parentElement!.innerHTML = '<span class="text-3xl">✨</span>';
              }}
            />
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Gemini CLI Configuration
            </h1>
            <p className="text-cm-coffee">
              Google's command-line AI assistant
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
                Locate the Gemini CLI configuration
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                The Gemini CLI configuration file is typically at:
              </p>
              <div className="ml-8 space-y-2">
                <div>
                  <p className="text-xs text-cm-coffee mb-1">macOS/Linux:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    ~/.gemini/settings.json
                  </code>
                </div>
                <div>
                  <p className="text-xs text-cm-coffee mb-1">Windows:</p>
                  <code className="block p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                    %USERPROFILE%\.gemini\settings.json
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
                Add or merge the following into your settings.json:
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
                Start Gemini CLI
              </h3>
              <p className="text-sm text-cm-coffee ml-8">
                Run <code className="bg-cm-sand/50 px-1 rounded">gemini</code> in your terminal.
                The MCP server will be initialized automatically.
              </p>
            </div>

            {/* Step 4 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">4</span>
                Test the connection
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                Verify by asking Gemini to use a Collective Memory tool:
              </p>
              <code className="block ml-8 p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                "Use the identify tool to connect to Collective Memory"
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

        {/* Gemini-Specific Features */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Gemini Integration Tips</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Large Context Window</h3>
              <p className="text-sm text-cm-coffee">
                Gemini's large context window works well with{' '}
                <code className="bg-cm-sand/50 px-1 rounded">get_context</code> for retrieving
                comprehensive documentation and patterns.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Cloud Integration</h3>
              <p className="text-sm text-cm-coffee">
                Use <code className="bg-cm-sand/50 px-1 rounded">search_entities</code> with type
                filters to find GCP-specific configurations and patterns.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Multi-Modal Support</h3>
              <p className="text-sm text-cm-coffee">
                While Collective Memory focuses on text, Gemini can help describe visual elements
                that you then store as entities for future reference.
              </p>
            </div>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">MCP not available?</h3>
              <p className="text-sm text-cm-coffee">
                Ensure you have the latest version of Gemini CLI that supports MCP.
                Check with <code className="bg-cm-sand/50 px-1 rounded">gemini --version</code>.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Authentication issues?</h3>
              <p className="text-sm text-cm-coffee">
                Double-check your PAT in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
                Ensure there's no trailing newline or whitespace.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Server startup errors? (stdio only)</h3>
              <p className="text-sm text-cm-coffee">
                Install uv if not present: <code className="bg-cm-sand/50 px-1 rounded">pip install uv</code>.
                Ensure Python 3.10+ is available.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
