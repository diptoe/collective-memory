'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Project, Team, Domain } from '@/types';

export default function AdminProjectsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<{
    total: number;
    active: number;
    archived: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<{ status?: string; team_key?: string; domain_key?: string }>({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [teams, setTeams] = useState<Team[]>([]);
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

  // Load projects, stats, and teams
  useEffect(() => {
    if (currentUser?.role === 'admin' || currentUser?.role === 'domain_admin') {
      loadData();
    }
  }, [currentUser, filter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const requests: Promise<unknown>[] = [
        api.projects.list({ ...filter, include_teams: 'true' }),
        api.teams.list(),
      ];

      // Load domains for admin users
      if (isAdmin) {
        requests.push(api.domains.list());
      }

      const responses = await Promise.all(requests);
      const [projectsResponse, teamsResponse] = responses as [
        Awaited<ReturnType<typeof api.projects.list>>,
        Awaited<ReturnType<typeof api.teams.list>>,
      ];

      if (projectsResponse.success && projectsResponse.data) {
        const projectsList = projectsResponse.data.projects;
        setProjects(projectsList);
        // Calculate stats from the list
        const active = projectsList.filter((p) => p.status === 'active').length;
        const archived = projectsList.filter((p) => p.status === 'archived').length;
        setStats({
          total: projectsList.length,
          active,
          archived,
        });
      }
      if (teamsResponse.success && teamsResponse.data) {
        setTeams(teamsResponse.data.teams);
      }

      // Set domains for admin users
      if (isAdmin && responses[2]) {
        const domainsResponse = responses[2] as Awaited<ReturnType<typeof api.domains.list>>;
        if (domainsResponse.success && domainsResponse.data) {
          setDomains(domainsResponse.data.domains);
        }
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
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
        <h1 className="text-2xl font-semibold text-cm-charcoal">Project Management</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
        >
          Create Project
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard label="Total Projects" value={stats.total} />
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
        <select
          value={filter.team_key || ''}
          onChange={(e) => setFilter((prev) => ({ ...prev, team_key: e.target.value || undefined }))}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="">All teams</option>
          {teams.map((team) => (
            <option key={team.team_key} value={team.team_key}>
              {team.name}
            </option>
          ))}
        </select>
      </div>

      {/* Projects Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Project</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Repository</th>
              {isAdmin && (
                <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Domain</th>
              )}
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Teams</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={isAdmin ? 6 : 5} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading projects...
                </td>
              </tr>
            ) : projects.length === 0 ? (
              <tr>
                <td colSpan={isAdmin ? 6 : 5} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No projects found. Create your first project to track a repository.
                </td>
              </tr>
            ) : (
              projects.map((project) => (
                <tr key={project.project_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm font-medium text-cm-charcoal">{project.name}</span>
                      {project.description && (
                        <p className="text-xs text-cm-coffee mt-0.5 line-clamp-1">{project.description}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {project.repository_url ? (
                      <div className="flex items-center gap-2">
                        {project.repository_type && (
                          <RepoTypeIcon type={project.repository_type} />
                        )}
                        <div>
                          <span className="text-sm text-cm-charcoal font-mono">
                            {project.repository_owner}/{project.repository_name}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <span className="text-xs text-cm-coffee">No repository</span>
                    )}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3">
                      <span className="text-sm text-cm-charcoal">
                        {getDomainName(project.domain_key)}
                      </span>
                    </td>
                  )}
                  <td className="px-4 py-3 text-sm text-cm-charcoal">
                    {project.teams?.length ?? 0}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        project.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {project.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/admin/projects/${project.project_key}`}
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
        <CreateProjectModal
          isAdmin={currentUser?.role === 'admin'}
          userDomainKey={currentUser?.domain_key}
          teams={teams}
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
  // Simple icon based on repository type
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

function CreateProjectModal({
  isAdmin,
  userDomainKey,
  teams,
  onClose,
  onCreated,
}: {
  isAdmin?: boolean;
  userDomainKey?: string;
  teams: Team[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [domainKey, setDomainKey] = useState(userDomainKey || '');
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedTeamKey, setSelectedTeamKey] = useState('');
  const [teamRole, setTeamRole] = useState<'owner' | 'contributor' | 'viewer'>('contributor');
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
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    if (isAdmin && !domainKey) {
      setError('Please select a domain');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      // Create the project
      const response = await api.projects.create({
        name: name.trim(),
        description: description.trim() || undefined,
        repository_url: repositoryUrl.trim() || undefined,
        domain_key: isAdmin ? domainKey : undefined,
      });

      if (response.success && response.data) {
        const project = response.data.project;

        // Add team association if selected
        if (selectedTeamKey && project) {
          await api.projects.addTeam(project.project_key, {
            team_key: selectedTeamKey,
            role: teamRole,
          });
        }

        onCreated();
      } else {
        setError(response.msg || 'Failed to create project');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Create Project</h2>

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
                placeholder="My Project"
              />
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
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Repository URL</label>
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
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Associate with Team (Optional)</label>
              <div className="flex gap-2">
                <select
                  value={selectedTeamKey}
                  onChange={(e) => setSelectedTeamKey(e.target.value)}
                  className="flex-1 px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">No team</option>
                  {teams.map((team) => (
                    <option key={team.team_key} value={team.team_key}>
                      {team.name}
                    </option>
                  ))}
                </select>
                {selectedTeamKey && (
                  <select
                    value={teamRole}
                    onChange={(e) => setTeamRole(e.target.value as 'owner' | 'contributor' | 'viewer')}
                    className="w-32 px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                  >
                    <option value="owner">Owner</option>
                    <option value="contributor">Contributor</option>
                    <option value="viewer">Viewer</option>
                  </select>
                )}
              </div>
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
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
