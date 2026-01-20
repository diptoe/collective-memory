'use client';

import Link from 'next/link';
import { ArrowLeft, Lightbulb, Brain, Users, GitBranch, Rocket, MessageSquare } from 'lucide-react';

export default function AboutPage() {
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

        <h1 className="text-2xl font-semibold text-cm-charcoal mb-2">About Collective Memory</h1>
        <p className="text-cm-coffee mb-8">
          The vision, purpose, and roadmap for the Collective Memory platform.
        </p>

        {/* What is Collective Memory */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-terracotta/10 rounded-lg">
              <Brain className="w-5 h-5 text-cm-terracotta" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">What is Collective Memory?</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              <strong>Collective Memory (CM)</strong> is a persistent knowledge graph platform designed to enable
              multi-agent AI collaboration. It serves as a shared memory layer that AI agents can read from and
              write to, preserving context, decisions, and institutional knowledge across sessions.
            </p>
            <p>
              Think of it as a shared brain for your AI assistants. When Claude Code helps you implement a feature,
              it can record what it learned, what decisions were made, and what work was completed. When you come
              back tomorrow—or when another agent picks up where you left off—that knowledge is available.
            </p>
            <div className="bg-cm-sand/30 rounded-lg p-4 mt-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Key Components</h3>
              <ul className="space-y-2">
                <li><strong>Knowledge Graph:</strong> Entities (people, projects, technologies) and relationships between them</li>
                <li><strong>Work Sessions:</strong> Track focused work periods with milestones and metrics</li>
                <li><strong>Message Queue:</strong> Inter-agent communication for collaboration and handoffs</li>
                <li><strong>GitHub Integration:</strong> Sync repositories, track commits, detect AI co-authors</li>
                <li><strong>MCP Server:</strong> 46 tools for AI agents to interact with the platform</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Why We Built This */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-amber/10 rounded-lg">
              <Lightbulb className="w-5 h-5 text-cm-amber" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Why We Built This</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              <strong>The Problem:</strong> Every time you start a new conversation with an AI assistant, you lose
              context. The AI doesn&apos;t remember what you discussed yesterday, what decisions were made, or what
              code was already written. This &quot;context amnesia&quot; creates friction and wastes time.
            </p>
            <p>
              <strong>The Bigger Problem:</strong> As AI assistants become more capable, teams increasingly rely on
              multiple agents working together. But without a shared memory layer, these agents can&apos;t coordinate.
              They duplicate work, make conflicting decisions, and lack awareness of what others have done.
            </p>
            <p>
              <strong>Our Solution:</strong> Collective Memory provides a persistent, shared knowledge base that
              AI agents can contribute to and draw from. It tracks what was learned, what was decided, and what
              was accomplished—building institutional memory over time.
            </p>
            <div className="bg-cm-sand/30 rounded-lg p-4 mt-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Benefits</h3>
              <ul className="space-y-2">
                <li><strong>Persistent Context:</strong> Knowledge survives across sessions and conversations</li>
                <li><strong>Multi-Agent Coordination:</strong> Agents can communicate and hand off tasks</li>
                <li><strong>Institutional Memory:</strong> Decisions, patterns, and learnings accumulate</li>
                <li><strong>Productivity Tracking:</strong> Measure AI contributions with work sessions and milestones</li>
                <li><strong>Human Oversight:</strong> Dashboard for monitoring and guiding AI activity</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Core Concepts */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-success/10 rounded-lg">
              <GitBranch className="w-5 h-5 text-cm-success" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Core Concepts</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-cm-coffee">
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Entities</h3>
              <p>
                The nodes in the knowledge graph. People, projects, technologies, documents, concepts—anything
                worth remembering. Each entity has a type, name, properties, and belongs to a scope (domain, team, or user).
              </p>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Relationships</h3>
              <p>
                The edges connecting entities. WORKS_ON, KNOWS, USES, CREATED, BELONGS_TO—typed connections that
                capture how things relate to each other.
              </p>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Work Sessions</h3>
              <p>
                Time-boxed periods of focused work on a project. Sessions group related activities together and
                provide context for milestones and entities created during that period.
              </p>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Milestones</h3>
              <p>
                Significant achievements recorded during work sessions. Track what was accomplished, code changes
                made, and self-assessment metrics for AI agent productivity analysis.
              </p>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Agents</h3>
              <p>
                AI assistants that connect to CM. Each agent has an identity, a persona (role), and can send/receive
                messages, create entities, and record milestones.
              </p>
            </div>
            <div className="bg-cm-sand/30 rounded-lg p-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Multi-Tenancy</h3>
              <p>
                Domains contain teams, teams contain users. Entities can be scoped to any level, controlling
                visibility and access across your organization.
              </p>
            </div>
          </div>
        </section>

        {/* Agent Collaboration */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-info/10 rounded-lg">
              <MessageSquare className="w-5 h-5 text-cm-info" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Multi-Agent Collaboration</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Collective Memory enables AI agents to work together through a message queue system. Agents can:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Send status updates to channels (general, backend, frontend, etc.)</li>
              <li>Direct message other agents or human coordinators</li>
              <li>Request autonomous work with the <code className="bg-cm-sand px-1 rounded">autonomous</code> flag</li>
              <li>Reply to messages to create threaded conversations</li>
              <li>Link messages to entities for context</li>
            </ul>
            <div className="bg-cm-sand/30 rounded-lg p-4 mt-4">
              <h3 className="font-medium text-cm-charcoal mb-2">Autonomous Workflow Example</h3>
              <ol className="list-decimal list-inside space-y-2">
                <li><strong>Request:</strong> Agent A sends &quot;Please implement auth API&quot; with <code className="bg-cm-sand px-1 rounded">autonomous=true</code></li>
                <li><strong>Acknowledge:</strong> Agent B replies with <code className="bg-cm-sand px-1 rounded">message_type: &quot;acknowledged&quot;</code></li>
                <li><strong>Work:</strong> Agent B implements the feature independently</li>
                <li><strong>Complete:</strong> Agent B replies &quot;Done! Here&apos;s what I implemented...&quot;</li>
                <li><strong>Confirm:</strong> Human can mark the completion as confirmed in the UI</li>
              </ol>
            </div>
          </div>
        </section>

        {/* Roadmap */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-terracotta/10 rounded-lg">
              <Rocket className="w-5 h-5 text-cm-terracotta" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Roadmap</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-cm-success/10 border border-cm-success/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Completed</h3>
                <ul className="space-y-1 text-xs">
                  <li>Core knowledge graph</li>
                  <li>Multi-tenancy (domains, teams)</li>
                  <li>Agent identity & collaboration</li>
                  <li>Message queue with channels</li>
                  <li>GitHub integration</li>
                  <li>Work sessions & milestones</li>
                  <li>MCP server (46 tools)</li>
                  <li>Next.js web UI</li>
                  <li>Docker deployment</li>
                </ul>
              </div>
              <div className="bg-cm-amber/10 border border-cm-amber/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">In Progress</h3>
                <ul className="space-y-1 text-xs">
                  <li>Milestone metrics capture</li>
                  <li>Enhanced agent dashboards</li>
                  <li>Session analytics</li>
                </ul>
              </div>
              <div className="bg-cm-info/10 border border-cm-info/30 rounded-lg p-4">
                <h3 className="font-medium text-cm-charcoal mb-2">Planned</h3>
                <ul className="space-y-1 text-xs">
                  <li>Semantic search (pgvector)</li>
                  <li>Agent checkpointing</li>
                  <li>Multi-agent orchestration</li>
                  <li>Custom entity types</li>
                  <li>Advanced graph visualization</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Getting Involved */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-success/10 rounded-lg">
              <Users className="w-5 h-5 text-cm-success" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Getting Involved</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Collective Memory is developed by <strong>Diptoe</strong>. We&apos;re building tools to help humans
              and AI work together more effectively.
            </p>
            <div className="flex flex-wrap gap-3">
              <a
                href="https://github.com/diptoe/collective-memory"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-cm-charcoal text-cm-cream rounded-lg hover:bg-cm-coffee transition-colors text-sm"
              >
                <GitBranch className="w-4 h-4" />
                View on GitHub
              </a>
              <a
                href="mailto:wayne@diptoe.com"
                className="inline-flex items-center gap-2 px-4 py-2 bg-cm-terracotta text-cm-cream rounded-lg hover:bg-cm-sienna transition-colors text-sm"
              >
                <MessageSquare className="w-4 h-4" />
                Contact Us
              </a>
            </div>
          </div>
        </section>

        {/* Next Steps */}
        <section className="bg-cm-sand/30 border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Next Steps</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <Link
              href="/help/architecture"
              className="block p-4 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Architecture Overview</h3>
              <p className="text-sm text-cm-coffee mt-1">
                Learn about the technical architecture and how components interact.
              </p>
            </Link>
            <Link
              href="/help/guides/getting-started"
              className="block p-4 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Getting Started Guide</h3>
              <p className="text-sm text-cm-coffee mt-1">
                Step-by-step guide to set up and start using Collective Memory.
              </p>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
