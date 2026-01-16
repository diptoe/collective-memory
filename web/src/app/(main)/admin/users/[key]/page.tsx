'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { User, Session, Domain } from '@/types';

export default function UserDetailPage() {
  const router = useRouter();
  const params = useParams();
  const userKey = params.key as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionInProgress, setActionInProgress] = useState('');

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load user data
  useEffect(() => {
    if (currentUser?.role === 'admin' && userKey) {
      loadUserData();
    }
  }, [currentUser, userKey]);

  const loadUserData = async () => {
    setIsLoading(true);
    try {
      const [userResponse, sessionsResponse, domainsResponse] = await Promise.all([
        api.users.get(userKey),
        api.users.sessions(userKey),
        api.domains.list({ status: 'active' }),
      ]);

      if (userResponse.success && userResponse.data) {
        setUser(userResponse.data.user);
      } else {
        setError('User not found');
      }

      if (sessionsResponse.success && sessionsResponse.data) {
        setSessions(sessionsResponse.data.sessions);
      }

      if (domainsResponse.success && domainsResponse.data) {
        setDomains(domainsResponse.data.domains);
      }
    } catch (err) {
      setError('Failed to load user');
    } finally {
      setIsLoading(false);
    }
  };

  const changeRole = async (newRole: 'admin' | 'user') => {
    if (!user) return;
    setActionInProgress('role');
    setError('');

    try {
      const response = await api.users.changeRole(userKey, newRole);
      if (response.success && response.data) {
        setUser(response.data.user);
      } else {
        setError(response.msg || 'Failed to change role');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to change role');
    } finally {
      setActionInProgress('');
    }
  };

  const toggleStatus = async () => {
    if (!user) return;
    setActionInProgress('status');
    setError('');

    const newStatus = user.status === 'active' ? 'suspended' : 'active';

    try {
      const response = await api.users.update(userKey, { status: newStatus });
      if (response.success && response.data) {
        setUser(response.data.user);
        if (newStatus === 'suspended') {
          setSessions([]);  // Sessions are revoked when suspended
        }
      } else {
        setError(response.msg || 'Failed to update status');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update status');
    } finally {
      setActionInProgress('');
    }
  };

  const changeDomain = async (domainKey: string | null) => {
    if (!user) return;
    setActionInProgress('domain');
    setError('');

    try {
      const response = await api.users.changeDomain(userKey, domainKey);
      if (response.success && response.data) {
        setUser(response.data.user);
      } else {
        setError(response.msg || 'Failed to change domain');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to change domain');
    } finally {
      setActionInProgress('');
    }
  };

  const revokeSessions = async () => {
    setActionInProgress('sessions');
    setError('');

    try {
      const response = await api.users.revokeSessions(userKey);
      if (response.success) {
        setSessions([]);
      } else {
        setError(response.msg || 'Failed to revoke sessions');
      }
    } catch (err) {
      setError('Failed to revoke sessions');
    } finally {
      setActionInProgress('');
    }
  };

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-cm-coffee">Loading user...</p>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
        <Link href="/admin/users" className="mt-4 inline-block text-cm-terracotta hover:underline">
          Back to Users
        </Link>
      </div>
    );
  }

  if (!user) return null;

  const isSelf = user.user_key === currentUser?.user_key;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/admin/users" className="text-cm-coffee hover:text-cm-charcoal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-lg font-medium">
            {user.initials}
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">{user.display_name}</h1>
            <p className="text-sm text-cm-coffee">{user.email}</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {/* User Details */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">User Details</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-cm-coffee">User Key</p>
            <p className="text-cm-charcoal font-mono text-sm">{user.user_key}</p>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">Email</p>
            <p className="text-cm-charcoal">{user.email}</p>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">First Name</p>
            <p className="text-cm-charcoal">{user.first_name}</p>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">Last Name</p>
            <p className="text-cm-charcoal">{user.last_name}</p>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">Role</p>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-1 text-xs rounded-full ${
                  user.role === 'admin'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                {user.role}
              </span>
              {!isSelf && (
                <button
                  onClick={() => changeRole(user.role === 'admin' ? 'user' : 'admin')}
                  disabled={actionInProgress === 'role'}
                  className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                >
                  {actionInProgress === 'role'
                    ? 'Changing...'
                    : user.role === 'admin'
                    ? 'Demote to User'
                    : 'Promote to Admin'}
                </button>
              )}
            </div>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">Status</p>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-1 text-xs rounded-full ${
                  user.status === 'active'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}
              >
                {user.status}
              </span>
              {!isSelf && (
                <button
                  onClick={toggleStatus}
                  disabled={actionInProgress === 'status'}
                  className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                >
                  {actionInProgress === 'status'
                    ? 'Updating...'
                    : user.status === 'active'
                    ? 'Suspend User'
                    : 'Activate User'}
                </button>
              )}
            </div>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">Last Login</p>
            <p className="text-cm-charcoal">
              {user.last_login_at
                ? new Date(user.last_login_at).toLocaleString()
                : 'Never'}
            </p>
          </div>
          <div>
            <p className="text-sm text-cm-coffee">Created</p>
            <p className="text-cm-charcoal">{new Date(user.created_at).toLocaleString()}</p>
          </div>
          <div className="col-span-2">
            <p className="text-sm text-cm-coffee">Domain</p>
            <div className="flex items-center gap-2 mt-1">
              <select
                value={user.domain_key || ''}
                onChange={(e) => changeDomain(e.target.value || null)}
                disabled={actionInProgress === 'domain'}
                className="px-3 py-1.5 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 disabled:opacity-50"
              >
                <option value="">No domain assigned</option>
                {domains.map((domain) => (
                  <option key={domain.domain_key} value={domain.domain_key}>
                    {domain.name} ({domain.slug})
                  </option>
                ))}
              </select>
              {actionInProgress === 'domain' && (
                <span className="text-xs text-cm-coffee">Updating...</span>
              )}
              {user.domain_key && (
                <Link
                  href={`/admin/domains/${user.domain_key}`}
                  className="text-xs text-cm-terracotta hover:underline"
                >
                  View Domain
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sessions */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">
            Active Sessions ({sessions.length})
          </h2>
          {sessions.length > 0 && (
            <button
              onClick={revokeSessions}
              disabled={actionInProgress === 'sessions'}
              className="text-sm text-cm-terracotta hover:underline disabled:opacity-50"
            >
              {actionInProgress === 'sessions' ? 'Revoking...' : 'Revoke All'}
            </button>
          )}
        </div>

        {sessions.length === 0 ? (
          <p className="text-sm text-cm-coffee">No active sessions</p>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.session_key}
                className="flex items-center justify-between p-3 bg-cm-cream rounded-md"
              >
                <div>
                  <p className="text-sm font-medium text-cm-charcoal">
                    {session.user_agent ? parseUserAgent(session.user_agent) : 'Unknown device'}
                  </p>
                  <p className="text-xs text-cm-coffee mt-1">
                    {session.ip_address && `${session.ip_address} • `}
                    Last active: {new Date(session.last_activity_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function parseUserAgent(ua: string): string {
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Firefox')) return 'Firefox';
  if (ua.includes('Safari')) return 'Safari';
  if (ua.includes('Edge')) return 'Edge';
  return 'Browser';
}
