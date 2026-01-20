'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function SSEHelpPage() {
  const { user } = useAuthStore();
  const [copiedHosted, setCopiedHosted] = useState(false);
  const [copiedDocker, setCopiedDocker] = useState(false);
  const [copiedEnv, setCopiedEnv] = useState(false);

  const pat = user?.pat || 'your-personal-access-token';

  // Hosted SSE config
  const hostedConfig = `{
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

  // Docker self-hosting command
  const dockerCommand = `docker run -d \\
  --name cm-sse \\
  -p 8080:8080 \\
  -e CM_MCP_TRANSPORT=sse \\
  -e CM_MCP_SSE_HOST=0.0.0.0 \\
  -e CM_MCP_SSE_PORT=8080 \\
  gcr.io/YOUR_PROJECT/cm-sse:latest`;

  // Environment variables
  const envVars = `CM_MCP_TRANSPORT=sse        # Enable SSE mode (required)
CM_MCP_SSE_HOST=0.0.0.0     # Bind address (default: 0.0.0.0)
CM_MCP_SSE_PORT=8080        # Port (default: 8080)
CM_PAT=your-pat             # Optional: default PAT for single-user mode`;

  const copyHostedConfig = async () => {
    await navigator.clipboard.writeText(hostedConfig);
    setCopiedHosted(true);
    setTimeout(() => setCopiedHosted(false), 2000);
  };

  const copyDockerCommand = async () => {
    await navigator.clipboard.writeText(dockerCommand);
    setCopiedDocker(true);
    setTimeout(() => setCopiedDocker(false), 2000);
  };

  const copyEnvVars = async () => {
    await navigator.clipboard.writeText(envVars);
    setCopiedEnv(true);
    setTimeout(() => setCopiedEnv(false), 2000);
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
              SSE Transport
            </h1>
            <p className="text-cm-coffee">
              Server-Sent Events for remote MCP connections
            </p>
          </div>
        </div>

        {/* Hosted Server - Primary Option */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">Hosted SSE Server</h2>
            <span className="px-2 py-0.5 bg-cm-success/20 text-cm-success text-xs font-medium rounded">Recommended</span>
          </div>
          <p className="text-cm-coffee mb-4">
            We provide a hosted SSE server at <code className="bg-cm-sand/50 px-2 py-0.5 rounded font-mono">cm-sse.diptoe.ai</code> —
            no setup required. Just configure your client and start using Collective Memory.
          </p>

          <div className="mb-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Add this to your MCP client configuration:</p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
                {hostedConfig}
              </pre>
              <button
                onClick={copyHostedConfig}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedHosted ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="bg-cm-success/10 border border-cm-success/30 rounded-lg p-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Why use the hosted server?</p>
            <ul className="text-sm text-cm-coffee space-y-1">
              <li>• No installation or setup required</li>
              <li>• Works on any platform immediately</li>
              <li>• Automatic updates to latest MCP server version</li>
              <li>• Deployed on Google Cloud Run with high availability</li>
            </ul>
          </div>
        </section>

        {/* What is SSE */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">What is SSE Transport?</h2>
          <p className="text-cm-coffee mb-4">
            <strong>SSE (Server-Sent Events)</strong> is an alternative to the default stdio transport.
            Instead of running the MCP server locally as a subprocess, your AI client connects to a
            remote HTTP server over the network.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cm-sand">
                  <th className="text-left py-2 pr-4 text-cm-charcoal font-medium">Feature</th>
                  <th className="text-left py-2 px-4 text-cm-charcoal font-medium">stdio</th>
                  <th className="text-left py-2 pl-4 text-cm-charcoal font-medium">SSE</th>
                </tr>
              </thead>
              <tbody className="text-cm-coffee">
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">How it runs</td>
                  <td className="py-2 px-4">Local subprocess</td>
                  <td className="py-2 pl-4">Remote HTTP server</td>
                </tr>
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">Dependencies</td>
                  <td className="py-2 px-4">Python + uv required</td>
                  <td className="py-2 pl-4">None</td>
                </tr>
                <tr className="border-b border-cm-sand/50">
                  <td className="py-2 pr-4">Updates</td>
                  <td className="py-2 px-4">Each client fetches</td>
                  <td className="py-2 pl-4">Server updates once</td>
                </tr>
                <tr>
                  <td className="py-2 pr-4">Latency</td>
                  <td className="py-2 px-4">Minimal (local)</td>
                  <td className="py-2 pl-4">Network dependent</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Authentication */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Authentication</h2>
          <p className="text-cm-coffee mb-4">
            The hosted SSE server uses your Personal Access Token (PAT) for authentication.
            Include it in the <code className="bg-cm-sand/50 px-1 rounded">Authorization</code> header:
          </p>
          <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto mb-4">
{`"headers": {
  "Authorization": "Bearer ${pat}"
}`}
          </pre>
          <p className="text-sm text-cm-coffee">
            Your PAT is available in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
            Each API call uses your PAT to authenticate and scope data to your account.
          </p>
        </section>

        {/* Self-Hosting Section */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Self-Hosting (Advanced)</h2>
          <p className="text-cm-coffee mb-4">
            If you prefer to run your own SSE server, you can deploy the MCP server with SSE transport enabled.
          </p>

          <div className="mb-6">
            <h3 className="font-medium text-cm-charcoal mb-2">Docker Deployment</h3>
            <p className="text-sm text-cm-coffee mb-3">
              Use the pre-built Docker image or build from <code className="bg-cm-sand/50 px-1 rounded">Dockerfile.mcp</code>:
            </p>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                {dockerCommand}
              </pre>
              <button
                onClick={copyDockerCommand}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedDocker ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="mb-4">
            <h3 className="font-medium text-cm-charcoal mb-2">Environment Variables</h3>
            <div className="relative">
              <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                {envVars}
              </pre>
              <button
                onClick={copyEnvVars}
                className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
              >
                {copiedEnv ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="bg-cm-sand/30 rounded-lg p-4">
            <p className="text-sm font-medium text-cm-charcoal mb-2">Deployment modes:</p>
            <ul className="text-sm text-cm-coffee space-y-2">
              <li>
                <strong>Multi-user (recommended):</strong> Don't set <code className="bg-cm-sand/50 px-1 rounded">CM_PAT</code> —
                clients pass their own PAT via Authorization header
              </li>
              <li>
                <strong>Single-user:</strong> Set <code className="bg-cm-sand/50 px-1 rounded">CM_PAT</code> on the server —
                all requests use that token
              </li>
            </ul>
          </div>
        </section>

        {/* SSE Endpoints */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Server Endpoints</h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <code className="bg-cm-sand/50 px-2 py-1 rounded text-sm font-mono text-cm-charcoal whitespace-nowrap">GET /sse</code>
              <p className="text-sm text-cm-coffee">SSE connection endpoint — this is what clients connect to</p>
            </div>
            <div className="flex items-start gap-3">
              <code className="bg-cm-sand/50 px-2 py-1 rounded text-sm font-mono text-cm-charcoal whitespace-nowrap">POST /messages/</code>
              <p className="text-sm text-cm-coffee">Message handling for tool calls (used internally)</p>
            </div>
            <div className="flex items-start gap-3">
              <code className="bg-cm-sand/50 px-2 py-1 rounded text-sm font-mono text-cm-charcoal whitespace-nowrap">GET /health</code>
              <p className="text-sm text-cm-coffee">Health check endpoint for monitoring</p>
            </div>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Connection refused?</h3>
              <p className="text-sm text-cm-coffee">
                For the hosted server, check your internet connection. For self-hosted, ensure the server is running
                and the port is accessible. Test with: <code className="bg-cm-sand/50 px-1 rounded">curl https://cm-sse.diptoe.ai/health</code>
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Authentication errors (401/403)?</h3>
              <p className="text-sm text-cm-coffee">
                Verify your PAT is correct in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
                Ensure the Authorization header is formatted as <code className="bg-cm-sand/50 px-1 rounded">Bearer your-pat</code>.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Client doesn't support SSE?</h3>
              <p className="text-sm text-cm-coffee">
                Most modern MCP clients support SSE transport. If yours doesn't, use the stdio transport instead
                with <code className="bg-cm-sand/50 px-1 rounded">uvx</code>. See the <Link href="/help" className="text-cm-terracotta hover:underline">main help page</Link> for details.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Client doesn't support custom headers?</h3>
              <p className="text-sm text-cm-coffee">
                If your client can't send Authorization headers, use stdio transport instead or self-host
                with <code className="bg-cm-sand/50 px-1 rounded">CM_PAT</code> set on the server.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
