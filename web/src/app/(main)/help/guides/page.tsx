'use client';

import Link from 'next/link';
import { ArrowLeft, BookOpen, Rocket, Clock, Users, MessageSquare } from 'lucide-react';

const guides = [
  {
    title: 'Getting Started',
    description: 'Create your account, configure your AI client, and make your first knowledge entries.',
    href: '/help/guides/getting-started',
    icon: Rocket,
    difficulty: 'Beginner',
    duration: '10 min',
  },
  {
    title: 'Work Sessions',
    description: 'Track focused work periods, record milestones, and capture productivity metrics.',
    href: '/help/guides/sessions',
    icon: Clock,
    difficulty: 'Beginner',
    duration: '8 min',
  },
  {
    title: 'Using Personas',
    description: 'Interact with AI personas that have specialized knowledge and communication styles.',
    href: '/help/guides/personas',
    icon: Users,
    difficulty: 'Intermediate',
    duration: '6 min',
  },
  {
    title: 'Multi-Agent Collaboration',
    description: 'Enable AI agents to communicate, hand off tasks, and work together autonomously.',
    href: '/help/guides/collaboration',
    icon: MessageSquare,
    difficulty: 'Advanced',
    duration: '12 min',
  },
];

export default function GuidesIndexPage() {
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
          <div className="p-3 bg-cm-terracotta/10 rounded-xl">
            <BookOpen className="w-8 h-8 text-cm-terracotta" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">Guides & Tutorials</h1>
            <p className="text-cm-coffee">Learn how to get the most out of Collective Memory</p>
          </div>
        </div>

        {/* Introduction */}
        <section className="bg-cm-ivory border border-cm-sand rounded-xl p-6 mb-6">
          <p className="text-sm text-cm-coffee">
            These guides walk you through the key features of Collective Memory, from initial setup
            to advanced multi-agent workflows. Each guide is designed to be followed step-by-step,
            with practical examples you can try immediately.
          </p>
        </section>

        {/* Guides Grid */}
        <div className="grid gap-4">
          {guides.map((guide) => {
            const Icon = guide.icon;
            return (
              <Link
                key={guide.href}
                href={guide.href}
                className="block bg-cm-ivory border border-cm-sand rounded-xl p-6 hover:border-cm-terracotta transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-cm-sand/50 rounded-lg flex-shrink-0">
                    <Icon className="w-6 h-6 text-cm-terracotta" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h2 className="text-lg font-semibold text-cm-charcoal">{guide.title}</h2>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full ${
                          guide.difficulty === 'Beginner'
                            ? 'bg-cm-success/20 text-cm-success'
                            : guide.difficulty === 'Intermediate'
                            ? 'bg-cm-amber/20 text-cm-amber'
                            : 'bg-cm-terracotta/20 text-cm-terracotta'
                        }`}
                      >
                        {guide.difficulty}
                      </span>
                      <span className="text-xs text-cm-coffee/60">{guide.duration}</span>
                    </div>
                    <p className="text-sm text-cm-coffee">{guide.description}</p>
                  </div>
                  <div className="text-cm-coffee/50 text-lg">→</div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Learning Path */}
        <section className="mt-8 bg-cm-sand/30 border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Recommended Learning Path</h2>
          <div className="flex items-center gap-2 text-sm text-cm-coffee">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">
                1
              </span>
              <span>Getting Started</span>
            </div>
            <span className="text-cm-coffee/30">→</span>
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">
                2
              </span>
              <span>Work Sessions</span>
            </div>
            <span className="text-cm-coffee/30">→</span>
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">
                3
              </span>
              <span>Personas</span>
            </div>
            <span className="text-cm-coffee/30">→</span>
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 bg-cm-terracotta text-cm-cream rounded-full flex items-center justify-center text-xs font-bold">
                4
              </span>
              <span>Collaboration</span>
            </div>
          </div>
        </section>

        {/* Additional Resources */}
        <section className="mt-6 bg-cm-ivory border border-cm-sand rounded-xl p-6">
          <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Additional Resources</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <Link
              href="/help/tools"
              className="p-4 bg-cm-sand/30 rounded-lg hover:bg-cm-sand/50 transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Tool Reference</h3>
              <p className="text-xs text-cm-coffee mt-1">
                Complete documentation for all 46 MCP tools.
              </p>
            </Link>
            <Link
              href="/help/architecture"
              className="p-4 bg-cm-sand/30 rounded-lg hover:bg-cm-sand/50 transition-colors"
            >
              <h3 className="font-medium text-cm-charcoal">Architecture</h3>
              <p className="text-xs text-cm-coffee mt-1">
                Understand how CM works under the hood.
              </p>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
