'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function SSEHelpPage() {
  const { user } = useAuthStore();
  const [copiedServer, setCopiedServer] = useState(false);
  const [copiedClient, setCopiedClient] = useState(false);

  const apiUrl = typeof window !== 'undefined'
    ? window.location.origin.replace(':3000', ':5001').replace('cm.diptoe.ai', 'cm-api.diptoe.ai')
    : 'http://localhost:5001';
  const pat = user?.pat || 'your-personal-access-token';

  const serverCommand = `# Install with SSE dependencies
pip install "collective-memory[sse]"

# Or install manually
pip install starlette uvicorn

# Run the SSE server
CM_MCP_TRANSPORT=sse \\
CM_MCP_SSE_PORT=8080 \\
CM_API_URL="${apiUrl}" \\
CM_PAT="${pat}" \\
python -m cm_mcp.server`;

  const clientConfig = `{
  "mcpServers": {
    "collective-memory": {
      "url": "http://your-sse-server:8080/sse"
    }
  }
}`;

  const copyServerCommand = async () => {
    await navigator.clipboard.writeText(serverCommand);
    setCopiedServer(true);
    setTimeout(() => setCopiedServer(false), 2000);
  };

  const copyClientConfig = async () => {
    await navigator.clipboard.writeText(clientConfig);
    setCopiedClient(true);
    setTimeout(() => setCopiedClient(false), 2000);
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
          <div className="w-16 h-16 rounded-xl bg-cm-amber/20 flex items-center justify-center text-3xl">
            🌐
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              SSE Transport Configuration
            </h1>
            <p className="text-cm-coffee">
              Server-Sent Events for remote MCP server deployments
            </p>
          </div>
        </div>

        {/* Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">What is SSE Transport?</h2>
          <p className="text-cm-coffee mb-4">
            By default, the Collective Memory MCP server uses <strong>stdio transport</strong>, which runs as a local
            process managed by your AI client. This requires Python and the MCP dependencies on each machine.
          </p>
          <p className="text-cm-coffee mb-4">
            <strong>SSE (Server-Sent Events) transport</strong> runs the MCP server as an HTTP service that clients
            connect to remotely. Benefits include:
          </p>
          <ul className="list-disc list-inside space-y-2 text-cm-coffee">
            <li>No Python installation required on client machines</li>
            <li>Centralized server deployment and management</li>
            <li>Easier updates — update once on the server</li>
            <li>Can be deployed to cloud services (Cloud Run, etc.)</li>
          </ul>
        </section>

        {/* Comparison Table */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">stdio vs SSE Comparison</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cm-sand">
                  <th className="text-left py-2 pr-4 text-cm-charcoal font-medium">Feature</th>
                  <th className="text-left py-2 px-4 text-cm-charcoal font-medium">stdio (Default)</th>
                  <th className="text-left py-2 pl-4 text-cm-charcoal font-medium">SSE (Remote)</th>
                </tr>
              </thead>
              <tbody className="text-cm-coffee">
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">Setup</td>
                  <td className="py-2 px-4">Client runs server locally</td>
                  <td className="py-2 pl-4">Central server, clients connect</td>
                </tr>
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">Dependencies</td>
                  <td className="py-2 px-4">Python + uv on each machine</td>
                  <td className="py-2 pl-4">None on client machines</td>
                </tr>
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">Latency</td>
                  <td className="py-2 px-4">Minimal (local)</td>
                  <td className="py-2 pl-4">Network dependent</td>
                </tr>
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">Updates</td>
                  <td className="py-2 px-4">Each client fetches</td>
                  <td className="py-2 pl-4">Update server once</td>
                </tr>
                <tr>
                  <td className="py-2 pr-4">Client Support</td>
                  <td className="py-2 px-4">All MCP clients</td>
                  <td className="py-2 pl-4">Claude Desktop, most others</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Server Setup */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Step 1: Run the SSE Server</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Run these commands on the machine that will host the MCP server:
          </p>
          <div className="relative">
            <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto whitespace-pre-wrap">
              {serverCommand}
            </pre>
            <button
              onClick={copyServerCommand}
              className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
            >
              {copiedServer ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div className="mt-4 p-4 bg-cm-sand/30 rounded-lg">
            <p className="text-xs font-medium text-cm-charcoal mb-2">Environment Variables:</p>
            <ul className="text-xs text-cm-coffee space-y-1">
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_MCP_TRANSPORT=sse</code> — Enable SSE mode</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_MCP_SSE_HOST=0.0.0.0</code> — Bind to all interfaces (default)</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_MCP_SSE_PORT=8080</code> — Server port (default: 8080)</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_API_URL</code> — Collective Memory API URL</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_PAT</code> — Your Personal Access Token</li>
            </ul>
          </div>
        </section>

        {/* Client Configuration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Step 2: Configure AI Clients</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Configure your AI clients to connect to the SSE server URL:
          </p>
          <div className="relative">
            <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
              {clientConfig}
            </pre>
            <button
              onClick={copyClientConfig}
              className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
            >
              {copiedClient ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <p className="text-xs text-cm-coffee mt-2">
            Replace <code className="bg-cm-sand/50 px-1 rounded">your-sse-server:8080</code> with your actual server address.
          </p>
        </section>

        {/* Endpoints */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">SSE Server Endpoints</h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <code className="bg-cm-sand/50 px-2 py-1 rounded text-sm font-mono text-cm-charcoal">GET /sse</code>
              <p className="text-sm text-cm-coffee">SSE connection endpoint for MCP clients</p>
            </div>
            <div className="flex items-start gap-3">
              <code className="bg-cm-sand/50 px-2 py-1 rounded text-sm font-mono text-cm-charcoal">POST /messages/</code>
              <p className="text-sm text-cm-coffee">Message handling endpoint for tool calls</p>
            </div>
            <div className="flex items-start gap-3">
              <code className="bg-cm-sand/50 px-2 py-1 rounded text-sm font-mono text-cm-charcoal">GET /health</code>
              <p className="text-sm text-cm-coffee">Health check endpoint for monitoring</p>
            </div>
          </div>
        </section>

        {/* Docker/Cloud Deployment */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Cloud Deployment</h2>
          <p className="text-sm text-cm-coffee mb-4">
            The SSE server can be deployed to cloud services. Example Docker command:
          </p>
          <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
{`docker run -d \\
  -p 8080:8080 \\
  -e CM_MCP_TRANSPORT=sse \\
  -e CM_API_URL=${apiUrl} \\
  -e CM_PAT=${pat} \\
  collective-memory-mcp`}
          </pre>
          <p className="text-xs text-cm-coffee mt-2">
            For Google Cloud Run, use the included <code className="bg-cm-sand/50 px-1 rounded">Dockerfile.mcp</code>.
          </p>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Connection refused?</h3>
              <p className="text-sm text-cm-coffee">
                Ensure the SSE server is running and accessible. Check firewall rules and that
                the port is open. Test with: <code className="bg-cm-sand/50 px-1 rounded">curl http://your-server:8080/health</code>
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Missing dependencies?</h3>
              <p className="text-sm text-cm-coffee">
                Install SSE dependencies: <code className="bg-cm-sand/50 px-1 rounded">pip install starlette uvicorn</code>
                or <code className="bg-cm-sand/50 px-1 rounded">pip install "collective-memory[sse]"</code>
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Client not connecting?</h3>
              <p className="text-sm text-cm-coffee">
                Verify your client supports SSE transport. Check that the URL includes <code className="bg-cm-sand/50 px-1 rounded">/sse</code>
                at the end (e.g., <code className="bg-cm-sand/50 px-1 rounded">http://server:8080/sse</code>).
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Authentication errors?</h3>
              <p className="text-sm text-cm-coffee">
                The PAT is set on the server, not the client. Verify your PAT in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
