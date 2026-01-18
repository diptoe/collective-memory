'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { User, Domain } from '@/types';

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

function isAdminOrDomainAdmin(role?: string): boolean {
  return role === 'admin' || role === 'domain_admin';
}

export default function AdminUsersPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<{ total: number; active: number; suspended: number; admins: number; users: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<{ role?: string; status?: string }>({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [domains, setDomains] = useState<Domain[]>([]);

  // Redirect if not admin or domain_admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (!isAdminOrDomainAdmin(currentUser?.role)) {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load users and stats
  useEffect(() => {
    if (isAdminOrDomainAdmin(currentUser?.role)) {
      loadData();
    }
  }, [currentUser, filter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const promises: Promise<any>[] = [
        api.users.list(filter),
        api.users.stats(),
      ];
      // Only system admins can list domains
      if (currentUser?.role === 'admin') {
        promises.push(api.domains.list());
      }

      const results = await Promise.all(promises);
      const [usersResponse, statsResponse] = results;

      if (usersResponse.success && usersResponse.data) {
        setUsers(usersResponse.data.users);
      }
      if (statsResponse.success && statsResponse.data) {
        setStats(statsResponse.data);
      }
      if (results[2]?.success && results[2]?.data) {
        setDomains(results[2].data.domains);
      }
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserCreated = () => {
    setShowAddModal(false);
    loadData();
  };

  if (!isAuthenticated || !isAdminOrDomainAdmin(currentUser?.role)) {
    return null;
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-cm-charcoal">User Management</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
        >
          Add User
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Users" value={stats.total} />
          <StatCard label="Active" value={stats.active} color="green" />
          <StatCard label="Suspended" value={stats.suspended} color="red" />
          <StatCard label="Admins" value={stats.admins} color="blue" />
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <select
          value={filter.role || ''}
          onChange={(e) => setFilter((prev) => ({ ...prev, role: e.target.value || undefined }))}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="">All roles</option>
          <option value="admin">System Admin</option>
          <option value="domain_admin">Domain Admin</option>
          <option value="user">User</option>
        </select>
        <select
          value={filter.status || ''}
          onChange={(e) => setFilter((prev) => ({ ...prev, status: e.target.value || undefined }))}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">User</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Email</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Domain</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Role</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Last Login</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading users...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No users found
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.user_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm font-medium">
                        {user.initials}
                      </div>
                      <span className="text-sm font-medium text-cm-charcoal">{user.display_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee">{user.email}</td>
                  <td className="px-4 py-3 text-sm text-cm-coffee">
                    {user.domain?.name || <span className="text-cm-sand">-</span>}
                  </td>
                  <td className="px-4 py-3">
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
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        user.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {user.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee">
                    {user.last_login_at
                      ? formatDateTime(user.last_login_at)
                      : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/admin/users/${user.user_key}`}
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

      {/* Add User Modal */}
      {showAddModal && (
        <AddUserModal
          onClose={() => setShowAddModal(false)}
          onSuccess={handleUserCreated}
          currentUser={currentUser!}
          domains={domains}
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
  color?: 'green' | 'red' | 'blue';
}) {
  const colorClasses = {
    green: 'text-green-600',
    red: 'text-red-600',
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

function AddUserModal({
  onClose,
  onSuccess,
  currentUser,
  domains,
}: {
  onClose: () => void;
  onSuccess: () => void;
  currentUser: User;
  domains: Domain[];
}) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'user' as 'admin' | 'domain_admin' | 'user',
    domain_key: currentUser.role === 'domain_admin' ? currentUser.domain_key || '' : '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isSystemAdmin = currentUser.role === 'admin';
  const isDomainAdmin = currentUser.role === 'domain_admin';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.email || !formData.password || !formData.first_name || !formData.last_name) {
      setError('All fields are required');
      return;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    if (isSystemAdmin && !formData.domain_key) {
      setError('Please select a domain');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await api.users.create({
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        role: formData.role,
        domain_key: formData.domain_key || undefined,
      });

      if (response.success) {
        onSuccess();
      } else {
        setError(response.msg || 'Failed to create user');
      }
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to create user');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-lg shadow-lg w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-cm-charcoal">Add New User</h2>
          <button
            onClick={onClose}
            className="text-cm-coffee hover:text-cm-charcoal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                First Name
              </label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="John"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Last Name
              </label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                placeholder="Doe"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              placeholder="john.doe@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Password
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              placeholder="Minimum 8 characters"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Role
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'domain_admin' | 'user' })}
              className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
            >
              <option value="user">User</option>
              <option value="domain_admin">Domain Admin</option>
              {isSystemAdmin && <option value="admin">System Admin</option>}
            </select>
            {isDomainAdmin && (
              <p className="text-xs text-cm-coffee mt-1">
                Domain admins can create users and domain admins in their own domain
              </p>
            )}
          </div>

          {isSystemAdmin && (
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Domain <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.domain_key}
                onChange={(e) => setFormData({ ...formData, domain_key: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                required
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

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-cm-coffee hover:text-cm-charcoal transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
