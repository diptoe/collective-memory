'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Repository, Project } from '@/types';

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

export default function RepositoryDetailPage() {
  const router = useRouter();
  const params = useParams();
  const repositoryKey = params.key as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [projectRepositories, setProjectRepositories] = useState<{ project_repository_key: string; project: Project; created_at: string }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [actionInProgress, setActionInProgress] = useState('');
  const [showLinkProjectModal, setShowLinkProjectModal] = useState(false);

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

  // Load repository data
  useEffect(() => {
    if ((currentUser?.role === 'admin' || currentUser?.role === 'domain_admin') && repositoryKey) {
      loadRepositoryData();
    }
  }, [currentUser, repositoryKey]);

  const loadRepositoryData = async () => {
    setIsLoading(true);
    try {
      const [repositoryResponse, projectsResponse] = await Promise.all([
        api.repositories.get(repositoryKey),
        api.repositories.projects(repositoryKey),
      ]);

      if (repositoryResponse.success && repositoryResponse.data) {
        const repo = repositoryResponse.data.repository;
        setRepository(repo);
        setEditName(repo.name);
        setEditDescription(repo.description || '');
        setEditRepositoryUrl(repo.repository_url || '');
      } else {
        setError('Repository not found');
      }

      if (projectsResponse.success && projectsResponse.data) {
        setProjectRepositories(projectsResponse.data.projects);
      }
    } catch (err) {
      setError('Failed to load repository');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!repository) return;
    setActionInProgress('save');
    setError('');

    try {
      const response = await api.repositories.update(repositoryKey, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        repository_url: editRepositoryUrl.trim() || undefined,
      });

      if (response.success && response.data) {
        setRepository(response.data.repository);
        setIsEditing(false);
      } else {
        setError(response.msg || 'Failed to update repository');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update repository');
    } finally {
      setActionInProgress('');
    }
  };

  const toggleStatus = async () => {
    if (!repository) return;
    setActionInProgress('status');
    setError('');

    const newStatus = repository.status === 'active' ? 'archived' : 'active';

    try {
      const response = await api.repositories.update(repositoryKey, { status: newStatus });
      if (response.success && response.data) {
        setRepository(response.data.repository);
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

  const unlinkProject = async (projectKey: string) => {
    if (!confirm('Are you sure you want to unlink this project from the repository?')) return;

    setActionInProgress(`unlink-${projectKey}`);
    setError('');

    try {
      const response = await api.repositories.removeProject(repositoryKey, projectKey);
      if (response.success) {
        setProjectRepositories(projectRepositories.filter(pr => pr.project.project_key !== projectKey));
      } else {
        setError(response.msg || 'Failed to unlink project');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to unlink project');
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
        <p className="text-cm-coffee">Loading repository...</p>
      </div>
    );
  }

  if (error && !repository) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
        <Link href="/admin/repositories" className="mt-4 inline-block text-cm-terracotta hover:underline">
          Back to Repositories
        </Link>
      </div>
    );
  }

  if (!repository) return null;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/admin/repositories" className="text-cm-coffee hover:text-cm-charcoal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-lg">
            <RepoTypeIcon type={repository.repository_type || ''} large />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">{repository.name}</h1>
            {repository.repository_owner && repository.repository_name && (
              <p className="text-sm text-cm-coffee font-mono">
                {repository.repository_owner}/{repository.repository_name}
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

      {/* Repository Details */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Repository Details</h2>
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
                  setEditName(repository.name);
                  setEditDescription(repository.description || '');
                  setEditRepositoryUrl(repository.repository_url || '');
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
              <p className="text-sm text-cm-coffee">Repository Key</p>
              <p className="text-cm-charcoal font-mono text-sm">{repository.repository_key}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Status</p>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    repository.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {repository.status}
                </span>
                <button
                  onClick={toggleStatus}
                  disabled={actionInProgress === 'status'}
                  className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                >
                  {actionInProgress === 'status'
                    ? 'Updating...'
                    : repository.status === 'active'
                    ? 'Archive'
                    : 'Activate'}
                </button>
              </div>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Name</p>
              <p className="text-cm-charcoal">{repository.name}</p>
            </div>
            {repository.repository_type && (
              <div>
                <p className="text-sm text-cm-coffee">Repository Type</p>
                <p className="text-cm-charcoal capitalize">{repository.repository_type}</p>
              </div>
            )}
            {repository.description && (
              <div className="col-span-2">
                <p className="text-sm text-cm-coffee">Description</p>
                <p className="text-cm-charcoal">{repository.description}</p>
              </div>
            )}
            <div className="col-span-2">
              <p className="text-sm text-cm-coffee">Repository URL</p>
              <a
                href={repository.repository_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cm-terracotta hover:underline font-mono text-sm break-all"
              >
                {repository.repository_url}
              </a>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Created</p>
              <p className="text-cm-charcoal">{formatDateTime(repository.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Updated</p>
              <p className="text-cm-charcoal">{formatDateTime(repository.updated_at)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Linked Projects */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">
            Linked Projects ({projectRepositories.length})
          </h2>
          <button
            onClick={() => setShowLinkProjectModal(true)}
            className="px-3 py-1.5 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90"
          >
            Link Project
          </button>
        </div>

        {projectRepositories.length === 0 ? (
          <p className="text-sm text-cm-coffee">No projects linked to this repository yet. Link a project to associate this repository with it.</p>
        ) : (
          <div className="space-y-3">
            {projectRepositories.map((pr) => (
              <div
                key={pr.project_repository_key}
                className="flex items-center justify-between p-3 bg-cm-cream rounded-md"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm">
                    <span>PR</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-cm-charcoal">
                      {pr.project?.name || 'Unknown Project'}
                    </p>
                    <p className="text-xs text-cm-coffee">
                      Linked {formatDateTime(pr.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href={`/admin/projects/${pr.project.project_key}`}
                    className="text-xs text-cm-terracotta hover:underline"
                  >
                    View Project
                  </Link>
                  <button
                    onClick={() => unlinkProject(pr.project.project_key)}
                    disabled={actionInProgress === `unlink-${pr.project.project_key}`}
                    className="text-xs text-red-600 hover:underline disabled:opacity-50"
                  >
                    {actionInProgress === `unlink-${pr.project.project_key}` ? 'Unlinking...' : 'Unlink'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Link Project Modal */}
      {showLinkProjectModal && (
        <LinkProjectModal
          repositoryKey={repositoryKey}
          existingProjectKeys={projectRepositories.map(pr => pr.project.project_key)}
          onClose={() => setShowLinkProjectModal(false)}
          onLinked={() => {
            setShowLinkProjectModal(false);
            loadRepositoryData();
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
        {icons[type] || 'RP'}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-cm-sand text-xs font-medium text-cm-charcoal">
      {icons[type] || '?'}
    </span>
  );
}

function LinkProjectModal({
  repositoryKey,
  existingProjectKeys,
  onClose,
  onLinked,
}: {
  repositoryKey: string;
  existingProjectKeys: string[];
  onClose: () => void;
  onLinked: () => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectKey, setSelectedProjectKey] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await api.projects.list({ status: 'active' });
      if (response.success && response.data) {
        // Filter out projects that are already linked
        const availableProjects = response.data.projects.filter(
          p => !existingProjectKeys.includes(p.project_key)
        );
        setProjects(availableProjects);
      }
    } catch (err) {
      setError('Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectKey) {
      setError('Please select a project');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.repositories.addProject(repositoryKey, { project_key: selectedProjectKey });

      if (response.success) {
        onLinked();
      } else {
        setError(response.msg || 'Failed to link project');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to link project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Link Project to Repository</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <p className="text-sm text-cm-coffee">Loading projects...</p>
        ) : projects.length === 0 ? (
          <p className="text-sm text-cm-coffee">No available projects to link</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Project</label>
                <select
                  value={selectedProjectKey}
                  onChange={(e) => setSelectedProjectKey(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">Select a project...</option>
                  {projects.map((project) => (
                    <option key={project.project_key} value={project.project_key}>
                      {project.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-cm-coffee mt-1">
                  Select a project to link to this repository
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
                disabled={isSubmitting || !selectedProjectKey}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Linking...' : 'Link Project'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
