'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Persona, Client } from '@/types';
import { ClientsNav } from '@/components/admin';
import { cn } from '@/lib/utils';

export default function AdminPersonasPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterClient, setFilterClient] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const isAdmin = currentUser?.role === 'admin';

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load clients for filter
  useEffect(() => {
    async function loadClients() {
      try {
        const res = await api.clients.list({ status: 'active' });
        if (res.success && res.data?.clients) {
          setClients(res.data.clients as Client[]);
        }
      } catch (err) {
        console.error('Failed to load clients:', err);
      }
    }
    if (isAdmin) {
      loadClients();
    }
  }, [isAdmin]);

  // Load personas
  useEffect(() => {
    async function loadPersonas() {
      setIsLoading(true);
      try {
        const res = await api.personas.list({ include_archived: filterStatus === 'all' || filterStatus === 'archived' });
        let personasList = res.data?.personas || [];

        // Filter by client if selected
        if (filterClient !== 'all') {
          personasList = personasList.filter(p => p.client_key === filterClient);
        }

        // Filter by status if not all
        if (filterStatus !== 'all') {
          personasList = personasList.filter(p => p.status === filterStatus);
        }

        setPersonas(personasList);
      } catch (err) {
        console.error('Failed to load personas:', err);
      } finally {
        setIsLoading(false);
      }
    }

    if (isAdmin) {
      loadPersonas();
    }
  }, [isAdmin, filterClient, filterStatus]);

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  // Stats
  const stats = {
    total: personas.length,
    active: personas.filter(p => p.status === 'active').length,
    linked: personas.filter(p => p.client_key).length,
    unlinked: personas.filter(p => !p.client_key).length,
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-cm-charcoal">Persona Management</h1>
          <p className="text-cm-coffee mt-1">
            Manage AI personas and their client associations
          </p>
        </div>
        <div className="flex items-center gap-4">
          <ClientsNav currentPage="personas" />
          <Link
            href="/admin/personas/new"
            className="flex items-center gap-2 px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Persona
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Personas" value={stats.total} />
        <StatCard label="Active" value={stats.active} color="green" />
        <StatCard label="Linked to Client" value={stats.linked} color="blue" />
        <StatCard label="Unlinked" value={stats.unlinked} color="gray" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6 flex-wrap">
        {/* Client filter */}
        <select
          value={filterClient}
          onChange={(e) => setFilterClient(e.target.value)}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="all">All Clients</option>
          {clients.map((client) => (
            <option key={client.client_key} value={client.client_key}>
              {client.name}
            </option>
          ))}
        </select>

        {/* Status filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal text-sm focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
        >
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Personas Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Persona</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Role</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Client</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Capabilities</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading personas...
                </td>
              </tr>
            ) : personas.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No personas found.
                </td>
              </tr>
            ) : (
              personas.map((persona) => (
                <PersonaRow key={persona.persona_key} persona={persona} clients={clients} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PersonaRow({ persona, clients }: { persona: Persona; clients: Client[] }) {
  const client = clients.find(c => c.client_key === persona.client_key);

  return (
    <tr className="border-t border-cm-sand hover:bg-cm-cream/50">
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
            style={{ backgroundColor: persona.color || '#d97757' }}
          >
            {persona.name.charAt(0)}
          </div>
          <span className="text-sm font-medium text-cm-charcoal">{persona.name}</span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-cm-coffee font-mono">{persona.role}</td>
      <td className="px-4 py-3 text-sm text-cm-charcoal">
        {client ? (
          <Link
            href={`/admin/clients/${client.client_key}`}
            className="text-cm-terracotta hover:underline"
          >
            {client.name}
          </Link>
        ) : (
          <span className="text-cm-coffee/50">-</span>
        )}
      </td>
      <td className="px-4 py-3">
        {persona.capabilities && persona.capabilities.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {persona.capabilities.slice(0, 3).map((cap) => (
              <span
                key={cap}
                className="px-1.5 py-0.5 bg-cm-sand/50 text-cm-coffee rounded text-xs"
              >
                {cap}
              </span>
            ))}
            {persona.capabilities.length > 3 && (
              <span className="text-xs text-cm-coffee">+{persona.capabilities.length - 3}</span>
            )}
          </div>
        ) : (
          <span className="text-cm-coffee/50 text-sm">-</span>
        )}
      </td>
      <td className="px-4 py-3">
        <span
          className={cn(
            'px-2 py-1 text-xs rounded-full',
            persona.status === 'active'
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-700'
          )}
        >
          {persona.status}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <Link
          href={`/personas/${persona.persona_key}`}
          className="text-sm text-cm-terracotta hover:underline"
        >
          View
        </Link>
      </td>
    </tr>
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
