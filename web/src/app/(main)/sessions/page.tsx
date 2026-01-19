'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { WorkSession, Entity, UserTeam } from '@/types';
import { cn } from '@/lib/utils';
import { MilestoneMetrics } from '@/components/milestone-metrics';

const STATUS_COLORS = {
  active: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-600',
  expired: 'bg-amber-100 text-amber-800',
};

export default function SessionsPage() {
  const { user } = useAuthStore();
  const [sessions, setSessions] = useState<WorkSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'closed' | 'expired'>('all');
  const [showStartModal, setShowStartModal] = useState(false);
  const [projects, setProjects] = useState<Entity[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [sessionName, setSessionName] = useState<string>('');
  const [isStarting, setIsStarting] = useState(false);
  const [activeSession, setActiveSession] = useState<WorkSession | null>(null);

  // Get user's teams from auth store
  const teams: UserTeam[] = user?.teams || [];

  const loadSessions = async () => {
    try {
      const params: { status?: 'active' | 'closed' | 'expired' } = {};
      if (filterStatus !== 'all') {
        params.status = filterStatus;
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
  };

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

  useEffect(() => {
    loadSessions();
    loadActiveSession();
    loadProjects();
  }, []);

  useEffect(() => {
    loadSessions();
  }, [filterStatus]);

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
        loadSessions();
        loadActiveSession();
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
      loadSessions();
      loadActiveSession();
    } catch (err) {
      console.error('Failed to extend session:', err);
    }
  };

  const handleCloseSession = async (sessionKey: string) => {
    if (!confirm('Are you sure you want to close this session?')) return;

    try {
      await api.workSessions.close(sessionKey);
      loadSessions();
      loadActiveSession();
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

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Work Sessions
          </h1>
          <p className="text-cm-coffee mt-1">
            Track focused work periods on projects
          </p>
        </div>
        <button
          onClick={() => setShowStartModal(true)}
          disabled={!!activeSession}
          className={cn(
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeSession
              ? 'bg-cm-sand text-cm-coffee cursor-not-allowed'
              : 'bg-cm-terracotta text-cm-ivory hover:bg-cm-terracotta/90'
          )}
          title={activeSession ? 'Close current session first' : 'Start new session'}
        >
          Start Session
        </button>
      </div>

      {/* Active Session Banner */}
      {activeSession && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
                <span className="font-medium text-green-800">Active Session</span>
              </div>
              <p className="text-sm text-green-700 mt-1">
                {activeSession.name || 'Unnamed session'} - Project: {activeSession.project?.name || activeSession.project_key}
              </p>
              {activeSession.time_remaining_seconds !== undefined && (
                <p className={cn(
                  'text-sm mt-1',
                  activeSession.time_remaining_seconds < 600
                    ? 'text-amber-600 font-medium'
                    : 'text-green-600'
                )}>
                  Expires in {formatTimeRemaining(activeSession.time_remaining_seconds)}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleExtendSession(activeSession.session_key)}
                className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
              >
                Extend 1h
              </button>
              <button
                onClick={() => handleCloseSession(activeSession.session_key)}
                className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total" value={sessions.length} />
        <StatCard label="Active" value={activeSessions.length} color="green" />
        <StatCard label="Closed" value={closedSessions.length} color="gray" />
        <StatCard label="Expired" value={expiredSessions.length} color="amber" />
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
            />
          ))}
        </div>
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
}: {
  session: WorkSession;
  isActive: boolean;
  onExtend: () => void;
  onClose: () => void;
  formatTimeRemaining: (seconds: number) => string;
  formatDate: (dateStr: string) => string;
}) {
  const [expanded, setExpanded] = useState(false);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loadingEntities, setLoadingEntities] = useState(false);
  const [entityCount, setEntityCount] = useState<number | null>(null);
  const [messageCount, setMessageCount] = useState<number | null>(null);

  // Load stats when component mounts
  useEffect(() => {
    const loadStats = async () => {
      try {
        const res = await api.workSessions.get(session.session_key, { include_stats: true });
        if (res.success && res.data?.session?.stats) {
          setEntityCount(res.data.session.stats.entity_count);
          setMessageCount(res.data.session.stats.message_count);
        }
      } catch (err) {
        console.error('Failed to load session stats:', err);
      }
    };
    loadStats();
  }, [session.session_key]);

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
        'border rounded-lg transition-colors',
        isActive
          ? 'bg-green-50 border-green-200'
          : 'bg-cm-ivory border-cm-sand hover:border-cm-terracotta/30'
      )}
    >
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-cm-charcoal">
                {session.name || 'Unnamed Session'}
              </h3>
              <span className={cn('px-2 py-0.5 text-xs rounded-full', STATUS_COLORS[session.status])}>
                {session.status}
              </span>
              {isActive && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-green-500 text-white">
                  Current
                </span>
              )}
            </div>

            <div className="text-sm text-cm-coffee space-y-1">
              <p>
                <span className="text-cm-charcoal/70">Project:</span>{' '}
                {session.project?.name || session.project_key}
              </p>
              <p>
                <span className="text-cm-charcoal/70">Started:</span>{' '}
                {formatDate(session.started_at)}
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
              {/* Stats row */}
              {(entityCount !== null || messageCount !== null) && (
                <div className="flex items-center gap-4 mt-2 pt-2 border-t border-cm-sand/50">
                  {entityCount !== null && (
                    <span className="text-xs text-cm-coffee">
                      <span className="font-medium">{entityCount}</span> entities
                    </span>
                  )}
                  {messageCount !== null && (
                    <span className="text-xs text-cm-coffee">
                      <span className="font-medium">{messageCount}</span> messages
                    </span>
                  )}
                  {entityCount !== null && entityCount > 0 && (
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

          {session.status === 'active' && (
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={onExtend}
                className="px-3 py-1.5 text-sm bg-cm-sand text-cm-coffee rounded-lg hover:bg-cm-sand/80 transition-colors"
              >
                Extend
              </button>
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
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
                  <div className="space-y-2">
                    {milestones.map((entity) => (
                      <div key={entity.entity_key} className="p-2 bg-cm-ivory rounded border border-cm-sand/50">
                        <div className="flex items-center gap-2">
                          <span>{getStatusEmoji(entity.properties?.status)}</span>
                          <span className="text-sm font-medium text-cm-charcoal">{entity.name}</span>
                          {typeof entity.properties?.status === 'string' && (
                            <span className={cn(
                              'px-1.5 py-0.5 text-xs rounded',
                              entity.properties.status === 'completed' ? 'bg-green-100 text-green-700' :
                              entity.properties.status === 'started' ? 'bg-blue-100 text-blue-700' :
                              entity.properties.status === 'blocked' ? 'bg-red-100 text-red-700' :
                              'bg-gray-100 text-gray-700'
                            )}>
                              {entity.properties.status}
                            </span>
                          )}
                          <span className="text-xs text-cm-coffee">
                            {new Date(entity.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        {entity.properties && Object.keys(entity.properties).filter(k => k !== 'status' && k !== 'work_session_key').length > 0 && (
                          <div className="mt-1 text-xs text-cm-coffee">
                            {Object.entries(entity.properties)
                              .filter(([key]) => key !== 'status' && key !== 'work_session_key')
                              .map(([key, value]) => (
                                <span key={key} className="mr-3">
                                  <span className="text-cm-charcoal/70">{key}:</span> {String(value)}
                                </span>
                              ))}
                          </div>
                        )}
                        {/* Milestone metrics */}
                        <MilestoneMetrics entityKey={entity.entity_key} className="mt-2" compact />
                      </div>
                    ))}
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
}: {
  label: string;
  value: number;
  color?: 'green' | 'gray' | 'amber';
}) {
  const colorClasses = {
    green: 'text-green-600',
    gray: 'text-gray-600',
    amber: 'text-amber-600',
  };

  return (
    <div className="bg-cm-ivory border border-cm-sand rounded-lg p-4">
      <p className="text-sm text-cm-coffee">{label}</p>
      <p className={cn('text-2xl font-semibold mt-1', color ? colorClasses[color] : 'text-cm-charcoal')}>
        {value}
      </p>
    </div>
  );
}
