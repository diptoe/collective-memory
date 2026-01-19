'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Agent, WorkSession, Entity } from '@/types';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

interface DashboardStats {
  activeAgents: number;
  unreadMessages: number;
  recentSessions: number;
  loading: boolean;
}

// Format duration in seconds to human-readable string
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const formatTimeRemaining = (seconds: number) => {
  if (seconds <= 0) return 'Expired';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
};

export default function StartPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats>({
    activeAgents: 0,
    unreadMessages: 0,
    recentSessions: 0,
    loading: true,
  });
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);
  const [activeSessions, setActiveSessions] = useState<WorkSession[]>([]);
  const [milestonesBySession, setMilestonesBySession] = useState<Record<string, Entity[]>>({});

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [agentsRes, messagesRes, sessionsRes, milestonesRes] = await Promise.all([
          api.agents.list({ active_only: true }),
          api.messages.list(undefined, { limit: 100, unread_only: true }),
          api.workSessions.list({ status: 'active', limit: 10 }),
          api.entities.list({ type: 'Milestone', limit: 50 }),
        ]);

        const agents = agentsRes.data?.agents || [];
        const messages = messagesRes.data?.messages || [];
        const sessions = sessionsRes.data?.sessions || [];
        const milestones = milestonesRes.data?.entities || [];

        // Filter milestones to only show "started" ones and group by session
        const startedMilestones = milestones.filter(
          (m: Entity) => m.properties?.status === 'started'
        );

        // Group milestones by work_session_key
        const grouped: Record<string, Entity[]> = {};
        startedMilestones.forEach((m: Entity) => {
          const sessionKey = m.work_session_key;
          if (sessionKey) {
            if (!grouped[sessionKey]) grouped[sessionKey] = [];
            grouped[sessionKey].push(m);
          }
        });

        setStats({
          activeAgents: agents.length,
          unreadMessages: messages.length,
          recentSessions: sessions.length,
          loading: false,
        });

        setActiveAgents(agents.slice(0, 3));
        setActiveSessions(sessions);
        setMilestonesBySession(grouped);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setStats(prev => ({ ...prev, loading: false }));
      }
    }

    loadDashboardData();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="h-full overflow-auto bg-cm-cream">
      {/* User Welcome Section */}
      <div className="p-6 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
          {getGreeting()}, {user?.first_name || 'there'}
        </h1>
        <p className="text-cm-coffee mt-1">
          Here's what's happening in your workspace
        </p>
      </div>

      {/* Main content */}
      <div className="px-6 pb-6">
        {/* Active Sessions with Milestones */}
        <div className="mb-6">
          {activeSessions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activeSessions.map((session) => {
                const sessionMilestones = milestonesBySession[session.session_key] || [];
                return (
                  <Link
                    key={session.session_key}
                    href="/sessions"
                    className="block bg-cm-ivory rounded-xl border border-cm-sand p-5 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-cm-success/10 flex items-center justify-center">
                        <div className="w-3 h-3 rounded-full bg-cm-success animate-pulse" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm text-cm-coffee">Active Session</p>
                          <code className="text-xs font-mono text-cm-coffee/70 bg-cm-sand/50 px-1.5 py-0.5 rounded">
                            {session.session_key}
                          </code>
                        </div>
                        <p className="text-lg font-semibold text-cm-charcoal truncate">
                          {session.name || 'Unnamed session'}
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-cm-sand flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-cm-coffee">
                      {session.agent_id && (
                        <span className="font-mono bg-cm-sand/50 px-1.5 py-0.5 rounded">
                          {session.agent_id}
                        </span>
                      )}
                      <span>
                        Duration: {formatDuration(Math.floor((Date.now() - new Date(session.started_at).getTime()) / 1000))}
                      </span>
                      {session.time_remaining_seconds !== undefined && (
                        <span className={cn(
                          session.time_remaining_seconds < 600 ? 'text-cm-warning font-medium' : ''
                        )}>
                          Expires in {formatTimeRemaining(session.time_remaining_seconds)}
                        </span>
                      )}
                    </div>
                    {/* Milestones within this session */}
                    {sessionMilestones.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-cm-sand">
                        <p className="text-xs text-cm-coffee mb-2 flex items-center gap-1">
                          <span>🚀</span>
                          <span>{sessionMilestones.length} active milestone{sessionMilestones.length !== 1 ? 's' : ''}</span>
                        </p>
                        <div className="space-y-1">
                          {sessionMilestones.map((milestone) => (
                            <div
                              key={milestone.entity_key}
                              className="flex items-center justify-between py-1 px-2 bg-cm-sand/30 rounded"
                            >
                              <p className="text-sm text-cm-charcoal truncate flex-1">{milestone.name}</p>
                              {typeof milestone.properties?.started_at === 'string' && (
                                <span className="text-xs text-cm-coffee ml-2 flex-shrink-0">
                                  {formatDuration(Math.floor((Date.now() - new Date(milestone.properties.started_at).getTime()) / 1000))}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="bg-cm-ivory border border-cm-sand rounded-xl p-5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-cm-sand/50 flex items-center justify-center text-2xl">
                  ⏱️
                </div>
                <div className="flex-1">
                  <p className="text-sm text-cm-coffee">No Active Sessions</p>
                  <p className="text-cm-charcoal font-medium">Start a session to track your work</p>
                </div>
                <Link
                  href="/sessions"
                  className="px-4 py-2 bg-cm-terracotta text-cm-ivory text-sm rounded-lg hover:bg-cm-terracotta/90 transition-colors"
                >
                  Start Session
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
      </div>
    </div>
  );
}
