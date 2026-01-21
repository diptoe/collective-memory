'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Client } from '@/types';
import { ClientsNav } from '@/components/admin';

export default function AdminClientsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<{ status?: string }>({});
  const isAdmin = currentUser?.role === 'admin';

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load clients
  useEffect(() => {
    if (currentUser?.role === 'admin') {
      loadData();
    }
  }, [currentUser, filter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const response = await api.clients.list({
        status: filter.status,
        include_counts: true,
      });

      if (response.success && response.data) {
        setClients(response.data.clients as Client[]);
      }
    } catch (err) {
      console.error('Failed to load clients:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  // Calculate stats from data
  const stats = {
    total: clients.length,
    active: clients.filter(c => c.status === 'active').length,
    deprecated: clients.filter(c => c.status === 'deprecated').length,
    totalModels: clients.reduce((sum, c) => sum + (c.models_count || 0), 0),
    totalPersonas: clients.reduce((sum, c) => sum + (c.personas_count || 0), 0),
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-cm-charcoal">Client Management</h1>
          <p className="text-cm-coffee mt-1">
            Manage AI development tools and their associated models and personas
          </p>
        </div>
        <div className="flex items-center gap-4">
          <ClientsNav currentPage="clients" />
          <Link
            href="/admin/clients/new"
            className="flex items-center gap-2 px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Client
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <StatCard label="Total Clients" value={stats.total} />
        <StatCard label="Active" value={stats.active} color="green" />
        <StatCard label="Deprecated" value={stats.deprecated} color="gray" />
        <StatCard label="Total Models" value={stats.totalModels} color="blue" />
        <StatCard label="Total Personas" value={stats.totalPersonas} color="blue" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <select
          value={filter.status || ''}
          onChange={(e) => setFilter((prev) => ({ ...prev, status: e.target.value || undefined }))}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="deprecated">Deprecated</option>
        </select>
      </div>

      {/* Clients Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Client</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Key</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Publisher</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Models</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Personas</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading clients...
                </td>
              </tr>
            ) : clients.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No clients found. Click &quot;Add Client&quot; to create one.
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <tr key={client.client_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm font-medium text-cm-charcoal">{client.name}</span>
                      {client.description && (
                        <p className="text-xs text-cm-coffee mt-0.5 truncate max-w-xs">{client.description}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-cm-coffee font-mono">{client.client_key}</td>
                  <td className="px-4 py-3 text-sm text-cm-charcoal">{client.publisher || '-'}</td>
                  <td className="px-4 py-3 text-sm text-cm-charcoal">{client.models_count ?? 0}</td>
                  <td className="px-4 py-3 text-sm text-cm-charcoal">{client.personas_count ?? 0}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        client.status === 'active'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {client.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/admin/clients/${client.client_key}`}
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

      {/* Info Box */}
      <div className="mt-6 p-4 bg-cm-sand/30 border border-cm-sand rounded-lg">
        <h3 className="text-sm font-medium text-cm-charcoal mb-2">About Clients</h3>
        <p className="text-sm text-cm-coffee">
          Clients represent the AI development tools and IDEs that can connect to Collective Memory
          (e.g., Claude Code, Cursor, VS Code). Each client can have associated Models and Personas
          that are optimized for that environment.
        </p>
      </div>
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
