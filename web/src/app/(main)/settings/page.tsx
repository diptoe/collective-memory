'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Session } from '@/types';

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, setUser, logout: logoutStore } = useAuthStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [patCopied, setPatCopied] = useState(false);
  const [isRegeneratingPat, setIsRegeneratingPat] = useState(false);
  const [showPatConfirm, setShowPatConfirm] = useState(false);
  const [error, setError] = useState('');

  // Profile editing state
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Logout state
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // Load sessions
  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);

  const loadSessions = async () => {
    try {
      const response = await api.auth.sessions();
      if (response.success && response.data) {
        setSessions(response.data.sessions);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const copyPat = async () => {
    if (user?.pat) {
      await navigator.clipboard.writeText(user.pat);
      setPatCopied(true);
      setTimeout(() => setPatCopied(false), 2000);
    }
  };

  const regeneratePat = async () => {
    setIsRegeneratingPat(true);
    setError('');

    try {
      const response = await api.auth.regeneratePat();
      if (response.success && response.data) {
        // Refresh user data to get new PAT
        const meResponse = await api.auth.me();
        if (meResponse.success && meResponse.data) {
          setUser(meResponse.data.user, meResponse.data.session);
        }
        setShowPatConfirm(false);
      } else {
        setError(response.msg || 'Failed to regenerate PAT');
      }
    } catch (err) {
      setError('Failed to regenerate PAT. Please try again.');
    } finally {
      setIsRegeneratingPat(false);
    }
  };

  const revokeSession = async (sessionKey: string) => {
    try {
      await api.auth.revokeSession(sessionKey);
      setSessions((prev) => prev.filter((s) => s.session_key !== sessionKey));
    } catch (err) {
      console.error('Failed to revoke session:', err);
    }
  };

  const revokeAllOtherSessions = async () => {
    const currentSessionKey = sessions.find((s) => s.is_current)?.session_key;
    for (const session of sessions) {
      if (session.session_key !== currentSessionKey) {
        await revokeSession(session.session_key);
      }
    }
  };

  // Profile editing
  const startEditingProfile = () => {
    setFirstName(user?.first_name || '');
    setLastName(user?.last_name || '');
    setIsEditingProfile(true);
    setProfileError('');
    setProfileSuccess('');
  };

  const cancelEditingProfile = () => {
    setIsEditingProfile(false);
    setProfileError('');
  };

  const saveProfile = async () => {
    setIsSavingProfile(true);
    setProfileError('');
    setProfileSuccess('');

    try {
      const response = await api.auth.updateProfile({
        first_name: firstName,
        last_name: lastName,
      });

      if (response.success && response.data) {
        setUser(response.data.user, null);
        setIsEditingProfile(false);
        setProfileSuccess('Profile updated successfully');
        setTimeout(() => setProfileSuccess(''), 3000);
      } else {
        setProfileError(response.msg || 'Failed to update profile');
      }
    } catch (err) {
      setProfileError('Failed to update profile. Please try again.');
    } finally {
      setIsSavingProfile(false);
    }
  };

  // Password change
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters');
      return;
    }

    setIsChangingPassword(true);

    try {
      const response = await api.auth.changePassword(currentPassword, newPassword);

      if (response.success) {
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordSuccess('Password changed successfully');
        setTimeout(() => setPasswordSuccess(''), 3000);
      } else {
        setPasswordError(response.msg || 'Failed to change password');
      }
    } catch (err) {
      setPasswordError('Failed to change password. Please try again.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Logout
  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await api.auth.logout();
      logoutStore();
      router.push('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      // Still clear local state even if API fails
      logoutStore();
      router.push('/login');
    }
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold text-cm-charcoal mb-6">Settings</h1>

      {/* Profile Section */}
      <section className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Profile</h2>
          {!isEditingProfile && (
            <button
              onClick={startEditingProfile}
              className="text-sm text-cm-sage hover:underline"
            >
              Edit
            </button>
          )}
        </div>

        {profileSuccess && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700">
            {profileSuccess}
          </div>
        )}
        {profileError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {profileError}
          </div>
        )}

        {isEditingProfile ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-cm-coffee mb-1">First Name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-sage"
                />
              </div>
              <div>
                <label className="block text-sm text-cm-coffee mb-1">Last Name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-sage"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-cm-coffee">Email</p>
                <p className="text-cm-charcoal font-medium">{user.email}</p>
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Role</p>
                <p className="text-cm-charcoal font-medium capitalize">{user.role}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={saveProfile}
                disabled={isSavingProfile}
                className="px-4 py-2 bg-cm-sage text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-sage/90 disabled:opacity-50 transition-colors"
              >
                {isSavingProfile ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={cancelEditingProfile}
                className="px-4 py-2 bg-cm-sand text-cm-charcoal rounded-md text-sm font-medium hover:bg-cm-sand/70 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-cm-coffee">Name</p>
              <p className="text-cm-charcoal font-medium">{user.display_name}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Email</p>
              <p className="text-cm-charcoal font-medium">{user.email}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Role</p>
              <p className="text-cm-charcoal font-medium capitalize">{user.role}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Member since</p>
              <p className="text-cm-charcoal font-medium">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Personal Access Token Section */}
      <section className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-2">Personal Access Token</h2>
        <p className="text-sm text-cm-coffee mb-4">
          Use this token to authenticate MCP clients and API requests.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {user.pat && (
          <div className="mb-4">
            <div className="flex items-center gap-2">
              <code className="flex-1 p-3 bg-cm-cream border border-cm-sand rounded-md font-mono text-sm text-cm-charcoal overflow-x-auto">
                {user.pat}
              </code>
              <button
                onClick={copyPat}
                className="px-4 py-2 bg-cm-sand text-cm-charcoal rounded-md text-sm font-medium hover:bg-cm-sand/70 transition-colors"
              >
                {patCopied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            {user.pat_created_at && (
              <p className="text-xs text-cm-coffee mt-2">
                Created: {new Date(user.pat_created_at).toLocaleString()}
              </p>
            )}
          </div>
        )}

        {/* MCP Configuration Example */}
        <div className="mb-4">
          <p className="text-sm font-medium text-cm-charcoal mb-2">MCP Configuration</p>
          <p className="text-xs text-cm-coffee mb-2">
            Add this to your MCP client configuration (e.g., Claude Desktop, Claude Code):
          </p>
          <pre className="p-3 bg-cm-cream border border-cm-sand rounded-md font-mono text-xs text-cm-charcoal overflow-x-auto">
{`{
  "mcpServers": {
    "collective-memory": {
      "command": "python",
      "args": ["-m", "cm_mcp.server"],
      "cwd": "/path/to/collective-memory",
      "env": {
        "CM_API_URL": "${typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5001'}",
        "CM_PAT": "${user.pat || 'your-pat-here'}"
      }
    }
  }
}`}
          </pre>
        </div>

        {/* Regenerate PAT */}
        {!showPatConfirm ? (
          <button
            onClick={() => setShowPatConfirm(true)}
            className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
          >
            Regenerate Token
          </button>
        ) : (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-md">
            <p className="text-sm text-amber-800 mb-3">
              <strong>Warning:</strong> Regenerating your PAT will invalidate your current token.
              Any MCP clients using the old token will need to be updated.
            </p>
            <div className="flex gap-2">
              <button
                onClick={regeneratePat}
                disabled={isRegeneratingPat}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
              >
                {isRegeneratingPat ? 'Regenerating...' : 'Confirm Regenerate'}
              </button>
              <button
                onClick={() => setShowPatConfirm(false)}
                className="px-4 py-2 bg-cm-sand text-cm-charcoal rounded-md text-sm font-medium hover:bg-cm-sand/70 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Sessions Section */}
      <section className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Active Sessions</h2>
          {sessions.length > 1 && (
            <button
              onClick={revokeAllOtherSessions}
              className="text-sm text-cm-terracotta hover:underline"
            >
              Revoke all other sessions
            </button>
          )}
        </div>

        {isLoadingSessions ? (
          <p className="text-sm text-cm-coffee">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <p className="text-sm text-cm-coffee">No active sessions</p>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.session_key}
                className={`flex items-center justify-between p-3 rounded-md ${
                  session.is_current ? 'bg-cm-sage/20 border border-cm-sage' : 'bg-cm-cream'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-cm-charcoal">
                      {session.user_agent ? parseUserAgent(session.user_agent) : 'Unknown device'}
                    </p>
                    {session.is_current && (
                      <span className="px-2 py-0.5 bg-cm-sage text-cm-ivory text-xs rounded-full">
                        Current
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-cm-coffee mt-1">
                    {session.ip_address && `${session.ip_address} • `}
                    Last active: {new Date(session.last_activity_at).toLocaleString()}
                  </p>
                </div>
                {!session.is_current && (
                  <button
                    onClick={() => revokeSession(session.session_key)}
                    className="text-sm text-cm-terracotta hover:underline"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Password Change Section */}
      <section className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Change Password</h2>

        {passwordSuccess && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-700">
            {passwordSuccess}
          </div>
        )}
        {passwordError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {passwordError}
          </div>
        )}

        <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm text-cm-coffee mb-1">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-cm-sand rounded-md text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-sage"
            />
          </div>
          <div>
            <label className="block text-sm text-cm-coffee mb-1">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-cm-sand rounded-md text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-sage"
            />
            <p className="text-xs text-cm-coffee mt-1">Minimum 8 characters</p>
          </div>
          <div>
            <label className="block text-sm text-cm-coffee mb-1">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 border border-cm-sand rounded-md text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-sage"
            />
          </div>
          <button
            type="submit"
            disabled={isChangingPassword}
            className="px-4 py-2 bg-cm-sage text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-sage/90 disabled:opacity-50 transition-colors"
          >
            {isChangingPassword ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </section>

      {/* Logout Section */}
      <section className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-2">Sign Out</h2>
        <p className="text-sm text-cm-coffee mb-4">
          Sign out of your account on this device.
        </p>
        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
        >
          {isLoggingOut ? 'Signing out...' : 'Sign Out'}
        </button>
      </section>
    </div>
  );
}

function parseUserAgent(ua: string): string {
  // Simple user agent parsing
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Firefox')) return 'Firefox';
  if (ua.includes('Safari')) return 'Safari';
  if (ua.includes('Edge')) return 'Edge';
  return 'Browser';
}
