'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function SSEHelpPage() {
  const { user } = useAuthStore();
  const [copiedPersonal, setCopiedPersonal] = useState(false);
  const [copiedShared, setCopiedShared] = useState(false);
  const [copiedServer, setCopiedServer] = useState(false);
  const [copiedClient, setCopiedClient] = useState(false);
  const [copiedClientAuth, setCopiedClientAuth] = useState(false);

  const apiUrl = typeof window !== 'undefined'
    ? window.location.origin.replace(':3000', ':5001').replace('cm.diptoe.ai', 'cm-api.diptoe.ai')
    : 'http://localhost:5001';
  const pat = user?.pat || 'your-personal-access-token';

  // Personal deployment - PAT baked into server
  const personalServerCommand = `# Install with SSE dependencies
pip install "collective-memory[sse]"

# Run with your PAT baked in (single-user)
CM_MCP_TRANSPORT=sse \\
CM_MCP_SSE_PORT=8080 \\
CM_PAT="${pat}" \\
python -m cm_mcp.server`;

  // Shared deployment - PAT from client headers
  const sharedServerCommand = `# Install with SSE dependencies
pip install "collective-memory[sse]"

# Run without PAT (multi-user mode)
CM_MCP_TRANSPORT=sse \\
CM_MCP_SSE_PORT=8080 \\
python -m cm_mcp.server`;

  // Legacy serverCommand for backwards compatibility
  const serverCommand = personalServerCommand;

  const clientConfig = `{
  "mcpServers": {
    "collective-memory": {
      "url": "http://your-sse-server:8080/sse"
    }
  }
}`;

  // Client config with Authorization header (for shared deployment)
  const clientConfigWithAuth = `{
  "mcpServers": {
    "collective-memory": {
      "url": "http://your-sse-server:8080/sse",
      "headers": {
        "Authorization": "Bearer ${pat}"
      }
    }
  }
}`;

  const copyPersonalCommand = async () => {
    await navigator.clipboard.writeText(personalServerCommand);
    setCopiedPersonal(true);
    setTimeout(() => setCopiedPersonal(false), 2000);
  };

  const copySharedCommand = async () => {
    await navigator.clipboard.writeText(sharedServerCommand);
    setCopiedShared(true);
    setTimeout(() => setCopiedShared(false), 2000);
  };

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

  const copyClientAuthConfig = async () => {
    await navigator.clipboard.writeText(clientConfigWithAuth);
    setCopiedClientAuth(true);
    setTimeout(() => setCopiedClientAuth(false), 2000);
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

        {/* Deployment Modes */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Deployment Modes</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Choose the deployment mode that fits your use case:
          </p>

          {/* Personal Deployment */}
          <div className="mb-6">
            <h3 className="font-medium text-cm-charcoal mb-2">Option A: Personal Deployment (Recommended for Getting Started)</h3>
            <p className="text-sm text-cm-coffee mb-3">
              Your PAT is configured on the server. Simple setup, but each user needs their own server instance.
            </p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                {personalServerCommand}
              </pre>
              <button
                onClick={copyPersonalCommand}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedPersonal ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          {/* Shared Deployment */}
          <div className="mb-4">
            <h3 className="font-medium text-cm-charcoal mb-2">Option B: Shared Deployment (Multi-User)</h3>
            <p className="text-sm text-cm-coffee mb-3">
              Multiple users share one server. Each client passes their PAT via the Authorization header.
              Ideal for team or cloud deployments.
            </p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                {sharedServerCommand}
              </pre>
              <button
                onClick={copySharedCommand}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedShared ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="p-4 bg-cm-sand/30 rounded-lg">
            <p className="text-xs font-medium text-cm-charcoal mb-2">Environment Variables:</p>
            <ul className="text-xs text-cm-coffee space-y-1">
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_MCP_TRANSPORT=sse</code> — Enable SSE mode</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_MCP_SSE_HOST=0.0.0.0</code> — Bind to all interfaces (default)</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_MCP_SSE_PORT=8080</code> — Server port (default: 8080)</li>
              <li><code className="bg-cm-sand/50 px-1 rounded">CM_PAT</code> — Your PAT (Option A only, optional fallback for Option B)</li>
            </ul>
          </div>
        </section>

        {/* Client Configuration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Client Configuration</h2>

          {/* Basic config (for personal deployment) */}
          <div className="mb-6">
            <h3 className="font-medium text-cm-charcoal mb-2">For Personal Deployment (Option A)</h3>
            <p className="text-sm text-cm-coffee mb-3">
              Simple URL-only configuration when PAT is on the server:
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
          </div>

          {/* Config with headers (for shared deployment) */}
          <div className="mb-4">
            <h3 className="font-medium text-cm-charcoal mb-2">For Shared Deployment (Option B)</h3>
            <p className="text-sm text-cm-coffee mb-3">
              Include your PAT in the Authorization header:
            </p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
                {clientConfigWithAuth}
              </pre>
              <button
                onClick={copyClientAuthConfig}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedClientAuth ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="text-xs text-cm-coffee mt-2">
              Note: Header support varies by MCP client. Check your client's documentation.
            </p>
          </div>

          <p className="text-xs text-cm-coffee">
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
            The SSE server can be deployed to cloud services like Google Cloud Run. For shared multi-user
            deployments, don't set CM_PAT — clients will provide their own PAT via the Authorization header.
          </p>
          <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
{`# Shared deployment (multi-user, no PAT baked in)
docker run -d \\
  -p 8080:8080 \\
  -e CM_MCP_TRANSPORT=sse \\
  collective-memory-mcp`}
          </pre>
          <p className="text-xs text-cm-coffee mt-4 mb-2">
            Or for personal deployment with PAT:
          </p>
          <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
{`# Personal deployment (single-user, PAT on server)
docker run -d \\
  -p 8080:8080 \\
  -e CM_MCP_TRANSPORT=sse \\
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
                For <strong>personal deployment</strong>: Verify CM_PAT is set on the server.
                For <strong>shared deployment</strong>: Ensure your client is sending the Authorization header
                with your PAT. Verify your PAT in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Client doesn't support headers?</h3>
              <p className="text-sm text-cm-coffee">
                If your MCP client doesn't support custom headers, use the personal deployment mode
                (Option A) with CM_PAT set on the server instead.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
