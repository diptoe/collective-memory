'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Session } from '@/types';

export default function AdminSessionsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState<'all' | 'web' | 'mcp'>('all');
  const [filterStatus, setFilterStatus] = useState<'active' | 'expired' | 'all'>('active');
  const [isCleaningUp, setIsCleaningUp] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<string | null>(null);

  // Helper functions (defined early for use in filtering)
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const isExpired = (session: Session) => {
    return new Date(session.expires_at) < new Date();
  };

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load sessions
  useEffect(() => {
    if (currentUser?.role === 'admin') {
      loadSessions();
    }
  }, [currentUser, filterStatus]);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const includeExpired = filterStatus === 'all' || filterStatus === 'expired';
      const response = await api.adminSessions.list({ include_expired: includeExpired });
      if (response.success && response.data) {
        setSessions(response.data.sessions);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Apply client-side filters
  const filteredSessions = sessions.filter((session) => {
    // Type filter
    if (filterType === 'web' && session.agent_key) return false;
    if (filterType === 'mcp' && !session.agent_key) return false;

    // Status filter (for expired-only view)
    if (filterStatus === 'expired' && !isExpired(session)) return false;
    if (filterStatus === 'active' && isExpired(session)) return false;

    return true;
  });

  const handleRevoke = async (sessionKey: string) => {
    if (!confirm('Are you sure you want to revoke this session?')) {
      return;
    }

    try {
      const response = await api.adminSessions.revoke(sessionKey);
      if (response.success) {
        loadSessions();
      }
    } catch (err) {
      console.error('Failed to revoke session:', err);
    }
  };

  const handleCleanup = async () => {
    setIsCleaningUp(true);
    setCleanupResult(null);
    try {
      const response = await api.adminSessions.cleanup();
      if (response.success && response.data) {
        setCleanupResult(`Cleaned up ${response.data.deleted_count} expired sessions`);
        loadSessions();
      }
    } catch (err) {
      console.error('Failed to cleanup sessions:', err);
      setCleanupResult('Failed to cleanup sessions');
    } finally {
      setIsCleaningUp(false);
    }
  };

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  // Calculate stats
  const activeSessions = sessions.filter(s => !isExpired(s)).length;
  const expiredSessions = sessions.filter(s => isExpired(s)).length;
  const sessionsWithAgent = sessions.filter(s => s.agent_key).length;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-cm-charcoal">Authentication Sessions</h1>
        <div className="flex items-center gap-3">
          <Link
            href="/admin/users"
            className="px-4 py-2 border border-cm-sand text-cm-charcoal rounded-md text-sm font-medium hover:bg-cm-sand/50 transition-colors"
          >
            ← Users
          </Link>
          <button
            onClick={handleCleanup}
            disabled={isCleaningUp}
            className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm hover:bg-cm-terracotta/90 disabled:opacity-50"
          >
            {isCleaningUp ? 'Cleaning...' : 'Cleanup Expired'}
          </button>
        </div>
      </div>

      {cleanupResult && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-md text-sm">
          {cleanupResult}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Sessions" value={sessions.length} />
        <StatCard label="Active" value={activeSessions} color="green" />
        <StatCard label="Expired" value={expiredSessions} color="red" />
        <StatCard label="MCP Sessions" value={sessionsWithAgent} color="blue" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as 'all' | 'web' | 'mcp')}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="all">All sessions</option>
          <option value="web">Web only</option>
          <option value="mcp">MCP only</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as 'active' | 'expired' | 'all')}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="active">Active only</option>
          <option value="expired">Expired only</option>
          <option value="all">All statuses</option>
        </select>
      </div>

      {/* Sessions Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">User</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Agent / Device</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">IP Address</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Last Activity</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Expires</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading sessions...
                </td>
              </tr>
            ) : filteredSessions.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No sessions found
                </td>
              </tr>
            ) : (
              filteredSessions.map((session) => (
                <tr
                  key={session.session_key}
                  className={`border-t border-cm-sand hover:bg-cm-cream/50 ${
                    isExpired(session) ? 'opacity-50' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    {session.user ? (
                      <div>
                        <div className="text-sm font-medium text-cm-charcoal">
                          {session.user.name}
                        </div>
                        <div className="text-xs text-cm-coffee">{session.user.email}</div>
                      </div>
                    ) : (
                      <span className="text-sm text-cm-coffee">{session.user_key}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {session.agent ? (
                      <div>
                        <div className="text-sm font-medium text-cm-charcoal">
                          {session.agent.agent_id}
                        </div>
                        <div className="text-xs text-cm-coffee">{session.agent.client}</div>
                      </div>
                    ) : (
                      <div className="text-sm text-cm-coffee">
                        {session.device_info || 'Unknown device'}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee font-mono text-xs">
                    {session.ip_address || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee">
                    {session.last_activity_at
                      ? formatDate(session.last_activity_at)
                      : '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee">
                    {formatDate(session.expires_at)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        isExpired(session)
                          ? 'bg-red-100 text-red-700'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      {isExpired(session) ? 'Expired' : 'Active'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {!isExpired(session) && (
                      <button
                        onClick={() => handleRevoke(session.session_key)}
                        className="text-sm text-red-600 hover:underline"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
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
  color?: 'green' | 'red' | 'blue';
}) {
  const colorClasses = {
    green: 'text-green-600',
    red: 'text-red-600',
    blue: 'text-blue-600',
  };

  return (
    <div className="bg-cm-ivory border border-cm-sand rounded-lg p-4">
      <p className="text-sm text-cm-coffee">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${color ? colorClasses[color] : 'text-cm-charcoal'}`}>
        {value}
      </p>
    </div>
  );
}
