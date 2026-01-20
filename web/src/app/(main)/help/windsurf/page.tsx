'use client';

import Link from 'next/link';
import { ArrowLeft, Wind, CheckCircle, AlertCircle, Copy, Settings, Terminal } from 'lucide-react';
import { useState } from 'react';

export default function WindsurfHelpPage() {
  const [copiedConfig, setCopiedConfig] = useState<string | null>(null);

  const copyToClipboard = async (text: string, configId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedConfig(configId);
      setTimeout(() => setCopiedConfig(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const sseConfig = `{
  "mcpServers": {
    "collective-memory": {
      "serverUrl": "https://cm-mcp-sse.diptoe.com/sse"
    }
  }
}`;

  const sseConfigWithPat = `{
  "mcpServers": {
    "collective-memory": {
      "serverUrl": "https://cm-mcp-sse.diptoe.com/sse?pat=YOUR_PAT_HERE"
    }
  }
}`;

  const stdioConfig = `{
  "mcpServers": {
    "collective-memory": {
      "command": "python",
      "args": ["-m", "cm_mcp.server"],
      "cwd": "/path/to/collective-memory",
      "env": {
        "CM_API_URL": "https://cm-api.diptoe.com",
        "CM_PAT": "YOUR_PAT_HERE"
      }
    }
  }
}`;

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

        {/* Page Title */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-emerald-100 rounded-xl">
            <Wind className="w-8 h-8 text-emerald-600" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">Windsurf</h1>
            <p className="text-cm-coffee">AI-powered IDE by Codeium</p>
          </div>
        </div>

        {/* Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Overview</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Windsurf is an AI-powered IDE built by Codeium that supports the Model Context Protocol (MCP).
            This allows Windsurf&apos;s AI assistant (Cascade) to connect to Collective Memory for persistent
            knowledge and multi-agent collaboration.
          </p>
          <div className="flex items-start gap-3 p-4 bg-cm-success/10 border border-cm-success/30 rounded-lg">
            <CheckCircle className="w-5 h-5 text-cm-success flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-cm-charcoal">MCP Support</p>
              <p className="text-cm-coffee">
                Windsurf has native MCP support. Configure CM in settings and the tools will be available to Cascade.
              </p>
            </div>
          </div>
        </section>

        {/* SSE Configuration (Recommended) */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">SSE Configuration</h2>
            <span className="px-2 py-0.5 bg-cm-terracotta text-cm-cream text-xs rounded-full">Recommended</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            Server-Sent Events (SSE) is the recommended transport for Windsurf. It connects to a hosted MCP server
            without requiring local Python installation.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Step 1: Open Windsurf Settings
              </h3>
              <p className="text-sm text-cm-coffee">
                Open Windsurf Settings (<code className="bg-cm-sand px-1 rounded">Cmd+,</code> on Mac, <code className="bg-cm-sand px-1 rounded">Ctrl+,</code> on Windows/Linux)
                and navigate to the MCP Servers section.
              </p>
            </div>

            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Step 2: Add SSE Configuration</h3>
              <p className="text-sm text-cm-coffee mb-2">
                Add the following configuration to your MCP servers:
              </p>
              <div className="relative">
                <pre className="bg-cm-charcoal text-cm-cream text-sm p-4 rounded-lg overflow-x-auto font-mono">
                  {sseConfig}
                </pre>
                <button
                  onClick={() => copyToClipboard(sseConfig, 'sse')}
                  className="absolute top-2 right-2 p-2 bg-cm-coffee/20 hover:bg-cm-coffee/40 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4 text-cm-cream" />
                </button>
                {copiedConfig === 'sse' && (
                  <span className="absolute top-2 right-12 text-xs text-cm-success bg-cm-charcoal px-2 py-1 rounded">
                    Copied!
                  </span>
                )}
              </div>
            </div>

            <div className="p-4 bg-cm-amber/10 border border-cm-amber/30 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-cm-amber flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-cm-charcoal">Passing PAT via URL</p>
                  <p className="text-cm-coffee">
                    If you need to pass your Personal Access Token in the URL (for server-side authentication), use:
                  </p>
                  <pre className="bg-cm-charcoal text-cm-cream text-xs p-2 rounded mt-2 overflow-x-auto font-mono">
                    {sseConfigWithPat}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* stdio Configuration (Alternative) */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">stdio Configuration</h2>
            <span className="px-2 py-0.5 bg-cm-sand text-cm-coffee text-xs rounded-full">Alternative</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            If you prefer to run the MCP server locally (useful for development or air-gapped environments),
            you can use the stdio transport.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Prerequisites
              </h3>
              <ul className="text-sm text-cm-coffee list-disc list-inside space-y-1">
                <li>Python 3.11+ installed</li>
                <li>Clone the collective-memory repository</li>
                <li>Install dependencies: <code className="bg-cm-sand px-1 rounded">pip install -r requirements.txt</code></li>
              </ul>
            </div>

            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Configuration</h3>
              <div className="relative">
                <pre className="bg-cm-charcoal text-cm-cream text-sm p-4 rounded-lg overflow-x-auto font-mono">
                  {stdioConfig}
                </pre>
                <button
                  onClick={() => copyToClipboard(stdioConfig, 'stdio')}
                  className="absolute top-2 right-2 p-2 bg-cm-coffee/20 hover:bg-cm-coffee/40 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4 text-cm-cream" />
                </button>
                {copiedConfig === 'stdio' && (
                  <span className="absolute top-2 right-12 text-xs text-cm-success bg-cm-charcoal px-2 py-1 rounded">
                    Copied!
                  </span>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Windsurf-Specific Tips */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Windsurf Tips</h2>
          <div className="space-y-4 text-sm text-cm-coffee">
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <div>
                <p className="font-medium text-cm-charcoal">Use Cascade for CM Interactions</p>
                <p>
                  Cascade (Windsurf&apos;s AI) will automatically have access to CM tools. Ask it to &quot;identify with Collective Memory&quot;
                  or &quot;search for entities about authentication&quot;.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <div>
                <p className="font-medium text-cm-charcoal">Start Work Sessions</p>
                <p>
                  When beginning focused work, ask Cascade to &quot;start a work session&quot;. This will track your
                  progress and link entities created during the session.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <div>
                <p className="font-medium text-cm-charcoal">Record Milestones</p>
                <p>
                  After completing significant work, ask Cascade to &quot;record a milestone&quot; to track
                  what was accomplished for future reference.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4 text-sm text-cm-coffee">
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <h3 className="font-medium text-cm-charcoal mb-2">MCP tools not appearing</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Restart Windsurf after adding the configuration</li>
                <li>Check that the server URL is correct</li>
                <li>Look for error messages in the Windsurf output panel</li>
              </ul>
            </div>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <h3 className="font-medium text-cm-charcoal mb-2">Authentication errors</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Verify your PAT is valid (create one in CM web UI under Profile → Access Tokens)</li>
                <li>Check that the PAT is correctly included in the URL or environment variable</li>
                <li>Ensure the PAT has not expired</li>
              </ul>
            </div>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <h3 className="font-medium text-cm-charcoal mb-2">Connection timeouts</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Check your internet connection</li>
                <li>Verify the CM API server is accessible</li>
                <li>For stdio: ensure Python and dependencies are correctly installed</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Related Links */}
        <section className="bg-cm-sand/30 border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Related</h2>
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
              href="/help/guides/getting-started"
              className="block p-4 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Getting Started</h3>
              <p className="text-sm text-cm-coffee mt-1">
                Step-by-step guide to start using Collective Memory.
              </p>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
