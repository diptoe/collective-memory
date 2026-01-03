'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Stats {
  entities: number;
  relationships: number;
  personas: number;
  conversations: number;
  agents: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const [entitiesRes, personasRes, agentsRes, conversationsRes] = await Promise.all([
          api.entities.list(),
          api.personas.list(),
          api.agents.list(),
          api.conversations.list(),
        ]);

        setStats({
          entities: entitiesRes.data?.entities?.length || 0,
          relationships: 0,
          personas: personasRes.data?.personas?.length || 0,
          conversations: conversationsRes.data?.conversations?.length || 0,
          agents: agentsRes.data?.agents?.length || 0,
        });
      } catch (err) {
        setError('Failed to load dashboard stats');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, []);

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-serif font-semibold text-cm-charcoal">
          Dashboard
        </h1>
        <p className="text-cm-coffee mt-2">
          Welcome to Collective Memory - your multi-agent collaboration platform
        </p>
      </header>

      {loading ? (
        <div className="text-cm-coffee">Loading...</div>
      ) : error ? (
        <div className="text-cm-error">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Entities"
            value={stats?.entities || 0}
            icon="🗄️"
            href="/entities"
          />
          <StatCard
            title="Personas"
            value={stats?.personas || 0}
            icon="👥"
            href="/personas"
          />
          <StatCard
            title="Active Agents"
            value={stats?.agents || 0}
            icon="⚙️"
            href="/agents"
          />
          <StatCard
            title="Conversations"
            value={stats?.conversations || 0}
            icon="💬"
            href="/chat"
          />
        </div>
      )}

      {/* Quick Actions */}
      <section className="mt-12">
        <h2 className="text-xl font-serif font-semibold text-cm-charcoal mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ActionCard
            title="Start a Conversation"
            description="Chat with an AI persona"
            href="/chat"
            color="terracotta"
          />
          <ActionCard
            title="Create Entity"
            description="Add to the knowledge graph"
            href="/entities?action=create"
            color="amber"
          />
          <ActionCard
            title="View Graph"
            description="Explore relationships"
            href="/graph"
            color="sienna"
          />
        </div>
      </section>

      {/* Recent Activity */}
      <section className="mt-12">
        <h2 className="text-xl font-serif font-semibold text-cm-charcoal mb-4">
          Getting Started
        </h2>
        <div className="bg-cm-ivory rounded-lg border border-cm-sand p-6">
          <ol className="space-y-4 text-cm-coffee">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">1</span>
              <span>Create or select a <strong className="text-cm-charcoal">Persona</strong> to chat with</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">2</span>
              <span>Add <strong className="text-cm-charcoal">Entities</strong> to the knowledge graph (projects, technologies, people)</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">3</span>
              <span>Create <strong className="text-cm-charcoal">Relationships</strong> between entities</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cm-terracotta text-cm-ivory text-sm flex items-center justify-center">4</span>
              <span>Chat with personas - context from the knowledge graph will enrich conversations</span>
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  href
}: {
  title: string;
  value: number;
  icon: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="block bg-cm-ivory rounded-lg border border-cm-sand p-6 hover:border-cm-terracotta transition-colors"
    >
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-3xl font-semibold text-cm-charcoal">{value}</span>
      </div>
      <p className="mt-2 text-sm text-cm-coffee">{title}</p>
    </a>
  );
}

function ActionCard({
  title,
  description,
  href,
  color
}: {
  title: string;
  description: string;
  href: string;
  color: 'terracotta' | 'amber' | 'sienna';
}) {
  const colorClasses = {
    terracotta: 'bg-cm-terracotta hover:bg-cm-sienna',
    amber: 'bg-cm-amber hover:bg-cm-terracotta',
    sienna: 'bg-cm-sienna hover:bg-cm-coffee',
  };

  return (
    <a
      href={href}
      className={`block rounded-lg p-6 text-cm-ivory transition-colors ${colorClasses[color]}`}
    >
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm opacity-90">{description}</p>
    </a>
  );
}
