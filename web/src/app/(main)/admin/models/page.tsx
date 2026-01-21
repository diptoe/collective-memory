'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Copy, Check, Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Model, Client, ModelProvider } from '@/types';
import { ClientsNav } from '@/components/admin';
import { cn } from '@/lib/utils';

const PROVIDER_CONFIG: Record<ModelProvider, { label: string; icon: string }> = {
  anthropic: { label: 'Anthropic', icon: '/icons/claude.svg' },
  openai: { label: 'OpenAI', icon: '/icons/gpt.svg' },
  google: { label: 'Google', icon: '/icons/gemini.svg' },
};

export default function AdminModelsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [models, setModels] = useState<Model[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterClient, setFilterClient] = useState<string>('all');
  const [includeDeprecated, setIncludeDeprecated] = useState(false);
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
          setClients(res.data.clients);
        }
      } catch (err) {
        console.error('Failed to load clients:', err);
      }
    }
    if (isAdmin) {
      loadClients();
    }
  }, [isAdmin]);

  // Load models
  useEffect(() => {
    async function loadModels() {
      setIsLoading(true);
      try {
        const params: { provider?: string; include_deprecated?: boolean } = {};
        if (filterProvider !== 'all') {
          params.provider = filterProvider;
        }
        if (includeDeprecated) {
          params.include_deprecated = true;
        }
        const res = await api.models.list(params);
        let modelsList = res.data?.models || [];

        // Filter by client if selected
        if (filterClient !== 'all') {
          modelsList = modelsList.filter(m => m.client_key === filterClient);
        }

        setModels(modelsList);
      } catch (err) {
        console.error('Failed to load models:', err);
      } finally {
        setIsLoading(false);
      }
    }

    if (isAdmin) {
      loadModels();
    }
  }, [isAdmin, filterProvider, filterClient, includeDeprecated]);

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  // Group models by provider
  const modelsByProvider = models.reduce((acc, model) => {
    const provider = model.provider;
    if (!acc[provider]) {
      acc[provider] = [];
    }
    acc[provider].push(model);
    return acc;
  }, {} as Record<string, Model[]>);

  // Stats
  const stats = {
    total: models.length,
    active: models.filter(m => m.status === 'active').length,
    linked: models.filter(m => m.client_key).length,
    unlinked: models.filter(m => !m.client_key).length,
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-cm-charcoal">Model Management</h1>
          <p className="text-cm-coffee mt-1">
            Manage AI models and their client associations
          </p>
        </div>
        <div className="flex items-center gap-4">
          <ClientsNav currentPage="models" />
          <Link
            href="/admin/models/new"
            className="flex items-center gap-2 px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Model
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Models" value={stats.total} />
        <StatCard label="Active" value={stats.active} color="green" />
        <StatCard label="Linked to Client" value={stats.linked} color="blue" />
        <StatCard label="Unlinked" value={stats.unlinked} color="gray" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6 flex-wrap">
        {/* Provider filter */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFilterProvider('all')}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              filterProvider === 'all'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
            )}
          >
            All Providers
          </button>
          {(['anthropic', 'openai', 'google'] as ModelProvider[]).map((provider) => (
            <button
              key={provider}
              onClick={() => setFilterProvider(provider)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-2',
                filterProvider === provider
                  ? 'bg-cm-terracotta text-cm-ivory'
                  : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
              )}
            >
              <img src={PROVIDER_CONFIG[provider].icon} alt="" className="w-4 h-4" />
              {PROVIDER_CONFIG[provider].label}
            </button>
          ))}
        </div>

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

        <label className="flex items-center gap-2 text-sm text-cm-coffee">
          <input
            type="checkbox"
            checked={includeDeprecated}
            onChange={(e) => setIncludeDeprecated(e.target.checked)}
            className="rounded border-cm-sand"
          />
          Show deprecated
        </label>
      </div>

      {/* Models Table */}
      <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-cm-sand/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Model</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Provider</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Model ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Client</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Context</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-cm-charcoal">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  Loading models...
                </td>
              </tr>
            ) : models.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-cm-coffee">
                  No models found.
                </td>
              </tr>
            ) : (
              models.map((model) => (
                <ModelRow key={model.model_key} model={model} clients={clients} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModelRow({ model, clients }: { model: Model; clients: Client[] }) {
  const [copied, setCopied] = useState(false);
  const client = clients.find(c => c.client_key === model.client_key);

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <tr className="border-t border-cm-sand hover:bg-cm-cream/50">
      <td className="px-4 py-3">
        <div>
          <span className="text-sm font-medium text-cm-charcoal">{model.name}</span>
          {model.capabilities && model.capabilities.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {model.capabilities.slice(0, 3).map((cap) => (
                <span
                  key={cap}
                  className="px-1.5 py-0.5 bg-cm-sand/50 text-cm-coffee rounded text-xs"
                >
                  {cap}
                </span>
              ))}
              {model.capabilities.length > 3 && (
                <span className="text-xs text-cm-coffee">+{model.capabilities.length - 3}</span>
              )}
            </div>
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-cm-charcoal capitalize">{model.provider}</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="text-sm text-cm-coffee font-mono">{model.model_id}</span>
          <button
            onClick={() => copyToClipboard(model.model_id)}
            className="p-0.5 text-cm-coffee/40 hover:text-cm-coffee transition-colors"
            title="Copy model ID"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </td>
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
      <td className="px-4 py-3 text-sm text-cm-coffee">
        {model.context_window ? `${(model.context_window / 1000).toFixed(0)}K` : '-'}
      </td>
      <td className="px-4 py-3">
        <span
          className={cn(
            'px-2 py-1 text-xs rounded-full',
            model.status === 'active'
              ? 'bg-green-100 text-green-700'
              : model.status === 'deprecated'
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-gray-100 text-gray-700'
          )}
        >
          {model.status}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <Link
          href={`/models/${model.model_key}`}
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
