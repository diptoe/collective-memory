'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Domain, User } from '@/types';

function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
}

export default function DomainDetailPage() {
  const router = useRouter();
  const params = useParams();
  const domainKey = params.key as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [domain, setDomain] = useState<Domain | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [actionInProgress, setActionInProgress] = useState('');

  // Edit form state
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load domain data
  useEffect(() => {
    if (currentUser?.role === 'admin' && domainKey) {
      loadDomainData();
    }
  }, [currentUser, domainKey]);

  const loadDomainData = async () => {
    setIsLoading(true);
    try {
      const [domainResponse, usersResponse] = await Promise.all([
        api.domains.get(domainKey),
        api.domains.users(domainKey),
      ]);

      if (domainResponse.success && domainResponse.data) {
        setDomain(domainResponse.data.domain);
        setEditName(domainResponse.data.domain.name);
        setEditDescription(domainResponse.data.domain.description || '');
      } else {
        setError('Domain not found');
      }

      if (usersResponse.success && usersResponse.data) {
        setUsers(usersResponse.data.users);
      }
    } catch (err) {
      setError('Failed to load domain');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!domain) return;
    setActionInProgress('save');
    setError('');

    try {
      const response = await api.domains.update(domainKey, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      });

      if (response.success && response.data) {
        setDomain(response.data.domain);
        setIsEditing(false);
      } else {
        setError(response.msg || 'Failed to update domain');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update domain');
    } finally {
      setActionInProgress('');
    }
  };

  const toggleStatus = async () => {
    if (!domain) return;
    setActionInProgress('status');
    setError('');

    const newStatus = domain.status === 'active' ? 'suspended' : 'active';

    try {
      const response = await api.domains.update(domainKey, { status: newStatus });
      if (response.success && response.data) {
        setDomain(response.data.domain);
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

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-cm-coffee">Loading domain...</p>
      </div>
    );
  }

  if (error && !domain) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
        <Link href="/admin/domains" className="mt-4 inline-block text-cm-terracotta hover:underline">
          Back to Domains
        </Link>
      </div>
    );
  }

  if (!domain) return null;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/admin/domains" className="text-cm-coffee hover:text-cm-charcoal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-lg">
            <span>{"🌐"}</span>
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">{domain.name}</h1>
            <p className="text-sm text-cm-coffee font-mono">{domain.slug}</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Domain Details */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Domain Details</h2>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm text-cm-terracotta hover:underline"
            >
              Edit
            </button>
          )}
        </div>

        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Name</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Description</label>
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={actionInProgress === 'save'}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50"
              >
                {actionInProgress === 'save' ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setEditName(domain.name);
                  setEditDescription(domain.description || '');
                }}
                className="px-4 py-2 text-sm text-cm-coffee hover:text-cm-charcoal"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-cm-coffee">Domain Key</p>
              <p className="text-cm-charcoal font-mono text-sm">{domain.domain_key}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Slug</p>
              <p className="text-cm-charcoal font-mono">{domain.slug}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Name</p>
              <p className="text-cm-charcoal">{domain.name}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Status</p>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    domain.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {domain.status}
                </span>
                <button
                  onClick={toggleStatus}
                  disabled={actionInProgress === 'status'}
                  className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                >
                  {actionInProgress === 'status'
                    ? 'Updating...'
                    : domain.status === 'active'
                    ? 'Suspend'
                    : 'Activate'}
                </button>
              </div>
            </div>
            {domain.description && (
              <div className="col-span-2">
                <p className="text-sm text-cm-coffee">Description</p>
                <p className="text-cm-charcoal">{domain.description}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-cm-coffee">Owner</p>
              <p className="text-cm-charcoal">
                {domain.owner ? domain.owner.display_name : 'No owner assigned'}
              </p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Created</p>
              <p className="text-cm-charcoal">{formatDateTime(domain.created_at)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Users in Domain */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">
          Users ({users.length})
        </h2>

        {users.length === 0 ? (
          <p className="text-sm text-cm-coffee">No users in this domain</p>
        ) : (
          <div className="space-y-3">
            {users.map((user) => (
              <div
                key={user.user_key}
                className="flex items-center justify-between p-3 bg-cm-cream rounded-md"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm font-medium">
                    {user.initials}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-cm-charcoal">{user.display_name}</p>
                    <p className="text-xs text-cm-coffee">{user.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      user.role === 'admin'
                        ? 'bg-blue-100 text-blue-700'
                        : user.role === 'domain_admin'
                        ? 'bg-purple-100 text-purple-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {user.role === 'domain_admin' ? 'Domain Admin' : user.role}
                  </span>
                  <Link
                    href={`/admin/users/${user.user_key}`}
                    className="text-sm text-cm-terracotta hover:underline"
                  >
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
