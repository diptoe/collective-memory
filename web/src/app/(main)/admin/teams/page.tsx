'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Team, Domain } from '@/types';

export default function AdminTeamsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [teams, setTeams] = useState<Team[]>([]);
  const [stats, setStats] = useState<{
    total: number;
    active: number;
    archived: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<{ status?: string }>({});
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Redirect if not admin or domain_admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load teams and stats
  useEffect(() => {
    if (currentUser?.role === 'admin' || currentUser?.role === 'domain_admin') {
      loadData();
    }
  }, [currentUser, filter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [teamsResponse, statsResponse] = await Promise.all([
        api.teams.list(filter),
        api.teams.stats(),
      ]);

      if (teamsResponse.success && teamsResponse.data) {
        setTeams(teamsResponse.data.teams);
      }
      if (statsResponse.success && statsResponse.data) {
        setStats(statsResponse.data);
      }
    } catch (err) {
      console.error('Failed to load teams:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated || (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin')) {
    return null;
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-cm-charcoal">Team Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
        >
          Create Team
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard label="Total Teams" value={stats.total} />
          <StatCard label="Active" value={stats.active} color="green" />
          <StatCard label="Archived" value={stats.archived} color="gray" />
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <select
          value={filter.status || ''}
          onChange={(e) => setFilter((prev) => ({ ...prev, status: e.target.value || undefined }))}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Teams Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Team</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Slug</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Members</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading teams...
                </td>
              </tr>
            ) : teams.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No teams found. Create your first team to organize your users.
                </td>
              </tr>
            ) : (
              teams.map((team) => (
                <tr key={team.team_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm font-medium text-cm-charcoal">{team.name}</span>
                      {team.description && (
                        <p className="text-xs text-cm-coffee mt-0.5">{team.description}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee font-mono">{team.slug}</td>
                  <td className="px-4 py-3 text-sm text-cm-charcoal">{team.member_count ?? 0}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        team.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {team.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/admin/teams/${team.team_key}`}
                      className="text-sm text-cm-terracotta hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateTeamModal
          isAdmin={currentUser?.role === 'admin'}
          userDomainKey={currentUser?.domain_key}
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            loadData();
          }}
        />
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
  color?: 'green' | 'gray' | 'blue';
}) {
  const colorClasses = {
    green: 'text-green-600',
    gray: 'text-gray-600',
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

function CreateTeamModal({
  isAdmin,
  userDomainKey,
  onClose,
  onCreated,
}: {
  isAdmin?: boolean;
  userDomainKey?: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [domainKey, setDomainKey] = useState(userDomainKey || '');
  const [domains, setDomains] = useState<Domain[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Load domains for admin users
  useEffect(() => {
    if (isAdmin) {
      api.domains.list().then((response) => {
        if (response.success && response.data) {
          setDomains(response.data.domains);
        }
      });
    }
  }, [isAdmin]);

  // Auto-generate slug from name
  useEffect(() => {
    if (name && !slug) {
      setSlug(name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''));
    }
  }, [name]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) {
      setError('Name and slug are required');
      return;
    }

    if (isAdmin && !domainKey) {
      setError('Please select a domain');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.teams.create({
        name: name.trim(),
        slug: slug.trim().toLowerCase(),
        description: description.trim() || undefined,
        domain_key: isAdmin ? domainKey : undefined,
      });

      if (response.success) {
        onCreated();
      } else {
        setError(response.msg || 'Failed to create team');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to create team');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Create Team</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {isAdmin && (
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Domain</label>
                <select
                  value={domainKey}
                  onChange={(e) => setDomainKey(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">Select a domain...</option>
                  {domains.map((domain) => (
                    <option key={domain.domain_key} value={domain.domain_key}>
                      {domain.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="Engineering Team"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Slug</label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal font-mono focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="engineering"
              />
              <p className="text-xs text-cm-coffee mt-1">Unique identifier for the team</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="Optional description..."
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-cm-coffee hover:text-cm-charcoal"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Creating...' : 'Create Team'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
