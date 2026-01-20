'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Project, TeamProject, TeamProjectRole, Team, Repository, Domain } from '@/types';

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

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectKey = params.key as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [project, setProject] = useState<Project | null>(null);
  const [teamProjects, setTeamProjects] = useState<TeamProject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [actionInProgress, setActionInProgress] = useState('');
  const [showAddTeamModal, setShowAddTeamModal] = useState(false);
  const [showLinkRepositoryModal, setShowLinkRepositoryModal] = useState(false);
  const [showMoveDomainModal, setShowMoveDomainModal] = useState(false);
  const [projectRepositories, setProjectRepositories] = useState<{ project_repository_key: string; repository: Repository; created_at: string }[]>([]);

  // Edit form state
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editRepositoryUrl, setEditRepositoryUrl] = useState('');

  // Redirect if not admin or domain_admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load project data
  useEffect(() => {
    if ((currentUser?.role === 'admin' || currentUser?.role === 'domain_admin') && projectKey) {
      loadProjectData();
    }
  }, [currentUser, projectKey]);

  const loadProjectData = async () => {
    setIsLoading(true);
    try {
      const [projectResponse, teamsResponse, repositoriesResponse] = await Promise.all([
        api.projects.get(projectKey),
        api.projects.teams(projectKey),
        api.projects.repositories(projectKey),
      ]);

      if (projectResponse.success && projectResponse.data) {
        const proj = projectResponse.data.project;
        setProject(proj);
        setEditName(proj.name);
        setEditDescription(proj.description || '');
        setEditRepositoryUrl(proj.repository_url || '');
      } else {
        setError('Project not found');
      }

      if (teamsResponse.success && teamsResponse.data) {
        setTeamProjects(teamsResponse.data.teams);
      }

      if (repositoriesResponse.success && repositoriesResponse.data) {
        setProjectRepositories(repositoriesResponse.data.repositories);
      }
    } catch (err) {
      setError('Failed to load project');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!project) return;
    setActionInProgress('save');
    setError('');

    try {
      const response = await api.projects.update(projectKey, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        repository_url: editRepositoryUrl.trim() || undefined,
      });

      if (response.success && response.data) {
        setProject(response.data.project);
        setIsEditing(false);
      } else {
        setError(response.msg || 'Failed to update project');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update project');
    } finally {
      setActionInProgress('');
    }
  };

  const toggleStatus = async () => {
    if (!project) return;
    setActionInProgress('status');
    setError('');

    const newStatus = project.status === 'active' ? 'archived' : 'active';

    try {
      const response = await api.projects.update(projectKey, { status: newStatus });
      if (response.success && response.data) {
        setProject(response.data.project);
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

  const updateTeamRole = async (teamKey: string, newRole: TeamProjectRole) => {
    setActionInProgress(`role-${teamKey}`);
    setError('');

    try {
      const response = await api.projects.updateTeam(projectKey, teamKey, { role: newRole });
      if (response.success && response.data?.team_project) {
        setTeamProjects(prev => prev.map(tp =>
          tp.team_key === teamKey ? { ...tp, ...response.data!.team_project } : tp
        ));
      } else {
        setError(response.msg || 'Failed to update team role');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update team role');
    } finally {
      setActionInProgress('');
    }
  };

  const removeTeam = async (teamKey: string) => {
    if (!confirm('Are you sure you want to remove this team from the project?')) return;

    setActionInProgress(`remove-${teamKey}`);
    setError('');

    try {
      const response = await api.projects.removeTeam(projectKey, teamKey);
      if (response.success) {
        setTeamProjects(teamProjects.filter(tp => tp.team_key !== teamKey));
      } else {
        setError(response.msg || 'Failed to remove team');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to remove team');
    } finally {
      setActionInProgress('');
    }
  };

  const unlinkRepository = async (repositoryKey: string) => {
    if (!confirm('Are you sure you want to unlink this repository from the project?')) return;

    setActionInProgress(`unlink-repo-${repositoryKey}`);
    setError('');

    try {
      const response = await api.projects.removeRepository(projectKey, repositoryKey);
      if (response.success) {
        setProjectRepositories(projectRepositories.filter(pr => pr.repository.repository_key !== repositoryKey));
      } else {
        setError(response.msg || 'Failed to unlink repository');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to unlink repository');
    } finally {
      setActionInProgress('');
    }
  };

  if (!isAuthenticated || (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin')) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-cm-coffee">Loading project...</p>
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
        <Link href="/admin/projects" className="mt-4 inline-block text-cm-terracotta hover:underline">
          Back to Projects
        </Link>
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/admin/projects" className="text-cm-coffee hover:text-cm-charcoal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-lg">
            <RepoTypeIcon type={project.repository_type || ''} large />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">{project.name}</h1>
            {project.repository_owner && project.repository_name && (
              <p className="text-sm text-cm-coffee font-mono">
                {project.repository_owner}/{project.repository_name}
              </p>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Project Details */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Project Details</h2>
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
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">Repository URL</label>
              <input
                type="text"
                value={editRepositoryUrl}
                onChange={(e) => setEditRepositoryUrl(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="https://github.com/owner/repo"
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
                  setEditName(project.name);
                  setEditDescription(project.description || '');
                  setEditRepositoryUrl(project.repository_url || '');
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
              <p className="text-sm text-cm-coffee">Project Key</p>
              <p className="text-cm-charcoal font-mono text-sm">{project.project_key}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Status</p>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    project.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {project.status}
                </span>
                <button
                  onClick={toggleStatus}
                  disabled={actionInProgress === 'status'}
                  className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                >
                  {actionInProgress === 'status'
                    ? 'Updating...'
                    : project.status === 'active'
                    ? 'Archive'
                    : 'Activate'}
                </button>
              </div>
            </div>
            {/* Move to Domain - System Admins Only */}
            {currentUser?.role === 'admin' && (
              <div>
                <p className="text-sm text-cm-coffee">Domain</p>
                <div className="flex items-center gap-2">
                  <span className="text-cm-charcoal font-mono text-sm">{project.domain_key}</span>
                  <button
                    onClick={() => setShowMoveDomainModal(true)}
                    className="text-xs text-cm-terracotta hover:underline"
                  >
                    Move to Another Domain
                  </button>
                </div>
              </div>
            )}
            <div>
              <p className="text-sm text-cm-coffee">Name</p>
              <p className="text-cm-charcoal">{project.name}</p>
            </div>
            {project.repository_type && (
              <div>
                <p className="text-sm text-cm-coffee">Repository Type</p>
                <p className="text-cm-charcoal capitalize">{project.repository_type}</p>
              </div>
            )}
            {project.description && (
              <div className="col-span-2">
                <p className="text-sm text-cm-coffee">Description</p>
                <p className="text-cm-charcoal">{project.description}</p>
              </div>
            )}
            {project.repository_url && (
              <div className="col-span-2">
                <p className="text-sm text-cm-coffee">Repository URL</p>
                <a
                  href={project.repository_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cm-terracotta hover:underline font-mono text-sm break-all"
                >
                  {project.repository_url}
                </a>
              </div>
            )}
            <div>
              <p className="text-sm text-cm-coffee">Created</p>
              <p className="text-cm-charcoal">{formatDateTime(project.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Updated</p>
              <p className="text-cm-charcoal">{formatDateTime(project.updated_at)}</p>
            </div>
            {project.entity_key && (
              <div className="col-span-2">
                <p className="text-sm text-cm-coffee">Linked Entity</p>
                <Link
                  href={`/entities/${project.entity_key}`}
                  className="text-cm-terracotta hover:underline font-mono text-sm"
                >
                  {project.entity_key}
                </Link>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Associated Teams */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">
            Associated Teams ({teamProjects.length})
          </h2>
          <button
            onClick={() => setShowAddTeamModal(true)}
            className="px-3 py-1.5 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90"
          >
            Add Team
          </button>
        </div>

        {teamProjects.length === 0 ? (
          <p className="text-sm text-cm-coffee">No teams associated with this project yet. Add teams to enable collaboration.</p>
        ) : (
          <div className="space-y-3">
            {teamProjects.map((tp) => (
              <div
                key={tp.team_project_key}
                className="flex items-center justify-between p-3 bg-cm-cream rounded-md"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm">
                    <span>{"👥"}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-cm-charcoal">
                      {tp.team?.name || 'Unknown Team'}
                    </p>
                    <p className="text-xs text-cm-coffee">
                      Added {formatDateTime(tp.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={tp.role}
                    onChange={(e) => updateTeamRole(tp.team_key, e.target.value as TeamProjectRole)}
                    disabled={actionInProgress === `role-${tp.team_key}`}
                    className="px-2 py-1 text-xs border border-cm-sand rounded-md bg-cm-ivory text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 disabled:opacity-50"
                  >
                    <option value="owner">Owner</option>
                    <option value="contributor">Contributor</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  <button
                    onClick={() => removeTeam(tp.team_key)}
                    disabled={actionInProgress === `remove-${tp.team_key}`}
                    className="text-xs text-red-600 hover:underline disabled:opacity-50"
                  >
                    {actionInProgress === `remove-${tp.team_key}` ? 'Removing...' : 'Remove'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Linked Repositories */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mt-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">
            Linked Repositories ({projectRepositories.length})
          </h2>
          <button
            onClick={() => setShowLinkRepositoryModal(true)}
            className="px-3 py-1.5 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90"
          >
            Link Repository
          </button>
        </div>

        {projectRepositories.length === 0 ? (
          <p className="text-sm text-cm-coffee">No repositories linked to this project yet. Link a repository to enable code tracking.</p>
        ) : (
          <div className="space-y-3">
            {projectRepositories.map((pr) => (
              <div
                key={pr.project_repository_key}
                className="flex items-center justify-between p-3 bg-cm-cream rounded-md"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm">
                    <RepoTypeIcon type={pr.repository.repository_type || ''} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-cm-charcoal">
                      {pr.repository.name}
                    </p>
                    {pr.repository.repository_owner && pr.repository.repository_name && (
                      <p className="text-xs text-cm-coffee font-mono">
                        {pr.repository.repository_owner}/{pr.repository.repository_name}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href={`/admin/repositories/${pr.repository.repository_key}`}
                    className="text-xs text-cm-terracotta hover:underline"
                  >
                    View Repository
                  </Link>
                  <button
                    onClick={() => unlinkRepository(pr.repository.repository_key)}
                    disabled={actionInProgress === `unlink-repo-${pr.repository.repository_key}`}
                    className="text-xs text-red-600 hover:underline disabled:opacity-50"
                  >
                    {actionInProgress === `unlink-repo-${pr.repository.repository_key}` ? 'Unlinking...' : 'Unlink'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Team Modal */}
      {showAddTeamModal && (
        <AddTeamModal
          projectKey={projectKey}
          existingTeamKeys={teamProjects.map(tp => tp.team_key)}
          onClose={() => setShowAddTeamModal(false)}
          onAdded={() => {
            setShowAddTeamModal(false);
            loadProjectData();
          }}
        />
      )}

      {/* Link Repository Modal */}
      {showLinkRepositoryModal && (
        <LinkRepositoryModal
          projectKey={projectKey}
          existingRepositoryKeys={projectRepositories.map(pr => pr.repository.repository_key)}
          onClose={() => setShowLinkRepositoryModal(false)}
          onLinked={() => {
            setShowLinkRepositoryModal(false);
            loadProjectData();
          }}
        />
      )}

      {/* Move to Domain Modal - System Admins Only */}
      {showMoveDomainModal && (
        <MoveDomainModal
          project={project}
          onClose={() => setShowMoveDomainModal(false)}
          onMoved={() => {
            setShowMoveDomainModal(false);
            loadProjectData();
          }}
        />
      )}
    </div>
  );
}

function RepoTypeIcon({ type, large }: { type: string; large?: boolean }) {
  const icons: Record<string, string> = {
    github: 'GH',
    gitlab: 'GL',
    bitbucket: 'BB',
    azure: 'AZ',
    codecommit: 'CC',
  };

  if (large) {
    return (
      <span className="text-lg font-medium">
        {icons[type] || 'PR'}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-cm-sand text-xs font-medium text-cm-charcoal">
      {icons[type] || '?'}
    </span>
  );
}

function AddTeamModal({
  projectKey,
  existingTeamKeys,
  onClose,
  onAdded,
}: {
  projectKey: string;
  existingTeamKeys: string[];
  onClose: () => void;
  onAdded: () => void;
}) {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeamKey, setSelectedTeamKey] = useState('');
  const [role, setRole] = useState<TeamProjectRole>('contributor');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      const response = await api.teams.list({ status: 'active' });
      if (response.success && response.data) {
        // Filter out teams that are already associated
        const availableTeams = response.data.teams.filter(
          t => !existingTeamKeys.includes(t.team_key)
        );
        setTeams(availableTeams);
      }
    } catch (err) {
      setError('Failed to load teams');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeamKey) {
      setError('Please select a team');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.projects.addTeam(projectKey, {
        team_key: selectedTeamKey,
        role,
      });

      if (response.success) {
        onAdded();
      } else {
        setError(response.msg || 'Failed to add team');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to add team');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Add Team to Project</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <p className="text-sm text-cm-coffee">Loading teams...</p>
        ) : teams.length === 0 ? (
          <p className="text-sm text-cm-coffee">No available teams to add</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Team</label>
                <select
                  value={selectedTeamKey}
                  onChange={(e) => setSelectedTeamKey(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">Select a team...</option>
                  {teams.map((team) => (
                    <option key={team.team_key} value={team.team_key}>
                      {team.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as TeamProjectRole)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="owner">Owner</option>
                  <option value="contributor">Contributor</option>
                  <option value="viewer">Viewer</option>
                </select>
                <p className="text-xs text-cm-coffee mt-1">
                  Owners have full control. Contributors can work on the project. Viewers can only read.
                </p>
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
                disabled={isSubmitting || !selectedTeamKey}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Adding...' : 'Add Team'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function LinkRepositoryModal({
  projectKey,
  existingRepositoryKeys,
  onClose,
  onLinked,
}: {
  projectKey: string;
  existingRepositoryKeys: string[];
  onClose: () => void;
  onLinked: () => void;
}) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepositoryKey, setSelectedRepositoryKey] = useState('');
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState<'existing' | 'new'>('existing');

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      const response = await api.repositories.list({ status: 'active' });
      if (response.success && response.data) {
        // Filter out repositories that are already linked
        const availableRepositories = response.data.repositories.filter(
          r => !existingRepositoryKeys.includes(r.repository_key)
        );
        setRepositories(availableRepositories);
      }
    } catch (err) {
      setError('Failed to load repositories');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (mode === 'existing' && !selectedRepositoryKey) {
      setError('Please select a repository');
      return;
    }
    if (mode === 'new' && !repositoryUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const data = mode === 'existing'
        ? { repository_key: selectedRepositoryKey }
        : { repository_url: repositoryUrl.trim() };

      const response = await api.projects.addRepository(projectKey, data);

      if (response.success) {
        onLinked();
      } else {
        setError(response.msg || 'Failed to link repository');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to link repository');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Link Repository to Project</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Mode Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => setMode('existing')}
            className={`flex-1 px-3 py-2 text-sm rounded-md ${
              mode === 'existing'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-charcoal hover:bg-cm-sand/80'
            }`}
          >
            Existing Repository
          </button>
          <button
            type="button"
            onClick={() => setMode('new')}
            className={`flex-1 px-3 py-2 text-sm rounded-md ${
              mode === 'new'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-charcoal hover:bg-cm-sand/80'
            }`}
          >
            New Repository
          </button>
        </div>

        {mode === 'existing' ? (
          isLoading ? (
            <p className="text-sm text-cm-coffee">Loading repositories...</p>
          ) : repositories.length === 0 ? (
            <div className="text-sm text-cm-coffee">
              <p>No available repositories to link.</p>
              <button
                type="button"
                onClick={() => setMode('new')}
                className="text-cm-terracotta hover:underline mt-2"
              >
                Create a new repository instead
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-cm-charcoal mb-1">Repository</label>
                  <select
                    value={selectedRepositoryKey}
                    onChange={(e) => setSelectedRepositoryKey(e.target.value)}
                    className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                  >
                    <option value="">Select a repository...</option>
                    {repositories.map((repository) => (
                      <option key={repository.repository_key} value={repository.repository_key}>
                        {repository.name} ({repository.repository_owner}/{repository.repository_name})
                      </option>
                    ))}
                  </select>
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
                  disabled={isSubmitting || !selectedRepositoryKey}
                  className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
                >
                  {isSubmitting ? 'Linking...' : 'Link Repository'}
                </button>
              </div>
            </form>
          )
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
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
                  A new repository will be created and linked to this project
                </p>
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
                disabled={isSubmitting || !repositoryUrl.trim()}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Creating & Linking...' : 'Create & Link Repository'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function MoveDomainModal({
  project,
  onClose,
  onMoved,
}: {
  project: Project;
  onClose: () => void;
  onMoved: () => void;
}) {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomainKey, setSelectedDomainKey] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [moveSummary, setMoveSummary] = useState<{
    repositories_moved: number;
    work_sessions_updated: number;
    team_associations_removed: number;
    agents_cleared: number;
  } | null>(null);

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      const response = await api.domains.list({ status: 'active' });
      if (response.success && response.data) {
        // Filter out the current domain
        const availableDomains = response.data.domains.filter(
          d => d.domain_key !== project.domain_key
        );
        setDomains(availableDomains);
      }
    } catch (err) {
      setError('Failed to load domains');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDomainKey) {
      setError('Please select a domain');
      return;
    }

    const selectedDomain = domains.find(d => d.domain_key === selectedDomainKey);
    if (!confirm(`Are you sure you want to move "${project.name}" to domain "${selectedDomain?.name || selectedDomainKey}"?\n\nThis action will:\n• Remove all team associations\n• Move linked repositories to the new domain\n• Update work sessions\n• Clear agent project context`)) {
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.projects.moveToDomain(project.project_key, selectedDomainKey);

      if (response.success && response.data) {
        setMoveSummary(response.data.summary);
      } else {
        setError(response.msg || 'Failed to move project');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to move project');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show success summary
  if (moveSummary) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-cm-charcoal">Project Moved Successfully</h2>
          </div>

          <div className="bg-cm-cream rounded-md p-4 mb-4">
            <h3 className="text-sm font-medium text-cm-charcoal mb-2">Migration Summary</h3>
            <ul className="text-sm text-cm-coffee space-y-1">
              <li>• <strong>{moveSummary.team_associations_removed}</strong> team association(s) removed</li>
              <li>• <strong>{moveSummary.repositories_moved}</strong> repository(ies) moved</li>
              <li>• <strong>{moveSummary.work_sessions_updated}</strong> work session(s) updated</li>
              <li>• <strong>{moveSummary.agents_cleared}</strong> agent(s) cleared</li>
            </ul>
          </div>

          <p className="text-sm text-cm-coffee mb-4">
            The project has been moved to the new domain. You may need to re-add team associations in the new domain.
          </p>

          <div className="flex justify-end">
            <button
              onClick={onMoved}
              className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Move Project to Another Domain</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Warning Box */}
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-md">
          <div className="flex items-start gap-2">
            <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="text-sm text-amber-800">
              <p className="font-medium mb-1">This action will:</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li>Remove all team associations (teams are domain-specific)</li>
                <li>Move linked repositories to the new domain</li>
                <li>Update work sessions to the new domain</li>
                <li>Clear project context from agents</li>
              </ul>
            </div>
          </div>
        </div>

        {isLoading ? (
          <p className="text-sm text-cm-coffee">Loading domains...</p>
        ) : domains.length === 0 ? (
          <p className="text-sm text-cm-coffee">No other domains available to move to.</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Current Domain</label>
                <p className="text-sm text-cm-coffee font-mono">{project.domain_key}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Target Domain</label>
                <select
                  value={selectedDomainKey}
                  onChange={(e) => setSelectedDomainKey(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">Select a domain...</option>
                  {domains.map((domain) => (
                    <option key={domain.domain_key} value={domain.domain_key}>
                      {domain.name} ({domain.domain_key})
                    </option>
                  ))}
                </select>
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
                disabled={isSubmitting || !selectedDomainKey}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Moving Project...' : 'Move Project'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
