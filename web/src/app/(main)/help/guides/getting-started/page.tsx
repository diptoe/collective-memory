'use client';

import Link from 'next/link';
import { ArrowLeft, Rocket, CheckCircle, Copy, ArrowRight, AlertCircle, Key, Settings, Search, Plus } from 'lucide-react';
import { useState } from 'react';

export default function GettingStartedGuidePage() {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(id);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const sseConfig = `{
  "mcpServers": {
    "collective-memory": {
      "serverUrl": "https://cm-mcp-sse.diptoe.com/sse?pat=YOUR_PAT_HERE"
    }
  }
}`;

  return (
    <div className="h-full overflow-auto bg-cm-cream">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/help/guides"
            className="inline-flex items-center gap-2 text-sm text-cm-coffee hover:text-cm-terracotta transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Guides
          </Link>
        </div>

        {/* Page Title */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-cm-success/10 rounded-xl">
            <Rocket className="w-8 h-8 text-cm-success" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">Getting Started</h1>
            <p className="text-cm-coffee">Your first steps with Collective Memory</p>
          </div>
        </div>

        {/* Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <p className="text-sm text-cm-coffee mb-4">
            This guide will walk you through setting up Collective Memory with your AI coding assistant.
            By the end, you&apos;ll have created your first knowledge entries and started tracking your work.
          </p>
          <div className="flex flex-wrap gap-4 text-xs text-cm-coffee">
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              Beginner friendly
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              ~10 minutes
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              No coding required
            </span>
          </div>
        </section>

        {/* Prerequisites */}
        <section className="bg-cm-amber/10 border border-cm-amber/30 rounded-xl p-6 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-cm-amber flex-shrink-0 mt-0.5" />
            <div>
              <h2 className="font-semibold text-cm-charcoal mb-2">Prerequisites</h2>
              <ul className="text-sm text-cm-coffee space-y-1">
                <li>An MCP-compatible AI client (Claude Code, Cursor, Windsurf, etc.)</li>
                <li>A Collective Memory account (sign up at the web UI)</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Step 1 */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center font-bold">
              1
            </span>
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-cm-terracotta" />
              <h2 className="text-lg font-semibold text-cm-charcoal">Create a Personal Access Token</h2>
            </div>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Your PAT (Personal Access Token) authenticates your AI client with Collective Memory.
            </p>
            <ol className="list-decimal list-inside space-y-2 ml-2">
              <li>Open the Collective Memory web UI</li>
              <li>Go to <strong>Profile → Access Tokens</strong></li>
              <li>Click <strong>Create Token</strong></li>
              <li>Give it a descriptive name (e.g., &quot;Claude Code - MacBook&quot;)</li>
              <li>Copy the generated token - you won&apos;t see it again!</li>
            </ol>
            <div className="p-3 bg-cm-sand/50 rounded-lg">
              <p className="text-xs text-cm-coffee/80">
                <strong>Tip:</strong> Create separate tokens for each device or client. This lets you
                revoke access to specific clients without affecting others.
              </p>
            </div>
          </div>
        </section>

        {/* Step 2 */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center font-bold">
              2
            </span>
            <div className="flex items-center gap-2">
              <Settings className="w-5 h-5 text-cm-terracotta" />
              <h2 className="text-lg font-semibold text-cm-charcoal">Configure Your AI Client</h2>
            </div>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Add Collective Memory as an MCP server in your AI client&apos;s configuration.
              Here&apos;s the SSE configuration (recommended):
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
              {copiedCode === 'sse' && (
                <span className="absolute top-2 right-12 text-xs text-cm-success bg-cm-charcoal px-2 py-1 rounded">
                  Copied!
                </span>
              )}
            </div>
            <p className="text-xs text-cm-coffee/80">
              Replace <code className="bg-cm-sand px-1 rounded">YOUR_PAT_HERE</code> with the token
              you created in Step 1.
            </p>
            <div className="flex gap-2">
              <Link
                href="/help/claude-code"
                className="text-xs text-cm-terracotta hover:underline"
              >
                Claude Code setup →
              </Link>
              <Link
                href="/help/cursor"
                className="text-xs text-cm-terracotta hover:underline"
              >
                Cursor setup →
              </Link>
              <Link
                href="/help/windsurf"
                className="text-xs text-cm-terracotta hover:underline"
              >
                Windsurf setup →
              </Link>
            </div>
          </div>
        </section>

        {/* Step 3 */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center font-bold">
              3
            </span>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-cm-terracotta" />
              <h2 className="text-lg font-semibold text-cm-charcoal">Identify with Collective Memory</h2>
            </div>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              The first thing your AI client should do is identify itself. This registers the agent
              and enables tracking.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">&quot;Please identify yourself with Collective Memory&quot;</p>
            </div>
            <p>
              The AI will call the <code className="bg-cm-sand px-1 rounded">identify</code> tool,
              which registers it with CM and sets up its session state.
            </p>
            <div className="p-3 bg-cm-success/10 border border-cm-success/30 rounded-lg">
              <p className="text-xs">
                <strong>Success indicator:</strong> The AI will confirm it&apos;s identified and may
                mention its agent name (a memorable word combination like &quot;swift-bold-keen-lion&quot;).
              </p>
            </div>
          </div>
        </section>

        {/* Step 4 */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center font-bold">
              4
            </span>
            <div className="flex items-center gap-2">
              <Search className="w-5 h-5 text-cm-terracotta" />
              <h2 className="text-lg font-semibold text-cm-charcoal">Search Existing Knowledge</h2>
            </div>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Before creating new knowledge, check what already exists. This helps avoid duplicates
              and builds on existing context.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">&quot;Search Collective Memory for entities about authentication&quot;</p>
            </div>
            <p>
              The AI will use <code className="bg-cm-sand px-1 rounded">search_entities</code> to
              find relevant knowledge. Results include entity names, types, and summaries.
            </p>
          </div>
        </section>

        {/* Step 5 */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center font-bold">
              5
            </span>
            <div className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-cm-terracotta" />
              <h2 className="text-lg font-semibold text-cm-charcoal">Create Your First Entity</h2>
            </div>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Create a knowledge entry to capture something you&apos;ve learned or decided.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">
                &quot;Create an entity in Collective Memory documenting that we use JWT tokens for API
                authentication, stored in httpOnly cookies&quot;
              </p>
            </div>
            <p>
              The AI will create an entity with an appropriate type (e.g., &quot;Decision&quot;, &quot;Concept&quot;,
              or &quot;Implementation&quot;) and a summary of the information.
            </p>
            <div className="p-3 bg-cm-info/10 border border-cm-info/30 rounded-lg">
              <p className="text-xs">
                <strong>Entity types:</strong> Concept, Decision, Implementation, Bug, Feature, Person,
                Team, Project, and more. The AI will choose an appropriate type based on context.
              </p>
            </div>
          </div>
        </section>

        {/* What's Next */}
        <section className="bg-cm-success/10 border border-cm-success/30 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">What&apos;s Next?</h2>
          <div className="space-y-3">
            <p className="text-sm text-cm-coffee">
              Now that you&apos;re set up, explore these features:
            </p>
            <div className="grid md:grid-cols-2 gap-3">
              <Link
                href="/help/guides/sessions"
                className="flex items-center justify-between p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
              >
                <div>
                  <p className="font-medium text-cm-charcoal text-sm">Work Sessions</p>
                  <p className="text-xs text-cm-coffee">Track focused work periods</p>
                </div>
                <ArrowRight className="w-4 h-4 text-cm-coffee/50" />
              </Link>
              <Link
                href="/help/guides/personas"
                className="flex items-center justify-between p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
              >
                <div>
                  <p className="font-medium text-cm-charcoal text-sm">Using Personas</p>
                  <p className="text-xs text-cm-coffee">Chat with specialized AI personas</p>
                </div>
                <ArrowRight className="w-4 h-4 text-cm-coffee/50" />
              </Link>
            </div>
          </div>
        </section>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <Link
            href="/help/guides"
            className="text-sm text-cm-terracotta hover:underline"
          >
            ← All Guides
          </Link>
          <Link
            href="/help/guides/sessions"
            className="text-sm text-cm-terracotta hover:underline"
          >
            Work Sessions →
          </Link>
        </div>
      </div>
    </div>
  );
}
