'use client';

import Link from 'next/link';

export default function HelpPage() {
  return (
    <div className="h-full overflow-auto bg-cm-cream">
      <div className="p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal mb-2">
            Help & Documentation
          </h1>
          <p className="text-cm-coffee">
            Learn about Collective Memory, explore tools, and configure your AI clients
          </p>
        </div>

        {/* About Blurb */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <p className="text-cm-coffee">
            <strong className="text-cm-charcoal">Collective Memory</strong> is a persistent knowledge graph
            platform that enables AI agents to build and share knowledge across sessions. Connect your
            AI coding assistant (Claude Code, Cursor, Windsurf, etc.) via MCP to give it persistent memory,
            multi-agent collaboration, and structured knowledge management.
          </p>
        </section>

        {/* Documentation Tiles */}
        <section className="grid md:grid-cols-2 gap-4 mb-6">
          <Link
            href="/help/about"
            className="bg-cm-ivory border border-cm-sand rounded-xl p-5 hover:border-cm-terracotta transition-colors group"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">🎯</span>
              <h3 className="font-semibold text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                About CM
              </h3>
            </div>
            <p className="text-sm text-cm-coffee">
              Vision, core concepts, and roadmap for Collective Memory.
            </p>
          </Link>
          <Link
            href="/help/guides"
            className="bg-cm-ivory border border-cm-sand rounded-xl p-5 hover:border-cm-terracotta transition-colors group"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">📖</span>
              <h3 className="font-semibold text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                Guides & Tutorials
              </h3>
            </div>
            <p className="text-sm text-cm-coffee">
              Step-by-step tutorials for sessions, personas, and collaboration.
            </p>
          </Link>
          <Link
            href="/help/tools"
            className="bg-cm-ivory border border-cm-sand rounded-xl p-5 hover:border-cm-terracotta transition-colors group"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">🔧</span>
              <h3 className="font-semibold text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                Tool Reference
              </h3>
            </div>
            <p className="text-sm text-cm-coffee">
              Complete documentation for all 46 MCP tools.
            </p>
          </Link>
          <Link
            href="/help/setup"
            className="bg-cm-ivory border border-cm-sand rounded-xl p-5 hover:border-cm-terracotta transition-colors group"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">⚙️</span>
              <h3 className="font-semibold text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                Client Setup
              </h3>
            </div>
            <p className="text-sm text-cm-coffee">
              Configure Claude Code, Cursor, Windsurf, and other AI clients.
            </p>
          </Link>
        </section>

        {/* Quick Start */}
        <section className="bg-cm-terracotta/10 border border-cm-terracotta/30 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-3">Quick Start</h2>
          <p className="text-sm text-cm-coffee mb-4">
            Get connected in 3 steps:
          </p>
          <ol className="list-decimal list-inside space-y-2 text-sm text-cm-charcoal mb-4">
            <li>Get your Personal Access Token from <Link href="/settings" className="text-cm-terracotta hover:underline">Settings</Link></li>
            <li>Add the MCP configuration to your AI client</li>
            <li>Ask your AI to &quot;identify with Collective Memory&quot;</li>
          </ol>
          <Link
            href="/help/setup"
            className="inline-flex items-center gap-2 px-4 py-2 bg-cm-terracotta text-cm-cream text-sm rounded-lg hover:bg-cm-terracotta/90 transition-colors"
          >
            View Setup Guide
            <span>→</span>
          </Link>
        </section>

        {/* Additional Resources */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Additional Resources</h2>
          <ul className="space-y-3">
            <li>
              <Link
                href="/help/architecture"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🏗️</span>
                <span>System Architecture & Technical Overview</span>
              </Link>
            </li>
            <li>
              <Link
                href="/settings"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🔑</span>
                <span>Manage your Personal Access Token</span>
              </Link>
            </li>
            <li>
              <Link
                href="/help/sse"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🌐</span>
                <span>SSE Transport Details & Self-Hosting</span>
              </Link>
            </li>
            <li>
              <a
                href="https://github.com/diptoe/collective-memory"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>📚</span>
                <span>GitHub Repository & Documentation</span>
              </a>
            </li>
            <li>
              <a
                href="https://modelcontextprotocol.io/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-cm-coffee hover:text-cm-terracotta transition-colors"
              >
                <span>🔗</span>
                <span>MCP Protocol Documentation</span>
              </a>
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
