'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useCanWrite } from '@/hooks/use-can-write';
import { WorkSession, Entity, UserTeam, Team, ClientType } from '@/types';
import { cn } from '@/lib/utils';
import { MilestoneMetricsPanel, extractAllMetrics } from '@/components/milestone-impact';
import { Markdown } from '@/components/markdown/markdown';

// Client configuration for icons
const CLIENT_CONFIG: Record<ClientType, { label: string; icon: string }> = {
  'claude-code': { label: 'Claude Code', icon: '/icons/claude_code.svg' },
  'claude-desktop': { label: 'Claude Desktop', icon: '/icons/claude_desktop.svg' },
  'codex': { label: 'Codex', icon: '/icons/gpt_codex.svg' },
  'gemini-cli': { label: 'Gemini CLI', icon: '/icons/gemini_cli.svg' },
  'cursor': { label: 'Cursor', icon: '/icons/cursor.svg' },
};

const STATUS_COLORS = {
  active: 'bg-cm-success/10 text-cm-success',
  closed: 'bg-cm-sand text-cm-coffee',
  expired: 'bg-cm-warning/10 text-cm-warning',
};

// Format duration in seconds to human-readable string
const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

// Refresh icon component
function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 21h5v-5" />
    </svg>
  );
}

type ViewMode = 'active' | 'browse';

