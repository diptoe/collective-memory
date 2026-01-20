'use client';

import Link from 'next/link';
import { ArrowLeft, Code2, AlertTriangle, CheckCircle, Copy, Puzzle, Settings } from 'lucide-react';
import { useState } from 'react';

export default function VSCodeHelpPage() {
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

  const clineConfig = `{
  "mcpServers": {
    "collective-memory": {
      "serverUrl": "https://cm-mcp-sse.diptoe.com/sse"
    }
  }
}`;

  const continueConfig = `{
  "mcpServers": [
    {
      "name": "collective-memory",
      "transport": {
        "type": "sse",
        "url": "https://cm-mcp-sse.diptoe.com/sse"
      }
    }
  ]
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
          <div className="p-3 bg-blue-100 rounded-xl">
            <Code2 className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">VS Code + Copilot</h1>
            <p className="text-cm-coffee">MCP integration options for Visual Studio Code</p>
          </div>
        </div>

        {/* Important Notice */}
        <section className="bg-cm-amber/10 border border-cm-amber/30 rounded-xl p-6 mb-6">
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-6 h-6 text-cm-amber flex-shrink-0 mt-0.5" />
            <div>
              <h2 className="text-lg font-semibold text-cm-charcoal mb-2">GitHub Copilot &amp; MCP</h2>
              <p className="text-sm text-cm-coffee">
                GitHub Copilot does not natively support the Model Context Protocol (MCP). However, there are several
                VS Code extensions that <em>do</em> support MCP and can work alongside or instead of Copilot.
              </p>
            </div>
          </div>
        </section>

        {/* Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">MCP-Compatible Extensions</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Several VS Code extensions support MCP, allowing you to connect Collective Memory to your editor.
            Here are the recommended options:
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Puzzle className="w-4 h-4 text-cm-terracotta" />
                <h3 className="font-medium text-cm-charcoal">Cline</h3>
              </div>
              <p className="text-xs text-cm-coffee mb-2">
                AI assistant with full MCP support. Works with Claude, GPT-4, and other models.
              </p>
              <a
                href="https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-cm-terracotta hover:underline"
              >
                View on Marketplace →
              </a>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Puzzle className="w-4 h-4 text-cm-terracotta" />
                <h3 className="font-medium text-cm-charcoal">Continue</h3>
              </div>
              <p className="text-xs text-cm-coffee mb-2">
                Open-source AI assistant with MCP support. Bring your own API key.
              </p>
              <a
                href="https://marketplace.visualstudio.com/items?itemName=Continue.continue"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-cm-terracotta hover:underline"
              >
                View on Marketplace →
              </a>
            </div>
          </div>
        </section>

        {/* Cline Configuration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">Cline Configuration</h2>
            <span className="px-2 py-0.5 bg-cm-terracotta text-cm-cream text-xs rounded-full">Recommended</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            Cline is the recommended VS Code extension for MCP. It supports both SSE and stdio transports.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Step 1: Install Cline
              </h3>
              <p className="text-sm text-cm-coffee">
                Search for &quot;Cline&quot; in VS Code Extensions (<code className="bg-cm-sand px-1 rounded">Cmd+Shift+X</code>)
                or install from the{' '}
                <a
                  href="https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cm-terracotta hover:underline"
                >
                  VS Code Marketplace
                </a>.
              </p>
            </div>

            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Step 2: Open Cline Settings</h3>
              <p className="text-sm text-cm-coffee">
                Click the Cline icon in the sidebar, then click the gear icon to open settings.
                Navigate to the MCP Servers section.
              </p>
            </div>

            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Step 3: Add CM Configuration (SSE)</h3>
              <div className="relative">
                <pre className="bg-cm-charcoal text-cm-cream text-sm p-4 rounded-lg overflow-x-auto font-mono">
                  {clineConfig}
                </pre>
                <button
                  onClick={() => copyToClipboard(clineConfig, 'cline')}
                  className="absolute top-2 right-2 p-2 bg-cm-coffee/20 hover:bg-cm-coffee/40 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4 text-cm-cream" />
                </button>
                {copiedConfig === 'cline' && (
                  <span className="absolute top-2 right-12 text-xs text-cm-success bg-cm-charcoal px-2 py-1 rounded">
                    Copied!
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-cm-success/10 border border-cm-success/30 rounded-lg">
              <CheckCircle className="w-5 h-5 text-cm-success flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-cm-charcoal">Verify Connection</p>
                <p className="text-cm-coffee">
                  After saving, Cline should show the CM tools available. Ask it to &quot;list available MCP tools&quot;
                  to verify the connection.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Continue Configuration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">Continue Configuration</h2>
            <span className="px-2 py-0.5 bg-cm-sand text-cm-coffee text-xs rounded-full">Alternative</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            Continue is an open-source AI assistant that also supports MCP.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Configuration</h3>
              <p className="text-sm text-cm-coffee mb-2">
                Add to your Continue config file (<code className="bg-cm-sand px-1 rounded">~/.continue/config.json</code>):
              </p>
              <div className="relative">
                <pre className="bg-cm-charcoal text-cm-cream text-sm p-4 rounded-lg overflow-x-auto font-mono">
                  {continueConfig}
                </pre>
                <button
                  onClick={() => copyToClipboard(continueConfig, 'continue')}
                  className="absolute top-2 right-2 p-2 bg-cm-coffee/20 hover:bg-cm-coffee/40 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4 text-cm-cream" />
                </button>
                {copiedConfig === 'continue' && (
                  <span className="absolute top-2 right-12 text-xs text-cm-success bg-cm-charcoal px-2 py-1 rounded">
                    Copied!
                  </span>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* stdio Configuration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">stdio Configuration</h2>
            <span className="px-2 py-0.5 bg-cm-sand text-cm-coffee text-xs rounded-full">Local</span>
          </div>
          <p className="text-sm text-cm-coffee mb-4">
            For local development or air-gapped environments, you can run the MCP server locally.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2">Prerequisites</h3>
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

        {/* Using with Copilot */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Using Alongside Copilot</h2>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              You can use Cline or Continue alongside GitHub Copilot. They serve complementary purposes:
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">GitHub Copilot</h3>
                <ul className="text-xs space-y-1">
                  <li>Inline code completions</li>
                  <li>Quick suggestions as you type</li>
                  <li>Tab-to-complete workflow</li>
                </ul>
              </div>
              <div className="bg-cm-sand/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Cline/Continue + CM</h3>
                <ul className="text-xs space-y-1">
                  <li>Multi-step task execution</li>
                  <li>Persistent knowledge access</li>
                  <li>Cross-session context</li>
                  <li>Multi-agent collaboration</li>
                </ul>
              </div>
            </div>
            <p className="text-xs text-cm-coffee/80 italic">
              Tip: Use Copilot for quick completions and Cline+CM for complex tasks requiring context and collaboration.
            </p>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4 text-sm text-cm-coffee">
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <h3 className="font-medium text-cm-charcoal mb-2">Extension not finding MCP tools</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Reload VS Code window after configuration changes</li>
                <li>Check the extension&apos;s output panel for error messages</li>
                <li>Verify the server URL is accessible</li>
              </ul>
            </div>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <h3 className="font-medium text-cm-charcoal mb-2">Authentication errors</h3>
              <ul className="list-disc list-inside space-y-1">
                <li>Create a PAT in CM web UI (Profile → Access Tokens)</li>
                <li>Include PAT in the server URL: <code className="bg-cm-sand px-1 rounded">?pat=YOUR_PAT</code></li>
                <li>For stdio: set CM_PAT in the env config</li>
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
              href="/help/cursor"
              className="block p-4 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Cursor Setup</h3>
              <p className="text-sm text-cm-coffee mt-1">
                Cursor has native MCP support if you prefer a dedicated AI IDE.
              </p>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
