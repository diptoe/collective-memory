'use client';

import Link from 'next/link';
import { ArrowLeft, Clock, CheckCircle, Play, Square, Flag, BarChart3, ArrowRight, Lightbulb } from 'lucide-react';

export default function SessionsGuidePage() {
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
          <div className="p-3 bg-cm-amber/10 rounded-xl">
            <Clock className="w-8 h-8 text-cm-amber" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">Work Sessions</h1>
            <p className="text-cm-coffee">Track focused work periods and milestones</p>
          </div>
        </div>

        {/* Overview */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <p className="text-sm text-cm-coffee mb-4">
            Work sessions help you track focused periods of work, recording what was accomplished
            and measuring productivity over time. Sessions are the foundation of CM&apos;s productivity tracking.
          </p>
          <div className="flex flex-wrap gap-4 text-xs text-cm-coffee">
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              Beginner friendly
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4 text-cm-success" />
              ~8 minutes
            </span>
          </div>
        </section>

        {/* What Are Sessions */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">What Are Work Sessions?</h2>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              A work session represents a focused period of work on a specific task or project.
              Sessions track:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-2">
              <li><strong>Duration:</strong> How long you worked</li>
              <li><strong>Milestones:</strong> What was accomplished</li>
              <li><strong>Context:</strong> Related entities and projects</li>
              <li><strong>Metrics:</strong> Tool calls, files changed, self-assessment</li>
            </ul>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="text-xs text-cm-coffee/80">
                <strong>Why track sessions?</strong> Sessions create a historical record of AI agent
                productivity, helping you understand work patterns, identify bottlenecks, and measure
                collaboration quality over time.
              </p>
            </div>
          </div>
        </section>

        {/* Starting a Session */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-success/10 rounded-lg">
              <Play className="w-5 h-5 text-cm-success" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Starting a Session</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Start a session when beginning focused work on a specific task.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">
                &quot;Start a work session for implementing the user authentication feature&quot;
              </p>
            </div>
            <p>
              The AI will call <code className="bg-cm-sand px-1 rounded">start_session</code> with:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li><strong>Goal:</strong> What you&apos;re trying to accomplish</li>
              <li><strong>Project:</strong> Optional project association</li>
              <li><strong>Context:</strong> Relevant entities to link</li>
            </ul>
            <div className="p-3 bg-cm-info/10 border border-cm-info/30 rounded-lg text-xs">
              <strong>Tip:</strong> You can only have one active session at a time. If you already
              have an active session, you&apos;ll need to end it first or extend it with a new goal.
            </div>
          </div>
        </section>

        {/* Recording Milestones */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-terracotta/10 rounded-lg">
              <Flag className="w-5 h-5 text-cm-terracotta" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Recording Milestones</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              Milestones mark significant accomplishments within a session. Record them when you
              complete a meaningful chunk of work.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">
                &quot;Record a milestone: completed the login form component with validation&quot;
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-3 mt-4">
              <div className="p-3 bg-cm-success/10 border border-cm-success/30 rounded-lg">
                <p className="font-medium text-cm-charcoal text-xs mb-1">Started</p>
                <p className="text-xs text-cm-coffee">Beginning a major task</p>
              </div>
              <div className="p-3 bg-cm-success/10 border border-cm-success/30 rounded-lg">
                <p className="font-medium text-cm-charcoal text-xs mb-1">Completed</p>
                <p className="text-xs text-cm-coffee">Finished a feature or fix</p>
              </div>
              <div className="p-3 bg-cm-amber/10 border border-cm-amber/30 rounded-lg">
                <p className="font-medium text-cm-charcoal text-xs mb-1">Blocked</p>
                <p className="text-xs text-cm-coffee">Hit an obstacle or blocker</p>
              </div>
            </div>
          </div>
        </section>

        {/* Self-Assessment */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-info/10 rounded-lg">
              <BarChart3 className="w-5 h-5 text-cm-info" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Self-Assessment Metrics</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              When recording completed milestones, AI agents can include self-assessment metrics
              (1-5 scale) to provide insight into the work quality:
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-cm-sand">
                    <th className="text-left py-2 pr-4 font-medium text-cm-charcoal">Metric</th>
                    <th className="text-left py-2 font-medium text-cm-charcoal">Description</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-cm-sand/50">
                    <td className="py-2 pr-4 font-mono">human_guidance_level</td>
                    <td className="py-2 text-cm-coffee">1 = fully autonomous, 5 = heavy guidance needed</td>
                  </tr>
                  <tr className="border-b border-cm-sand/50">
                    <td className="py-2 pr-4 font-mono">model_understanding</td>
                    <td className="py-2 text-cm-coffee">1 = low understanding, 5 = high understanding</td>
                  </tr>
                  <tr className="border-b border-cm-sand/50">
                    <td className="py-2 pr-4 font-mono">model_accuracy</td>
                    <td className="py-2 text-cm-coffee">1 = many errors, 5 = very accurate</td>
                  </tr>
                  <tr className="border-b border-cm-sand/50">
                    <td className="py-2 pr-4 font-mono">collaboration_rating</td>
                    <td className="py-2 text-cm-coffee">1 = poor collaboration, 5 = excellent</td>
                  </tr>
                  <tr>
                    <td className="py-2 pr-4 font-mono">complexity_rating</td>
                    <td className="py-2 text-cm-coffee">1 = trivial task, 5 = very complex</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Ending a Session */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cm-error/10 rounded-lg">
              <Square className="w-5 h-5 text-cm-error" />
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Ending a Session</h2>
          </div>
          <div className="space-y-4 text-sm text-cm-coffee">
            <p>
              End a session when you&apos;ve finished your focused work period. This saves the session
              record with all milestones and metrics.
            </p>
            <div className="p-4 bg-cm-sand/30 rounded-lg">
              <p className="font-medium text-cm-charcoal mb-2">Ask your AI:</p>
              <p className="italic">
                &quot;End the current session - we completed the authentication feature&quot;
              </p>
            </div>
            <p>
              You can provide a summary of what was accomplished and any notes for future reference.
            </p>
          </div>
        </section>

        {/* Best Practices */}
        <section className="bg-cm-amber/10 border border-cm-amber/30 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-cm-amber" />
            <h2 className="text-lg font-semibold text-cm-charcoal">Best Practices</h2>
          </div>
          <div className="space-y-3 text-sm text-cm-coffee">
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-amber text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <div>
                <p className="font-medium text-cm-charcoal">Start sessions with clear goals</p>
                <p className="text-xs">Define what &quot;done&quot; looks like before starting.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-amber text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <div>
                <p className="font-medium text-cm-charcoal">Record milestones frequently</p>
                <p className="text-xs">Don&apos;t wait until the end - capture progress as you go.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-amber text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <div>
                <p className="font-medium text-cm-charcoal">Record before committing</p>
                <p className="text-xs">Record a milestone before making a git commit to ensure work is tracked.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-cm-amber text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">4</span>
              <div>
                <p className="font-medium text-cm-charcoal">Include honest self-assessment</p>
                <p className="text-xs">Accurate metrics help identify patterns and areas for improvement.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Related Tools */}
        <section className="bg-cm-sand/30 border border-cm-sand rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Related Tools</h2>
          <div className="grid md:grid-cols-2 gap-3">
            <Link
              href="/help/tools/start_session"
              className="p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <code className="text-sm font-medium text-cm-charcoal">start_session</code>
              <p className="text-xs text-cm-coffee mt-1">Begin a new work session</p>
            </Link>
            <Link
              href="/help/tools/end_session"
              className="p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <code className="text-sm font-medium text-cm-charcoal">end_session</code>
              <p className="text-xs text-cm-coffee mt-1">Complete the current session</p>
            </Link>
            <Link
              href="/help/tools/record_milestone"
              className="p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <code className="text-sm font-medium text-cm-charcoal">record_milestone</code>
              <p className="text-xs text-cm-coffee mt-1">Record an accomplishment</p>
            </Link>
            <Link
              href="/help/tools/get_active_session"
              className="p-3 bg-cm-ivory border border-cm-sand rounded-lg hover:border-cm-terracotta transition-colors"
            >
              <code className="text-sm font-medium text-cm-charcoal">get_active_session</code>
              <p className="text-xs text-cm-coffee mt-1">Check current session status</p>
            </Link>
          </div>
        </section>

        {/* What's Next */}
        <section className="bg-cm-success/10 border border-cm-success/30 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">What&apos;s Next?</h2>
          <div className="grid md:grid-cols-2 gap-3">
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
          </div>
        </section>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <Link
            href="/help/guides/getting-started"
            className="text-sm text-cm-terracotta hover:underline"
          >
            ← Getting Started
          </Link>
          <Link
            href="/help/guides/personas"
            className="text-sm text-cm-terracotta hover:underline"
          >
            Using Personas →
          </Link>
        </div>
      </div>
    </div>
  );
}
