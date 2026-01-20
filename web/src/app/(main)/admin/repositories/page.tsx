'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Repository, Domain } from '@/types';

export default function AdminRepositoriesPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [stats, setStats] = useState<{
    total: number;
    active: number;
    archived: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<{ status?: string; domain_key?: string }>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [domains, setDomains] = useState<Domain[]>([]);
  const isAdmin = currentUser?.role === 'admin';

  // Redirect if not admin or domain_admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load repositories and stats
  useEffect(() => {
    if (currentUser?.role === 'admin' || currentUser?.role === 'domain_admin') {
      loadData();
    }
  }, [currentUser, filter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const requests: Promise<unknown>[] = [
        api.repositories.list({ ...filter, include_projects: true }),
      ];

      // Load domains for admin users
      if (isAdmin) {
        requests.push(api.domains.list());
      }

      const responses = await Promise.all(requests);
      const [repositoriesResponse] = responses as [
        Awaited<ReturnType<typeof api.repositories.list>>,
      ];

      if (repositoriesResponse.success && repositoriesResponse.data) {
        const repositoriesList = repositoriesResponse.data.repositories;
        setRepositories(repositoriesList);
        // Calculate stats from the list
        const active = repositoriesList.filter((r) => r.status === 'active').length;
        const archived = repositoriesList.filter((r) => r.status === 'archived').length;
        setStats({
          total: repositoriesList.length,
          active,
          archived,
        });
      }

      // Set domains for admin users
      if (isAdmin && responses[1]) {
        const domainsResponse = responses[1] as Awaited<ReturnType<typeof api.domains.list>>;
        if (domainsResponse.success && domainsResponse.data) {
          setDomains(domainsResponse.data.domains);
        }
      }
    } catch (err) {
      console.error('Failed to load repositories:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated || (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin')) {
    return null;
  }

  // Get domain name for display
  const getDomainName = (domainKey: string | undefined) => {
    if (!domainKey) return 'Unknown';
    const domain = domains.find((d) => d.domain_key === domainKey);
    return domain?.name || domainKey;
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-cm-charcoal">Repository Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
        >
          Create Repository
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard label="Total Repositories" value={stats.total} />
          <StatCard label="Active" value={stats.active} color="green" />
          <StatCard label="Archived" value={stats.archived} color="gray" />
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        {isAdmin && domains.length > 0 && (
          <select
            value={filter.domain_key || ''}
            onChange={(e) => setFilter((prev) => ({ ...prev, domain_key: e.target.value || undefined }))}
            className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
          >
            <option value="">All domains</option>
            {domains.map((domain) => (
              <option key={domain.domain_key} value={domain.domain_key}>
                {domain.name}
              </option>
            ))}
          </select>
        )}
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

      {/* Repositories Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Repository</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Type</th>
              {isAdmin && (
                <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Domain</th>
              )}
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Projects</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={isAdmin ? 6 : 5} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading repositories...
                </td>
              </tr>
            ) : repositories.length === 0 ? (
              <tr>
                <td colSpan={isAdmin ? 6 : 5} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No repositories found. Create your first repository to track code.
                </td>
              </tr>
            ) : (
              repositories.map((repository) => (
                <tr key={repository.repository_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm font-medium text-cm-charcoal">{repository.name}</span>
                      {repository.repository_owner && repository.repository_name && (
                        <p className="text-xs text-cm-coffee font-mono mt-0.5">
                          {repository.repository_owner}/{repository.repository_name}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {repository.repository_type && (
                      <RepoTypeIcon type={repository.repository_type} />
                    )}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3">
                      <span className="text-sm text-cm-charcoal">
                        {getDomainName(repository.domain_key)}
                      </span>
                    </td>
                  )}
                  <td className="px-4 py-3 text-sm text-cm-charcoal">
                    {repository.projects?.length ?? 0}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        repository.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {repository.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/admin/repositories/${repository.repository_key}`}
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
        <CreateRepositoryModal
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

function RepoTypeIcon({ type }: { type: string }) {
  const icons: Record<string, string> = {
    github: 'GH',
    gitlab: 'GL',
    bitbucket: 'BB',
    azure: 'AZ',
    codecommit: 'CC',
  };

  return (
    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-cm-sand text-xs font-medium text-cm-charcoal">
      {icons[type] || '?'}
    </span>
  );
}

function CreateRepositoryModal({
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
  const [description, setDescription] = useState('');
  const [repositoryUrl, setRepositoryUrl] = useState('');
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repositoryUrl.trim()) {
      setError('Repository URL is required');
      return;
    }

    if (isAdmin && !domainKey) {
      setError('Please select a domain');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.repositories.create({
        repository_url: repositoryUrl.trim(),
        name: name.trim() || undefined,
        description: description.trim() || undefined,
        domain_key: isAdmin ? domainKey : undefined,
      });

      if (response.success) {
        onCreated();
      } else {
        setError(response.msg || 'Failed to create repository');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to create repository');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Create Repository</h2>

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
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Repository URL *</label>
              <input
                type="text"
                value={repositoryUrl}
                onChange={(e) => setRepositoryUrl(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="https://github.com/owner/repo"
              />
              <p className="text-xs text-cm-coffee mt-1">
                Supports GitHub, GitLab, Bitbucket, Azure DevOps, CodeCommit
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Name (optional)</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="Defaults to repository name from URL"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Description (optional)</label>
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
              {isSubmitting ? 'Creating...' : 'Create Repository'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
