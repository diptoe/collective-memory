'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Team, TeamMembership, TeamMemberRole, User, Domain } from '@/types';

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

export default function TeamDetailPage() {
  const router = useRouter();
  const params = useParams();
  const teamKey = params.key as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMembership[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [actionInProgress, setActionInProgress] = useState('');
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [showMoveDomainModal, setShowMoveDomainModal] = useState(false);

  // Edit form state
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');

  // Redirect if not admin or domain_admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin' && currentUser?.role !== 'domain_admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load team data
  useEffect(() => {
    if ((currentUser?.role === 'admin' || currentUser?.role === 'domain_admin') && teamKey) {
      loadTeamData();
    }
  }, [currentUser, teamKey]);

  const loadTeamData = async () => {
    setIsLoading(true);
    try {
      const [teamResponse, membersResponse] = await Promise.all([
        api.teams.get(teamKey),
        api.teams.members(teamKey),
      ]);

      if (teamResponse.success && teamResponse.data) {
        setTeam(teamResponse.data.team);
        setEditName(teamResponse.data.team.name);
        setEditDescription(teamResponse.data.team.description || '');
      } else {
        setError('Team not found');
      }

      if (membersResponse.success && membersResponse.data) {
        setMembers(membersResponse.data.members);
      }
    } catch (err) {
      setError('Failed to load team');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!team) return;
    setActionInProgress('save');
    setError('');

    try {
      const response = await api.teams.update(teamKey, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      });

      if (response.success && response.data) {
        setTeam(response.data.team);
        setIsEditing(false);
      } else {
        setError(response.msg || 'Failed to update team');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update team');
    } finally {
      setActionInProgress('');
    }
  };

  const toggleStatus = async () => {
    if (!team) return;
    setActionInProgress('status');
    setError('');

    const newStatus = team.status === 'active' ? 'archived' : 'active';

    try {
      const response = await api.teams.update(teamKey, { status: newStatus });
      if (response.success && response.data) {
        setTeam(response.data.team);
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

  const updateMemberRole = async (userKey: string, newRole: TeamMemberRole) => {
    setActionInProgress(`role-${userKey}`);
    setError('');

    try {
      const response = await api.teams.updateMember(teamKey, userKey, { role: newRole });
      if (response.success && response.data?.membership) {
        // Update the specific member in the array
        setMembers(prev => prev.map(m =>
          m.user_key === userKey ? { ...m, ...response.data!.membership } : m
        ));
      } else {
        setError(response.msg || 'Failed to update member role');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update member role');
    } finally {
      setActionInProgress('');
    }
  };

  const updateMemberSlug = async (userKey: string, newSlug: string) => {
    const trimmedSlug = newSlug.trim().toLowerCase();
    // Find current member to check if unchanged
    const member = members.find(m => m.user_key === userKey);
    if (member?.slug === trimmedSlug || (!member?.slug && !trimmedSlug)) return;

    setActionInProgress(`slug-${userKey}`);
    setError('');

    try {
      const response = await api.teams.updateMember(teamKey, userKey, { slug: trimmedSlug });
      if (response.success && response.data?.membership) {
        // Update the specific member in the array
        setMembers(prev => prev.map(m =>
          m.user_key === userKey ? { ...m, ...response.data!.membership } : m
        ));
      } else {
        setError(response.msg || 'Failed to update member slug');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update member slug');
    } finally {
      setActionInProgress('');
    }
  };

  const removeMember = async (userKey: string) => {
    if (!confirm('Are you sure you want to remove this member from the team?')) return;

    setActionInProgress(`remove-${userKey}`);
    setError('');

    try {
      const response = await api.teams.removeMember(teamKey, userKey);
      if (response.success) {
        setMembers(members.filter(m => m.user_key !== userKey));
      } else {
        setError(response.msg || 'Failed to remove member');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to remove member');
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
        <p className="text-cm-coffee">Loading team...</p>
      </div>
    );
  }

  if (error && !team) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
        <Link href="/admin/teams" className="mt-4 inline-block text-cm-terracotta hover:underline">
          Back to Teams
        </Link>
      </div>
    );
  }

  if (!team) return null;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/admin/teams" className="text-cm-coffee hover:text-cm-charcoal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-lg">
            <span>{"👥"}</span>
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">{team.name}</h1>
            <p className="text-sm text-cm-coffee font-mono">{team.slug}</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Team Details */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Team Details</h2>
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
                  setEditName(team.name);
                  setEditDescription(team.description || '');
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
              <p className="text-sm text-cm-coffee">Team Key</p>
              <p className="text-cm-charcoal font-mono text-sm">{team.team_key}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Slug</p>
              <p className="text-cm-charcoal font-mono">{team.slug}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Name</p>
              <p className="text-cm-charcoal">{team.name}</p>
            </div>
            <div>
              <p className="text-sm text-cm-coffee">Status</p>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    team.status === 'active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {team.status}
                </span>
                <button
                  onClick={toggleStatus}
                  disabled={actionInProgress === 'status'}
                  className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                >
                  {actionInProgress === 'status'
                    ? 'Updating...'
                    : team.status === 'active'
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
                  <span className="text-cm-charcoal font-mono text-sm">{team.domain_key}</span>
                  <button
                    onClick={() => setShowMoveDomainModal(true)}
                    className="text-xs text-cm-terracotta hover:underline"
                  >
                    Move to Another Domain
                  </button>
                </div>
              </div>
            )}
            {team.description && (
              <div className="col-span-2">
                <p className="text-sm text-cm-coffee">Description</p>
                <p className="text-cm-charcoal">{team.description}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-cm-coffee">Created</p>
              <p className="text-cm-charcoal">{formatDateTime(team.created_at)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Team Members */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">
            Members ({members.length})
          </h2>
          <button
            onClick={() => setShowAddMemberModal(true)}
            className="px-3 py-1.5 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90"
          >
            Add Member
          </button>
        </div>

        {members.length === 0 ? (
          <p className="text-sm text-cm-coffee">No members in this team yet. Add members to get started.</p>
        ) : (
          <div className="space-y-3">
            {members.map((membership) => (
              <div
                key={membership.membership_key}
                className="flex items-center justify-between p-3 bg-cm-cream rounded-md"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm font-medium">
                    {membership.user?.initials || '?'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-cm-charcoal">
                      {membership.user?.display_name || 'Unknown User'}
                    </p>
                    <div className="flex items-center gap-2">
                      <p className="text-xs text-cm-coffee">{membership.user?.email}</p>
                      {membership.slug && (
                        <span className="px-1.5 py-0.5 text-xs bg-cm-sand rounded text-cm-coffee font-mono">
                          @{membership.slug}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    defaultValue={membership.slug || ''}
                    placeholder="slug"
                    onBlur={(e) => updateMemberSlug(membership.user_key, e.target.value)}
                    disabled={actionInProgress === `slug-${membership.user_key}`}
                    className="w-20 px-2 py-1 text-xs border border-cm-sand rounded-md bg-cm-ivory text-cm-charcoal font-mono placeholder:text-cm-sand focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 disabled:opacity-50"
                    title="Custom identifier (2-10 chars, used as agent_id suffix)"
                  />
                  <select
                    value={membership.role}
                    onChange={(e) => updateMemberRole(membership.user_key, e.target.value as TeamMemberRole)}
                    disabled={actionInProgress === `role-${membership.user_key}`}
                    className="px-2 py-1 text-xs border border-cm-sand rounded-md bg-cm-ivory text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 disabled:opacity-50"
                  >
                    <option value="owner">Owner</option>
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  <button
                    onClick={() => removeMember(membership.user_key)}
                    disabled={actionInProgress === `remove-${membership.user_key}`}
                    className="text-xs text-red-600 hover:underline disabled:opacity-50"
                  >
                    {actionInProgress === `remove-${membership.user_key}` ? 'Removing...' : 'Remove'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Member Modal */}
      {showAddMemberModal && (
        <AddMemberModal
          teamKey={teamKey}
          existingMemberKeys={members.map(m => m.user_key)}
          onClose={() => setShowAddMemberModal(false)}
          onAdded={() => {
            setShowAddMemberModal(false);
            loadTeamData();
          }}
        />
      )}

      {/* Move to Domain Modal - System Admins Only */}
      {showMoveDomainModal && (
        <MoveDomainModal
          team={team}
          onClose={() => setShowMoveDomainModal(false)}
          onMoved={() => {
            setShowMoveDomainModal(false);
            loadTeamData();
          }}
        />
      )}
    </div>
  );
}

function AddMemberModal({
  teamKey,
  existingMemberKeys,
  onClose,
  onAdded,
}: {
  teamKey: string;
  existingMemberKeys: string[];
  onClose: () => void;
  onAdded: () => void;
}) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserKey, setSelectedUserKey] = useState('');
  const [role, setRole] = useState<TeamMemberRole>('member');
  const [slug, setSlug] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Update slug when user is selected
  const handleUserSelect = (userKey: string) => {
    setSelectedUserKey(userKey);
    const selectedUser = users.find(u => u.user_key === userKey);
    if (selectedUser?.initials) {
      setSlug(selectedUser.initials.toLowerCase());
    } else {
      setSlug('');
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await api.users.list({ limit: 100 });
      if (response.success && response.data) {
        // Filter out users who are already members
        const availableUsers = response.data.users.filter(
          u => !existingMemberKeys.includes(u.user_key)
        );
        setUsers(availableUsers);
      }
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserKey) {
      setError('Please select a user');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.teams.addMember(teamKey, {
        user_key: selectedUserKey,
        role,
        ...(slug && { slug }),
      });

      if (response.success) {
        onAdded();
      } else {
        setError(response.msg || 'Failed to add member');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to add member');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Add Team Member</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <p className="text-sm text-cm-coffee">Loading users...</p>
        ) : users.length === 0 ? (
          <p className="text-sm text-cm-coffee">No available users to add</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">User</label>
                <select
                  value={selectedUserKey}
                  onChange={(e) => handleUserSelect(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="">Select a user...</option>
                  {users.map((user) => (
                    <option key={user.user_key} value={user.user_key}>
                      {user.display_name} ({user.email})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as TeamMemberRole)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                  <option value="owner">Owner</option>
                </select>
                <p className="text-xs text-cm-coffee mt-1">
                  Owners and admins can manage team members. Members can create content. Viewers can only read.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Slug <span className="text-cm-coffee font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                  placeholder="Defaults to user initials"
                  maxLength={10}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal font-mono focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                />
                <p className="text-xs text-cm-coffee mt-1">
                  Used as agent ID suffix (e.g., claude-code-project-{slug || 'wh'})
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
                disabled={isSubmitting || !selectedUserKey}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Adding...' : 'Add Member'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function MoveDomainModal({
  team,
  onClose,
  onMoved,
}: {
  team: Team;
  onClose: () => void;
  onMoved: () => void;
}) {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomainKey, setSelectedDomainKey] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [moveSummary, setMoveSummary] = useState<{
    project_associations_removed: number;
    slug_changed: boolean;
    original_slug: string;
    new_slug: string;
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
          d => d.domain_key !== team.domain_key
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
    if (!confirm(`Are you sure you want to move "${team.name}" to domain "${selectedDomain?.name || selectedDomainKey}"?\n\nThis action will:\n• Remove all project associations\n• Update the team's domain\n• Slug may be modified if already exists in target domain`)) {
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.teams.moveToDomain(team.team_key, selectedDomainKey);

      if (response.success && response.data) {
        setMoveSummary(response.data.summary);
      } else {
        setError(response.msg || 'Failed to move team');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to move team');
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
            <h2 className="text-lg font-semibold text-cm-charcoal">Team Moved Successfully</h2>
          </div>

          <div className="bg-cm-cream rounded-md p-4 mb-4">
            <h3 className="text-sm font-medium text-cm-charcoal mb-2">Migration Summary</h3>
            <ul className="text-sm text-cm-coffee space-y-1">
              <li>• <strong>{moveSummary.project_associations_removed}</strong> project association(s) removed</li>
              {moveSummary.slug_changed && (
                <li>• Slug changed from <strong className="font-mono">{moveSummary.original_slug}</strong> to <strong className="font-mono">{moveSummary.new_slug}</strong></li>
              )}
            </ul>
          </div>

          <p className="text-sm text-cm-coffee mb-4">
            The team has been moved to the new domain. Team members are preserved and can now access the team in the new domain.
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
        <h2 className="text-lg font-semibold text-cm-charcoal mb-4">Move Team to Another Domain</h2>

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
                <li>Remove all project associations (projects are domain-specific)</li>
                <li>Keep all team memberships intact</li>
                <li>Modify slug if already exists in target domain</li>
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
                <p className="text-sm text-cm-coffee font-mono">{team.domain_key}</p>
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
                {isSubmitting ? 'Moving Team...' : 'Move Team'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
