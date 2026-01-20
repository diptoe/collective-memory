'use client';

import Link from 'next/link';
import { ArrowLeft, Users, CheckCircle, MessageCircle, Sparkles, ArrowRight, Lightbulb } from 'lucide-react';

export default function PersonasGuidePage() {
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
          <div className="p-3 bg-purple-100 rounded-xl">
            <Users className="w-8 h-8 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">Using Personas</h1>
            <p className="text-cm-coffee">Interact with specialized AI personas</p>
          </div>
        </div>

        {/* Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <p className="text-sm text-cm-coffee mb-4">
            Personas are AI characters with specialized knowledge and communication styles.
            They provide an alternative way to interact with the knowledge in Collective Memory,
            each bringing their own perspective and expertise.
          </p>
          <div className="flex flex-wrap gap-4 text-xs text-cm-coffee">
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              Intermediate
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              ~6 minutes
            </span>
          </div>
        </section>

        {/* What Are Personas */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">What Are Personas?</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Personas are AI-powered characters that have access to the knowledge graph but
              respond with their own unique style and perspective. Each persona has:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-2">
              <li><strong>Name and Avatar:</strong> A distinct identity (e.g., &quot;Max&quot;, &quot;Luna&quot;)</li>
              <li><strong>Specialty:</strong> Area of expertise (architecture, debugging, etc.)</li>
              <li><strong>Communication Style:</strong> How they phrase responses</li>
              <li><strong>Background:</strong> Context that shapes their perspective</li>
            </ul>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="text-xs text-cm-coffee/80">
                <strong>Example:</strong> A &quot;Senior Architect&quot; persona might focus on system design
                and scalability, while a &quot;Security Expert&quot; persona emphasizes vulnerabilities and
                best practices. Same knowledge, different perspectives.
              </p>
            </div>
          </div>
        </section>

        {/* Listing Personas */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Discovering Available Personas</h2>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Start by seeing what personas are available in your team or domain.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">&quot;List the available personas in Collective Memory&quot;</p>
            </div>
            <p>
              The AI will call <code className="bg-cm-sand px-1 rounded">list_personas</code> and
              show you each persona&apos;s name, specialty, and a brief description.
            </p>
          </div>
        </section>

        {/* Chatting with Personas */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-terracotta/10 rounded-lg">
              <MessageCircle className="w-5 h-5 text-cm-terracotta" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Chatting with a Persona</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Once you&apos;ve found a persona you want to interact with, start a conversation.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">
                &quot;Chat with the Security Expert persona: What authentication vulnerabilities
                should I watch out for in our API?&quot;
              </p>
            </div>
            <p>
              The AI will call <code className="bg-cm-sand px-1 rounded">chat_with_persona</code>,
              passing your message. The persona will:
            </p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Search the knowledge graph for relevant information</li>
              <li>Formulate a response in their unique style</li>
              <li>Reference specific entities when applicable</li>
            </ol>
            <div className="p-3 bg-cm-info/10 border border-cm-info/30 rounded-lg text-xs">
              <strong>Note:</strong> Persona responses are generated using the AI model and
              filtered through the persona&apos;s defined characteristics. They have access to all
              knowledge in your scope but interpret it through their expertise lens.
            </div>
          </div>
        </section>

        {/* Example Personas */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Example Personas</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">M</span>
                </div>
                <div>
                  <p className="font-medium text-cm-charcoal">Max</p>
                  <p className="text-xs text-cm-coffee">Systems Architect</p>
                </div>
              </div>
              <p className="text-xs text-cm-coffee">
                Focuses on system design, scalability, and architectural patterns.
                Provides strategic technical guidance.
              </p>
            </div>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-bold text-sm">L</span>
                </div>
                <div>
                  <p className="font-medium text-cm-charcoal">Luna</p>
                  <p className="text-xs text-cm-coffee">Code Quality Expert</p>
                </div>
              </div>
              <p className="text-xs text-cm-coffee">
                Emphasizes clean code, testing, and maintainability.
                Helpful for code reviews and refactoring.
              </p>
            </div>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-red-600 font-bold text-sm">S</span>
                </div>
                <div>
                  <p className="font-medium text-cm-charcoal">Sam</p>
                  <p className="text-xs text-cm-coffee">Security Specialist</p>
                </div>
              </div>
              <p className="text-xs text-cm-coffee">
                Identifies vulnerabilities and security concerns.
                Recommends secure coding practices.
              </p>
            </div>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 font-bold text-sm">D</span>
                </div>
                <div>
                  <p className="font-medium text-cm-charcoal">Devon</p>
                  <p className="text-xs text-cm-coffee">DevOps Engineer</p>
                </div>
              </div>
              <p className="text-xs text-cm-coffee">
                Handles deployment, CI/CD, and infrastructure concerns.
                Practical operational focus.
              </p>
            </div>
          </div>
          <p className="text-xs text-cm-coffee/80 mt-4 italic">
            These are examples - your team may have different personas configured.
          </p>
        </section>

        {/* When to Use Personas */}
        <section className="bg-cm-amber/10 border border-cm-amber/30 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-cm-amber" />
            <h2 className="text-lg font-semibold text-cm-charcoal">When to Use Personas</h2>
          </div>
          <div className="space-y-3 text-sm text-cm-coffee">
            <div className="flex gap-3">
              <span className="text-cm-success">✓</span>
              <div>
                <p className="font-medium text-cm-charcoal">Getting a specialized perspective</p>
                <p className="text-xs">When you need expert-level insight on a specific topic.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-cm-success">✓</span>
              <div>
                <p className="font-medium text-cm-charcoal">Code reviews and feedback</p>
                <p className="text-xs">Ask a Quality Expert persona to review your implementation.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-cm-success">✓</span>
              <div>
                <p className="font-medium text-cm-charcoal">Security audits</p>
                <p className="text-xs">Have a Security persona analyze your code for vulnerabilities.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-cm-success">✓</span>
              <div>
                <p className="font-medium text-cm-charcoal">Brainstorming solutions</p>
                <p className="text-xs">Get different perspectives on architectural decisions.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Related Tools */}
        <section className="bg-cm-sand/30 border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Related Tools</h2>
          <div className="grid md:grid-cols-2 gap-3">
            <Link
              href="/help/tools/list_personas"
              className="p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <code className="text-sm font-medium text-cm-charcoal">list_personas</code>
              <p className="text-xs text-cm-coffee mt-1">See all available personas</p>
            </Link>
            <Link
              href="/help/tools/chat_with_persona"
              className="p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <code className="text-sm font-medium text-cm-charcoal">chat_with_persona</code>
              <p className="text-xs text-cm-coffee mt-1">Send a message to a persona</p>
            </Link>
          </div>
        </section>

        {/* What's Next */}
        <section className="bg-cm-success/10 border border-cm-success/30 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">What&apos;s Next?</h2>
          <div className="grid md:grid-cols-2 gap-3">
            <Link
              href="/help/guides/collaboration"
              className="flex items-center justify-between p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <div>
                <p className="font-medium text-cm-charcoal text-sm">Multi-Agent Collaboration</p>
                <p className="text-xs text-cm-coffee">Enable AI agents to work together</p>
              </div>
              <ArrowRight className="w-4 h-4 text-cm-coffee/50" />
            </Link>
            <Link
              href="/help/tools"
              className="flex items-center justify-between p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <div>
                <p className="font-medium text-cm-charcoal text-sm">Tool Reference</p>
                <p className="text-xs text-cm-coffee">Explore all 46 MCP tools</p>
              </div>
              <ArrowRight className="w-4 h-4 text-cm-coffee/50" />
            </Link>
          </div>
        </section>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <Link
            href="/help/guides/sessions"
            className="text-sm text-cm-terracotta hover:underline"
          >
            ← Work Sessions
          </Link>
          <Link
            href="/help/guides/collaboration"
            className="text-sm text-cm-terracotta hover:underline"
          >
            Collaboration →
          </Link>
        </div>
      </div>
    </div>
  );
}