export default function SessionsPage() {
  const { user } = useAuthStore();
  const canWrite = useCanWrite();
  const [sessions, setSessions] = useState<WorkSession[]>([]);
  const [userActiveSessions, setUserActiveSessions] = useState<WorkSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('browse'); // Will be set based on active sessions
  const [viewModeInitialized, setViewModeInitialized] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'closed' | 'expired'>('all');
  const [showStartModal, setShowStartModal] = useState(false);
  const [projects, setProjects] = useState<Entity[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [sessionName, setSessionName] = useState<string>('');
  const [isStarting, setIsStarting] = useState(false);
  const [activeSession, setActiveSession] = useState<WorkSession | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Admin team filter state
  const [allTeams, setAllTeams] = useState<Team[]>([]);
  const [teamFilter, setTeamFilter] = useState<'mine' | string>('mine'); // 'mine' or team_key

  // Get user's teams from auth store
  const teams: UserTeam[] = user?.teams || [];

  // Check if user is admin (system or domain admin)
  const isAdmin = user?.role === 'admin' || user?.role === 'domain_admin';

  // Load sessions for browse view (with filters)
  const loadSessions = useCallback(async () => {
    try {
      const params: { status?: 'active' | 'closed' | 'expired'; team_key?: string } = {};
      if (filterStatus !== 'all') {
        params.status = filterStatus;
      }
      // In browse view, admins can filter by team
      if (viewMode === 'browse' && isAdmin && teamFilter !== 'mine') {
        params.team_key = teamFilter;
      }
      const res = await api.workSessions.list(params);
      if (res.success && res.data) {
        setSessions(res.data.sessions || []);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoading(false);
    }
  }, [filterStatus, viewMode, isAdmin, teamFilter]);

  // Load user's active sessions (for active view)
  const loadUserActiveSessions = useCallback(async () => {
    try {
      const res = await api.workSessions.list({ status: 'active' });
      if (res.success && res.data) {
        const activeSessions = res.data.sessions || [];
        setUserActiveSessions(activeSessions);
        // Set initial view mode based on whether user has active sessions
        if (!viewModeInitialized) {
          setViewMode(activeSessions.length > 0 ? 'active' : 'browse');
          setViewModeInitialized(true);
        }
      }
    } catch (err) {
      console.error('Failed to load user active sessions:', err);
    }
  }, [viewModeInitialized]);

  const loadActiveSession = async () => {
    try {
      const res = await api.workSessions.getActive();
      if (res.success && res.data) {
        setActiveSession(res.data.session);
      }
    } catch (err) {
      console.error('Failed to load active session:', err);
    }
  };

  const loadProjects = async () => {
    try {
      const res = await api.entities.list({ type: 'Project' });
      if (res.success && res.data) {
        setProjects(res.data.entities || []);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  };

  // Load all teams for admin dropdown
  const loadAllTeams = async () => {
    if (!isAdmin) return;
    try {
      const res = await api.teams.list();
      if (res.success && res.data) {
        setAllTeams(res.data.teams || []);
      }
    } catch (err) {
      console.error('Failed to load teams:', err);
    }
  };

  // Refresh handler for active view
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([loadUserActiveSessions(), loadActiveSession()]);
    } finally {
      setIsRefreshing(false);
    }
  }, [loadUserActiveSessions]);

  // Initial load
  useEffect(() => {
    loadUserActiveSessions();
    loadActiveSession();
    loadProjects();
    if (isAdmin) {
      loadAllTeams();
    }
  }, [isAdmin]);

  // Load browse sessions when view mode changes to browse or filters change
  useEffect(() => {
    if (viewMode === 'browse') {
      loadSessions();
    }
  }, [viewMode, filterStatus, teamFilter, loadSessions]);

  const handleStartSession = async () => {
    if (!selectedProject) return;

    setIsStarting(true);
    try {
      const res = await api.workSessions.start({
        project_key: selectedProject,
        name: sessionName || undefined,
        team_key: selectedTeam || undefined,
      });
      if (res.success) {
        setShowStartModal(false);
        setSelectedProject('');
        setSelectedTeam('');
        setSessionName('');
        loadUserActiveSessions();
        loadActiveSession();
        if (viewMode === 'browse') loadSessions();
        // Switch to active view since user now has an active session
        setViewMode('active');
      }
    } catch (err) {
      console.error('Failed to start session:', err);
      alert('Failed to start session');
    } finally {
      setIsStarting(false);
    }
  };

  const handleExtendSession = async (sessionKey: string) => {
    try {
      await api.workSessions.extend(sessionKey, 1);
      loadUserActiveSessions();
      loadActiveSession();
      if (viewMode === 'browse') loadSessions();
    } catch (err) {
      console.error('Failed to extend session:', err);
    }
  };

  const handleCloseSession = async (sessionKey: string) => {
    if (!confirm('Are you sure you want to close this session?')) return;

    try {
      await api.workSessions.close(sessionKey);
      await loadUserActiveSessions();
      loadActiveSession();
      if (viewMode === 'browse') loadSessions();
      // If no more active sessions, switch to browse view
      const res = await api.workSessions.list({ status: 'active' });
      if (res.success && (!res.data?.sessions || res.data.sessions.length === 0)) {
        setViewMode('browse');
      }
    } catch (err) {
      console.error('Failed to close session:', err);
    }
  };

  const formatTimeRemaining = (seconds: number) => {
    if (seconds <= 0) return 'Expired';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  // Count sessions by status
  const activeSessions = sessions.filter(s => s.status === 'active');
  const closedSessions = sessions.filter(s => s.status === 'closed');
  const expiredSessions = sessions.filter(s => s.status === 'expired');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading sessions...</p>
      </div>
    );
  }

  // Determine if we should auto-expand the single active session
  const shouldAutoExpand = viewMode === 'active' && userActiveSessions.length === 1;

  return (
    <div className="p-6">
      {/* ACTIVE VIEW */}
      {viewMode === 'active' ? (
        <>
          {/* Header for Active View */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
                Active Sessions
              </h1>
              <p className="text-cm-coffee mt-1">
                {userActiveSessions.length === 1
                  ? 'Your current work session'
                  : `${userActiveSessions.length} active work sessions`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className={cn(
                  "p-2 rounded-lg border border-cm-sand hover:border-cm-terracotta/50 hover:bg-cm-ivory transition-colors",
                  isRefreshing && "opacity-50 cursor-not-allowed"
                )}
                title="Refresh"
              >
                <RefreshIcon className={cn(isRefreshing && "animate-spin")} />
              </button>
              <button
                onClick={() => setViewMode('browse')}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-cm-sand text-cm-coffee hover:bg-cm-sand/80 transition-colors"
              >
                Browse All
              </button>
              <button
                onClick={() => canWrite && setShowStartModal(true)}
                disabled={!!activeSession || !canWrite}
                title={!canWrite ? 'Guest users cannot start sessions' : activeSession ? 'Close current session first' : 'Start new session'}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  !canWrite || activeSession
                    ? 'bg-cm-sand text-cm-coffee cursor-not-allowed opacity-50'
                    : 'bg-cm-terracotta text-cm-ivory hover:bg-cm-terracotta/90'
                )}
              >
                Start Session
              </button>
            </div>
          </div>

          {/* Active Sessions List */}
          {userActiveSessions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-cm-coffee mb-4">No active sessions.</p>
              <button
                onClick={() => canWrite && setShowStartModal(true)}
                disabled={!canWrite}
                title={!canWrite ? 'Guest users cannot start sessions' : undefined}
                className={cn(
                  "px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg transition-colors",
                  canWrite ? "hover:bg-cm-terracotta/90" : "opacity-50 cursor-not-allowed"
                )}
              >
                Start a Session
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {userActiveSessions.map((session) => (
                <SessionCard
                  key={session.session_key}
                  session={session}
                  isActive={session.session_key === activeSession?.session_key}
                  onExtend={() => handleExtendSession(session.session_key)}
                  onClose={() => handleCloseSession(session.session_key)}
                  formatTimeRemaining={formatTimeRemaining}
                  formatDate={formatDate}
                  autoExpand={shouldAutoExpand}
                  canWrite={canWrite}
                />
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          {/* BROWSE VIEW */}
          {/* Header for Browse View */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
                Work Sessions
              </h1>
              <p className="text-cm-coffee mt-1">
                Track focused work periods on projects
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* Show "Back to Active" button if user has active sessions */}
              {userActiveSessions.length > 0 && (
                <button
                  onClick={() => setViewMode('active')}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-cm-success/10 text-cm-success hover:bg-cm-success/20 transition-colors flex items-center gap-2"
                >
                  <span className="w-2 h-2 rounded-full bg-cm-success animate-pulse" />
                  Active ({userActiveSessions.length})
                </button>
              )}
              <button
                onClick={() => canWrite && setShowStartModal(true)}
                disabled={!!activeSession || !canWrite}
                title={!canWrite ? 'Guest users cannot start sessions' : activeSession ? 'Close current session first' : 'Start new session'}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  !canWrite || activeSession
                    ? 'bg-cm-sand text-cm-coffee cursor-not-allowed opacity-50'
                    : 'bg-cm-terracotta text-cm-ivory hover:bg-cm-terracotta/90'
                )}
              >
                Start Session
              </button>
            </div>
          </div>

          {/* Admin Team Filter */}
          {isAdmin && allTeams.length > 0 && (
            <div className="mb-4 flex items-center gap-2">
              <span className="text-sm text-cm-coffee">View:</span>
              <select
                value={teamFilter}
                onChange={(e) => setTeamFilter(e.target.value)}
                className="px-3 py-1.5 text-sm border border-cm-sand rounded-lg bg-cm-ivory text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              >
                <option value="mine">My Sessions</option>
                {allTeams.map((team) => (
                  <option key={team.team_key} value={team.team_key}>
                    {team.name} (Team)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Stats Cards */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <StatCard label="Total" value={sessions.length} icon="📊" />
            <StatCard label="Active" value={activeSessions.length} color="success" icon="⚡" />
            <StatCard label="Closed" value={closedSessions.length} color="default" icon="✓" />
            <StatCard label="Expired" value={expiredSessions.length} color="warning" icon="⏱️" />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 mb-6">
            {(['all', 'active', 'closed', 'expired'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg transition-colors capitalize',
                  filterStatus === status
                    ? 'bg-cm-terracotta text-cm-ivory'
                    : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
                )}
              >
                {status}
              </button>
            ))}
          </div>

          {/* Sessions List */}
          {sessions.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-cm-coffee mb-4">No work sessions found.</p>
              <p className="text-sm text-cm-coffee/70">
                Start a session to begin tracking your work on a project.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <SessionCard
                  key={session.session_key}
                  session={session}
                  isActive={session.session_key === activeSession?.session_key}
                  onExtend={() => handleExtendSession(session.session_key)}
                  onClose={() => handleCloseSession(session.session_key)}
                  formatTimeRemaining={formatTimeRemaining}
                  formatDate={formatDate}
                  canWrite={canWrite}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Start Session Modal */}
      {showStartModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-cm-cream rounded-lg p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Start Work Session</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Project *
                </label>
                <select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-lg bg-cm-ivory text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">Select a project...</option>
                  {projects.map((project) => (
                    <option key={project.entity_key} value={project.entity_key}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Session Name (optional)
                </label>
                <input
                  type="text"
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  placeholder="e.g., Feature implementation"
                  className="w-full px-3 py-2 border border-cm-sand rounded-lg bg-cm-ivory text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                />
              </div>

              {teams.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-cm-charcoal mb-1">
                    Team (optional)
                  </label>
                  <select
                    value={selectedTeam}
                    onChange={(e) => setSelectedTeam(e.target.value)}
                    className="w-full px-3 py-2 border border-cm-sand rounded-lg bg-cm-ivory text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                  >
                    <option value="">No team (domain-wide)</option>
                    {teams.map((team) => (
                      <option key={team.team_key} value={team.team_key}>
                        {team.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-cm-coffee mt-1">
                    Scopes the session to a specific team
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowStartModal(false);
                  setSelectedProject('');
                  setSelectedTeam('');
                  setSessionName('');
                }}
                className="px-4 py-2 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartSession}
                disabled={!selectedProject || isStarting}
                className="px-4 py-2 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-terracotta/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isStarting ? 'Starting...' : 'Start Session'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SessionCard({
  session,
  isActive,
  onExtend,
  onClose,
  formatTimeRemaining,
  formatDate,
  autoExpand = false,
  canWrite = true,
}: {
  session: WorkSession;
  isActive: boolean;
  onExtend: () => void;
  onClose: () => void;
  formatTimeRemaining: (seconds: number) => string;
  formatDate: (dateStr: string) => string;
  autoExpand?: boolean;
  canWrite?: boolean;
}) {
  const [expanded, setExpanded] = useState(autoExpand);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loadingEntities, setLoadingEntities] = useState(false);
  const [milestoneCount, setMilestoneCount] = useState<number | null>(null);
  const [messageCount, setMessageCount] = useState<number | null>(null);
  const [otherEntityCount, setOtherEntityCount] = useState<number | null>(null);
  const [autoExpandLoaded, setAutoExpandLoaded] = useState(false);

  // Load stats when component mounts
  useEffect(() => {
    const loadStats = async () => {
      try {
        const res = await api.workSessions.get(session.session_key, { include_stats: true });
        if (res.success && res.data?.session?.stats) {
          setMilestoneCount(res.data.session.stats.milestone_count);
          setMessageCount(res.data.session.stats.message_count);
          setOtherEntityCount(res.data.session.stats.other_entity_count);
        }
      } catch (err) {
        console.error('Failed to load session stats:', err);
      }
    };
    loadStats();
  }, [session.session_key]);

  // Auto-expand: load entities when autoExpand is true
  useEffect(() => {
    if (autoExpand && !autoExpandLoaded && entities.length === 0) {
      setAutoExpandLoaded(true);
      const loadEntities = async () => {
        setLoadingEntities(true);
        try {
          const res = await api.workSessions.getEntities(session.session_key, { limit: 50 });
          if (res.success && res.data) {
            setEntities(res.data.entities || []);
          }
        } catch (err) {
          console.error('Failed to load session entities:', err);
        } finally {
          setLoadingEntities(false);
        }
      };
      loadEntities();
    }
  }, [autoExpand, autoExpandLoaded, entities.length, session.session_key]);

  const handleExpand = async () => {
    if (!expanded && entities.length === 0) {
      setLoadingEntities(true);
      try {
        const res = await api.workSessions.getEntities(session.session_key, { limit: 50 });
        if (res.success && res.data) {
          setEntities(res.data.entities || []);
        }
      } catch (err) {
        console.error('Failed to load session entities:', err);
      } finally {
        setLoadingEntities(false);
      }
    }
    setExpanded(!expanded);
  };

  // Filter to get Milestones only
  const milestones = entities.filter(e => e.entity_type === 'Milestone');

  // Status emoji for milestone display
  const getStatusEmoji = (status: string | unknown) => {
    if (status === 'started') return '🚀';
    if (status === 'completed') return '✅';
    if (status === 'blocked') return '🚫';
    return '📍';
  };

  return (
    <div
      className={cn(
        'border rounded-xl transition-colors bg-cm-ivory border-cm-sand',
        isActive && 'ring-2 ring-cm-success/30'
      )}
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {/* Status indicator icon */}
            <div className={cn(
              'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
              session.status === 'active' ? 'bg-cm-success/10' :
              session.status === 'expired' ? 'bg-cm-warning/10' :
              'bg-cm-sand/50'
            )}>
              {session.status === 'active' ? (
                <div className="w-3 h-3 rounded-full bg-cm-success animate-pulse" />
              ) : session.status === 'expired' ? (
                <span className="text-cm-warning">⏱️</span>
              ) : (
                <span className="text-cm-coffee/50">✓</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-cm-charcoal">
                  {session.name || 'Unnamed Session'}
                </h3>
                <span className={cn('px-2 py-0.5 text-xs rounded-full', STATUS_COLORS[session.status])}>
                  {session.status}
                </span>
                {isActive && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-cm-success/10 text-cm-success font-medium">
                    Current
                  </span>
                )}
            </div>
            <div className="flex items-center gap-1 mb-2">
              <code className="text-xs font-mono text-cm-coffee/70 bg-cm-sand/30 px-1.5 py-0.5 rounded">
                {session.session_key}
              </code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(session.session_key);
                }}
                className="p-1 text-cm-coffee/50 hover:text-cm-terracotta transition-colors"
                title="Copy session key"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>

            <div className="text-sm text-cm-coffee space-y-1">
              {/* Project info */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-cm-charcoal/70">Project:</span>
                <span className="font-medium text-cm-charcoal">{session.project?.name || session.project_key}</span>
                {session.project?.repository_url && (
                  <a
                    href={session.project.repository_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-cm-terracotta hover:underline flex items-center gap-1"
                  >
                    {session.project.repository_owner}/{session.project.repository_name}
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>
              {/* Agent info with icons */}
              {(session.agent_id || session.agent) && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-cm-charcoal/70">Started by:</span>
                  {session.agent?.client && CLIENT_CONFIG[session.agent.client as ClientType] && (
                    <img
                      src={CLIENT_CONFIG[session.agent.client as ClientType].icon}
                      alt={CLIENT_CONFIG[session.agent.client as ClientType].label}
                      className="w-4 h-4"
                      title={CLIENT_CONFIG[session.agent.client as ClientType].label}
                    />
                  )}
                  <span className="font-mono text-xs bg-cm-sand/50 px-1 py-0.5 rounded">
                    {session.agent?.agent_id || session.agent_id}
                  </span>
                  {session.agent?.model_name && (
                    <span className="text-xs text-cm-coffee/70 flex items-center gap-1">
                      · {session.agent.model_name}
                    </span>
                  )}
                  {session.agent?.persona_name && (
                    <span className="text-xs px-1.5 py-0.5 bg-cm-sand/50 rounded text-cm-coffee/70">
                      {session.agent.persona_name}
                    </span>
                  )}
                  {session.agent?.user_name && (
                    <span className="text-xs text-cm-coffee/60">
                      ({session.agent.user_name})
                    </span>
                  )}
                </div>
              )}
              <p>
                <span className="text-cm-charcoal/70">Started:</span>{' '}
                {formatDate(session.started_at)}
                {' · '}
                <span className="text-cm-charcoal/70">Duration:</span>{' '}
                {session.ended_at
                  ? formatDuration(Math.floor((new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 1000))
                  : formatDuration(Math.floor((Date.now() - new Date(session.started_at).getTime()) / 1000))
                }
              </p>
              {session.ended_at && (
                <p>
                  <span className="text-cm-charcoal/70">Ended:</span>{' '}
                  {formatDate(session.ended_at)}
                </p>
              )}
              {session.status === 'active' && session.time_remaining_seconds !== undefined && (
                <p className={cn(
                  session.time_remaining_seconds < 600 ? 'text-amber-600 font-medium' : ''
                )}>
                  <span className="text-cm-charcoal/70">Expires in:</span>{' '}
                  {formatTimeRemaining(session.time_remaining_seconds)}
                </p>
              )}
              {session.summary && (
                <p className="mt-2 text-cm-charcoal/80 italic">
                  "{session.summary}"
                </p>
              )}
              {/* Stats row - categorized counts */}
              {(milestoneCount !== null || messageCount !== null || otherEntityCount !== null) && (
                <div className="flex items-center gap-4 mt-2 pt-2 border-t border-cm-sand/50">
                  {milestoneCount !== null && milestoneCount > 0 && (
                    <span className="text-xs text-cm-coffee">
                      <span className="font-medium">{milestoneCount}</span> milestone{milestoneCount !== 1 ? 's' : ''}
                    </span>
                  )}
                  {messageCount !== null && messageCount > 0 && (
                    <span className="text-xs text-cm-coffee">
                      <span className="font-medium">{messageCount}</span> message{messageCount !== 1 ? 's' : ''}
                    </span>
                  )}
                  {otherEntityCount !== null && otherEntityCount > 0 && (
                    <span className="text-xs text-cm-coffee">
                      <span className="font-medium">{otherEntityCount}</span> other
                    </span>
                  )}
                  {((milestoneCount ?? 0) + (otherEntityCount ?? 0)) > 0 && (
                    <button
                      onClick={handleExpand}
                      className="text-xs text-cm-terracotta hover:underline"
                    >
                      {expanded ? 'Hide details' : 'Show details'}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
          </div>

          {session.status === 'active' && canWrite && (
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={onExtend}
                className="px-3 py-1.5 text-sm bg-cm-sand text-cm-coffee rounded-lg hover:bg-cm-sand/80 transition-colors"
              >
                Extend
              </button>
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-sm bg-cm-error/10 text-cm-error rounded-lg hover:bg-cm-error/20 transition-colors"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Expanded entities section */}
      {expanded && (
        <div className="border-t border-cm-sand/50 p-4 bg-cm-cream/50">
          {loadingEntities ? (
            <p className="text-sm text-cm-coffee">Loading entities...</p>
          ) : entities.length === 0 ? (
            <p className="text-sm text-cm-coffee">No entities recorded in this session.</p>
          ) : (
            <div className="space-y-3">
              {/* Milestones section */}
              {milestones.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-cm-charcoal uppercase tracking-wider mb-2">
                    Milestones ({milestones.length})
                  </h4>
                  <div className="space-y-3">
                    {milestones.map((entity) => {
                      // Extract all metrics from entity.metrics (loaded with entities)
                      const allMetrics = extractAllMetrics(entity.metrics);

                      return (
                        <div key={entity.entity_key} className="p-3 bg-cm-ivory rounded-lg border border-cm-sand/50">
                          <div className="flex gap-4">
                            {/* Left: Milestone content */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span>{getStatusEmoji(entity.properties?.status)}</span>
                                <span className="text-sm font-medium text-cm-charcoal">{entity.name}</span>
                                <code className="text-[10px] font-mono text-cm-coffee/50 bg-cm-sand/30 px-1 py-0.5 rounded">
                                  {entity.entity_key}
                                </code>
                                <button
                                  onClick={() => navigator.clipboard.writeText(entity.entity_key)}
                                  className="p-0.5 text-cm-coffee/40 hover:text-cm-terracotta transition-colors"
                                  title="Copy milestone key"
                                >
                                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                </button>
                                {typeof entity.properties?.status === 'string' && (
                                  <span className={cn(
                                    'px-1.5 py-0.5 text-xs rounded',
                                    entity.properties.status === 'completed' ? 'bg-cm-success/10 text-cm-success' :
                                    entity.properties.status === 'started' ? 'bg-cm-info/10 text-cm-info' :
                                    entity.properties.status === 'blocked' ? 'bg-cm-error/10 text-cm-error' :
                                    'bg-cm-sand text-cm-coffee'
                                  )}>
                                    {entity.properties.status}
                                  </span>
                                )}
                                {/* Duration display: show saved duration for completed, or calculate running duration for started */}
                                {typeof entity.properties?.duration_seconds === 'number' && entity.properties.duration_seconds > 0 ? (
                                  <span className="px-1.5 py-0.5 text-xs bg-cm-sand rounded text-cm-charcoal">
                                    {formatDuration(entity.properties.duration_seconds)}
                                  </span>
                                ) : entity.properties?.status === 'started' ? (
                                  <span className="px-1.5 py-0.5 text-xs bg-cm-info/10 text-cm-info rounded animate-pulse">
                                    {formatDuration(Math.floor((Date.now() - new Date(String(entity.properties?.started_at || entity.created_at)).getTime()) / 1000))}
                                  </span>
                                ) : null}
                                <span className="text-xs text-cm-coffee">
                                  {new Date(entity.created_at).toLocaleTimeString()}
                                </span>
                                {typeof entity.properties?.agent_id === 'string' && (
                                  <span className="text-xs text-cm-coffee/70 font-mono">
                                    by {entity.properties.agent_id}
                                  </span>
                                )}
                                <Link
                                  href={`/entities/${entity.entity_type.toLowerCase()}/${entity.entity_key}`}
                                  className="text-cm-coffee/40 hover:text-cm-terracotta transition-colors"
                                  title="View milestone entity"
                                >
                                  →
                                </Link>
                              </div>

                              {/* Narrative fields - goal, outcome, summary */}
                              {typeof entity.properties?.goal === 'string' && (
                                <div className="mt-2">
                                  <span className="text-xs font-medium text-cm-charcoal/70">Goal:</span>
                                  <Markdown content={entity.properties.goal} className="mt-0.5 text-xs text-cm-coffee" />
                                </div>
                              )}
                              {typeof entity.properties?.outcome === 'string' && (
                                <div className="mt-2">
                                  <span className="text-xs font-medium text-cm-charcoal/70">Outcome:</span>
                                  <Markdown content={entity.properties.outcome} className="mt-0.5 text-xs text-cm-coffee" />
                                </div>
                              )}
                              {typeof entity.properties?.summary === 'string' && (
                                <div className="mt-2">
                                  <span className="text-xs font-medium text-cm-charcoal/70">Summary:</span>
                                  <div className="mt-1 pl-2 border-l-2 border-cm-sand">
                                    <Markdown content={entity.properties.summary} className="text-xs text-cm-coffee" />
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Right: All metrics visualization */}
                            <MilestoneMetricsPanel
                              {...allMetrics}
                              className="flex-shrink-0"
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Other entities */}
              {entities.filter(e => e.entity_type !== 'Milestone').length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-cm-charcoal uppercase tracking-wider mb-2">
                    Other Entities ({entities.filter(e => e.entity_type !== 'Milestone').length})
                  </h4>
                  <div className="space-y-2">
                    {entities.filter(e => e.entity_type !== 'Milestone').map((entity) => (
                      <div key={entity.entity_key} className="p-2 bg-cm-ivory rounded border border-cm-sand/50">
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 text-xs bg-cm-sand rounded">{entity.entity_type}</span>
                          <span className="text-sm font-medium text-cm-charcoal">{entity.name}</span>
                          <span className="text-xs text-cm-coffee">
                            {new Date(entity.created_at).toLocaleTimeString()}
                          </span>
                          <Link
                            href={`/entities/${entity.entity_type.toLowerCase()}/${entity.entity_key}`}
                            className="text-cm-coffee/40 hover:text-cm-terracotta transition-colors"
                            title="View entity"
                          >
                            →
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: number;
  color?: 'success' | 'default' | 'warning';
  icon?: string;
}) {
  const colorClasses = {
    success: 'text-cm-success',
    default: 'text-cm-coffee',
    warning: 'text-cm-warning',
  };

  const iconBgClasses = {
    success: 'bg-cm-success/10',
    default: 'bg-cm-sand/50',
    warning: 'bg-cm-warning/10',
  };

  return (
    <div className="bg-cm-ivory border border-cm-sand rounded-xl p-4">
      <div className="flex items-center gap-3">
        {icon && (
          <div className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center text-lg',
            color ? iconBgClasses[color] : 'bg-cm-sand/50'
          )}>
            {icon}
          </div>
        )}
        <div>
          <p className="text-sm text-cm-coffee">{label}</p>
          <p className={cn('text-2xl font-semibold', color ? colorClasses[color] : 'text-cm-charcoal')}>
            {value}
          </p>
        </div>
      </div>
    </div>
  );
}
