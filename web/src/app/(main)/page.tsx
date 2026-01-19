'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Activity, Agent } from '@/types';

interface DashboardStats {
  activeAgents: number;
  unreadMessages: number;
  recentSessions: number;
  loading: boolean;
}

interface QuickLink {
  href: string;
  label: string;
  description: string;
  icon: string;
}

const QUICK_LINKS: QuickLink[] = [
  { href: '/chat', label: 'Chat', description: 'Talk with AI personas', icon: '💬' },
  { href: '/knowledge', label: 'Knowledge', description: 'Browse the knowledge graph', icon: '📊' },
  { href: '/agents', label: 'Agents', description: 'View connected AI agents', icon: '⚙️' },
  { href: '/sessions', label: 'Sessions', description: 'Track work sessions', icon: '⏱️' },
];

export default function StartPage() {
  const [stats, setStats] = useState<DashboardStats>({
    activeAgents: 0,
    unreadMessages: 0,
    recentSessions: 0,
    loading: true,
  });
  const [recentActivity, setRecentActivity] = useState<Activity[]>([]);
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [agentsRes, messagesRes, sessionsRes, activitiesRes] = await Promise.all([
          api.agents.list({ active_only: true }),
          api.messages.list(undefined, { limit: 100, unread_only: true }),
          api.workSessions.list({ limit: 10 }),
          api.activities.list({ limit: 10 }),
        ]);

        const agents = agentsRes.data?.agents || [];
        const messages = messagesRes.data?.messages || [];
        const sessions = sessionsRes.data?.sessions || [];
        const activities = activitiesRes.data?.activities || [];

        setStats({
          activeAgents: agents.length,
          unreadMessages: messages.length,
          recentSessions: sessions.length,
          loading: false,
        });

        setActiveAgents(agents.slice(0, 3));
        setRecentActivity(activities.filter((a: Activity) => a.activity_type !== 'agent_heartbeat').slice(0, 5));
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setStats(prev => ({ ...prev, loading: false }));
      }
    }

    loadDashboardData();
  }, []);

  const formatActivityTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getActivityDescription = (activity: Activity): string => {
    const meta = activity.extra_data || {};

    switch (activity.activity_type) {
      case 'message_sent':
        return `Message sent to ${meta.channel || 'channel'}`;
      case 'agent_registered':
        return `Agent connected${meta.client ? ` via ${meta.client}` : ''}`;
      case 'search_performed':
        return `Search performed`;
      case 'entity_created':
        return `Created ${meta.entity_type}: ${meta.entity_name}`;
      case 'entity_updated':
        return `Updated ${meta.entity_type}: ${meta.entity_name}`;
      default:
        return activity.activity_type.replace(/_/g, ' ');
    }
  };

  return (
    <div className="h-full overflow-auto bg-cm-cream">
      {/* Header */}
      <div className="p-6 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
          Welcome to Collective Memory
        </h1>
        <p className="text-cm-coffee mt-1">
          Your AI collaboration hub for persistent knowledge
        </p>
      </div>

      {/* Main content */}
      <div className="px-6 pb-6">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Active Agents Card */}
          <Link
            href="/agents"
            className="bg-cm-ivory rounded-xl border border-cm-sand p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-cm-terracotta/10 flex items-center justify-center text-2xl">
                ⚙️
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Active Agents</p>
                <p className="text-2xl font-semibold text-cm-charcoal">
                  {stats.loading ? '...' : stats.activeAgents}
                </p>
              </div>
            </div>
            {activeAgents.length > 0 && (
              <div className="mt-3 pt-3 border-t border-cm-sand">
                <div className="flex flex-wrap gap-1">
                  {activeAgents.map(agent => (
                    <span
                      key={agent.agent_key}
                      className="text-xs px-2 py-0.5 bg-cm-sand/50 rounded text-cm-coffee"
                    >
                      {agent.client || agent.agent_id?.split(':')[0]}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Link>

          {/* Unread Messages Card */}
          <Link
            href="/messages"
            className="bg-cm-ivory rounded-xl border border-cm-sand p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-cm-amber/10 flex items-center justify-center text-2xl">
                📥
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Unread Messages</p>
                <p className="text-2xl font-semibold text-cm-charcoal">
                  {stats.loading ? '...' : stats.unreadMessages}
                </p>
              </div>
            </div>
            {stats.unreadMessages > 0 && (
              <div className="mt-3 pt-3 border-t border-cm-sand">
                <p className="text-xs text-cm-coffee">
                  {stats.unreadMessages === 1 ? '1 message waiting' : `${stats.unreadMessages} messages waiting`}
                </p>
              </div>
            )}
          </Link>

          {/* Sessions Card */}
          <Link
            href="/sessions"
            className="bg-cm-ivory rounded-xl border border-cm-sand p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-cm-success/10 flex items-center justify-center text-2xl">
                ⏱️
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Work Sessions</p>
                <p className="text-2xl font-semibold text-cm-charcoal">
                  {stats.loading ? '...' : stats.recentSessions}
                </p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-cm-sand">
              <p className="text-xs text-cm-coffee">Recent sessions tracked</p>
            </div>
          </Link>
        </div>

        {/* Quick Links */}
        <div className="mb-8">
          <h2 className="font-serif text-lg font-semibold text-cm-charcoal mb-4">Quick Links</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {QUICK_LINKS.map(link => (
              <Link
                key={link.href}
                href={link.href}
                className="bg-cm-ivory rounded-lg border border-cm-sand p-4 hover:shadow-md hover:border-cm-terracotta/30 transition-all text-center"
              >
                <div className="text-2xl mb-2">{link.icon}</div>
                <p className="font-medium text-cm-charcoal">{link.label}</p>
                <p className="text-xs text-cm-coffee mt-1">{link.description}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif text-lg font-semibold text-cm-charcoal">Recent Activity</h2>
            <Link
              href="/activity"
              className="text-sm text-cm-terracotta hover:text-cm-sienna transition-colors"
            >
              View all
            </Link>
          </div>
          <div className="bg-cm-ivory rounded-xl border border-cm-sand divide-y divide-cm-sand">
            {stats.loading ? (
              <div className="p-4 text-center text-cm-coffee">
                Loading activity...
              </div>
            ) : recentActivity.length > 0 ? (
              recentActivity.map(activity => (
                <div key={activity.activity_key} className="p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cm-sand/50 flex items-center justify-center text-sm">
                    {activity.activity_type === 'entity_created' && '+'}
                    {activity.activity_type === 'entity_updated' && '~'}
                    {activity.activity_type === 'message_sent' && 'M'}
                    {activity.activity_type === 'agent_registered' && '@'}
                    {activity.activity_type === 'search_performed' && '?'}
                    {!['entity_created', 'entity_updated', 'message_sent', 'agent_registered', 'search_performed'].includes(activity.activity_type) && '•'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-cm-charcoal truncate">
                      {getActivityDescription(activity)}
                    </p>
                    <p className="text-xs text-cm-coffee">
                      {activity.actor} • {formatActivityTime(activity.created_at)}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-cm-coffee">
                No recent activity
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
