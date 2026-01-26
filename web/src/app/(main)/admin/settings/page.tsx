'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

interface GuestSettings {
  exists: boolean;
  enabled: boolean;
  email: string;
  user_key?: string;
  created_at?: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Guest access state
  const [guestSettings, setGuestSettings] = useState<GuestSettings | null>(null);
  const [isTogglingGuest, setIsTogglingGuest] = useState(false);

  const isAdmin = currentUser?.role === 'admin';

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (!isAdmin) {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router, isAdmin]);

  // Load settings
  useEffect(() => {
    if (isAdmin) {
      loadSettings();
    }
  }, [isAdmin]);

  const loadSettings = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.guestSettings.get();
      if (response.success && response.data) {
        setGuestSettings(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleGuestAccess = async () => {
    if (!guestSettings) return;

    setIsTogglingGuest(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const newEnabled = !guestSettings.enabled;
      const response = await api.guestSettings.update(newEnabled);

      if (response.success) {
        setGuestSettings(prev => prev ? { ...prev, enabled: newEnabled, exists: true } : null);
        setSuccessMessage(`Guest access ${newEnabled ? 'enabled' : 'disabled'} successfully`);

        // Clear success message after 3 seconds
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to update guest access');
    } finally {
      setIsTogglingGuest(false);
    }
  };

  if (!isAuthenticated || !isAdmin) {
    return null;
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-cm-charcoal">Settings</h1>
          <p className="text-sm text-cm-coffee mt-1">
            System configuration and feature toggles
          </p>
        </div>
        <Link
          href="/admin/database"
          className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal transition-colors text-sm"
        >
          Back to Database
        </Link>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-700">{successMessage}</p>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <p className="text-cm-coffee">Loading settings...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Guest Access Section */}
          <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">👤</span>
                  <h2 className="text-lg font-medium text-cm-charcoal">Guest Access</h2>
                </div>
                <p className="text-sm text-cm-coffee mb-4">
                  Allow visitors to explore the platform with view-only access. Guest users can browse
                  entities, messages, sessions, and the knowledge graph, but cannot create, edit, or delete anything.
                </p>

                {guestSettings && (
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-cm-coffee">Status:</span>
                      <span className={cn(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        guestSettings.enabled
                          ? "bg-green-100 text-green-700"
                          : "bg-cm-sand text-cm-coffee"
                      )}>
                        {guestSettings.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-cm-coffee">Email:</span>
                      <code className="text-xs bg-cm-sand/50 px-1.5 py-0.5 rounded font-mono">
                        {guestSettings.email}
                      </code>
                    </div>
                    {guestSettings.exists && guestSettings.user_key && (
                      <div className="flex items-center gap-2">
                        <span className="text-cm-coffee">User:</span>
                        <code className="text-xs bg-cm-sand/50 px-1.5 py-0.5 rounded font-mono">
                          {guestSettings.user_key}
                        </code>
                      </div>
                    )}
                    {guestSettings.created_at && (
                      <div className="flex items-center gap-2">
                        <span className="text-cm-coffee">Created:</span>
                        <span className="text-cm-charcoal">
                          {new Date(guestSettings.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="ml-6">
                <button
                  onClick={toggleGuestAccess}
                  disabled={isTogglingGuest}
                  className={cn(
                    "relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
                    guestSettings?.enabled ? "bg-cm-success" : "bg-cm-sand"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform",
                      guestSettings?.enabled ? "translate-x-7" : "translate-x-1"
                    )}
                  />
                </button>
              </div>
            </div>

            {/* Info box */}
            <div className="mt-6 p-4 bg-cm-sand/30 rounded-lg">
              <h3 className="text-sm font-medium text-cm-charcoal mb-2">How it works</h3>
              <ul className="text-xs text-cm-coffee space-y-1">
                <li>• When enabled, a "Access as Guest" button appears on the login page</li>
                <li>• Guest users see a banner indicating view-only mode</li>
                <li>• All create, edit, and delete buttons are disabled for guests</li>
                <li>• API endpoints return 403 for any write operations</li>
                <li>• MCP tools return read-only mode messages for write attempts</li>
              </ul>
            </div>
          </div>

          {/* Future settings sections can be added here */}
          <div className="text-center py-8 text-sm text-cm-coffee">
            More settings coming soon...
          </div>
        </div>
      )}
    </div>
  );
}
