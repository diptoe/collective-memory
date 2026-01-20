'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function ClaudeCodeHelpPage() {
  const { user } = useAuthStore();
  const [copied, setCopied] = useState(false);

  const apiUrl = typeof window !== 'undefined'
    ? window.location.origin.replace(':3000', ':5001').replace('cm.diptoe.ai', 'cm-api.diptoe.ai')
    : 'http://localhost:5001';
  const pat = user?.pat || 'your-personal-access-token';

  const configSnippet = `{
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
}`;

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(configSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
              src="/icons/clients/claude-code.svg"
              alt="Claude Code"
              className="w-10 h-10"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
                (e.target as HTMLImageElement).parentElement!.innerHTML = '<span class="text-3xl">💻</span>';
              }}
            />
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Claude Code Configuration
            </h1>
            <p className="text-cm-coffee">
              Command-line AI assistant for software development
            </p>
          </div>
        </div>

        {/* Configuration Steps */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Configuration Steps</h2>

          <div className="space-y-6">
            {/* Step 1 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">1</span>
                Open your Claude Code settings file
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                The settings file is located at:
              </p>
              <code className="block ml-8 p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                ~/.claude/settings.json
              </code>
              <p className="text-xs text-cm-coffee ml-8 mt-2">
                On macOS/Linux, this is in your home directory. On Windows, it's typically at{' '}
                <code className="bg-cm-sand/50 px-1 rounded">%USERPROFILE%\.claude\settings.json</code>
              </p>
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
                  {configSnippet}
                </pre>
                <button
                  onClick={copyToClipboard}
                  className="absolute top-2 right-2 px-3 py-1 bg-cm-ivory/20 hover:bg-cm-ivory/30 text-cm-cream text-xs rounded transition-colors"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>

            {/* Step 3 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">3</span>
                Restart Claude Code
              </h3>
              <p className="text-sm text-cm-coffee ml-8">
                After saving the configuration, restart Claude Code for the changes to take effect.
                The MCP server will be available as <code className="bg-cm-sand/50 px-1 rounded">collective-memory</code>.
              </p>
            </div>

            {/* Step 4 */}
            <div>
              <h3 className="font-medium text-cm-charcoal mb-2 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">4</span>
                Verify the connection
              </h3>
              <p className="text-sm text-cm-coffee ml-8 mb-2">
                In Claude Code, you can verify the MCP server is connected by asking Claude to use a Collective Memory tool:
              </p>
              <code className="block ml-8 p-3 bg-cm-sand/50 rounded-lg font-mono text-sm text-cm-charcoal">
                "Use the identify tool to register yourself with Collective Memory"
              </code>
            </div>
          </div>
        </section>

        {/* Alternative: Local Development */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Alternative: Local Development Setup</h2>
          <p className="text-sm text-cm-coffee mb-4">
            If you're running the Collective Memory server locally or want to use a local clone:
          </p>
          <pre className="p-4 bg-cm-charcoal text-cm-cream rounded-lg font-mono text-sm overflow-x-auto">
{`{
  "mcpServers": {
    "collective-memory": {
      "command": "python",
      "args": ["-m", "cm_mcp.server"],
      "cwd": "/path/to/collective-memory",
      "env": {
        "CM_API_URL": "http://localhost:5001",
        "CM_PAT": "${pat}"
      }
    }
  }
}`}
          </pre>
          <p className="text-xs text-cm-coffee mt-2">
            Replace <code className="bg-cm-sand/50 px-1 rounded">/path/to/collective-memory</code> with the actual path to your local repository.
          </p>
        </section>

        {/* Available Tools */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Available MCP Tools</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Once connected, you'll have access to 45+ tools including:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {[
              'identify', 'search_entities', 'create_entity', 'get_context',
              'send_message', 'get_messages', 'start_session', 'record_milestone',
              'sync_repository', 'list_personas', 'chat_with_persona'
            ].map((tool) => (
              <div key={tool} className="px-3 py-2 bg-cm-sand/50 rounded text-sm font-mono text-cm-charcoal">
                {tool}
              </div>
            ))}
          </div>
          <p className="text-xs text-cm-coffee mt-3">
            Tools are prefixed with <code className="bg-cm-sand/50 px-1 rounded">mcp__collective-memory__</code> in Claude Code.
          </p>
        </section>

        {/* Troubleshooting */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Troubleshooting</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Server not connecting?</h3>
              <p className="text-sm text-cm-coffee">
                Make sure Python 3.10+ is installed and <code className="bg-cm-sand/50 px-1 rounded">uvx</code> is available.
                You can install it with <code className="bg-cm-sand/50 px-1 rounded">pip install uv</code>.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Authentication errors?</h3>
              <p className="text-sm text-cm-coffee">
                Verify your PAT is correct in <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link>.
                You may need to regenerate it if it has expired.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-cm-charcoal mb-1">Tools not appearing?</h3>
              <p className="text-sm text-cm-coffee">
                Try restarting Claude Code completely. Check the Claude Code logs for any error messages.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
