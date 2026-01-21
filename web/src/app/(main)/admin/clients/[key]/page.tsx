'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { Client, Model, Persona } from '@/types';

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

export default function ClientDetailPage() {
  const router = useRouter();
  const params = useParams();
  const clientKey = params.key as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [client, setClient] = useState<Client | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [actionInProgress, setActionInProgress] = useState('');
  const [activeTab, setActiveTab] = useState<'details' | 'models' | 'personas'>('details');

  // Edit form state
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editPublisher, setEditPublisher] = useState('');

  // Redirect if not admin
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    } else if (currentUser?.role !== 'admin') {
      router.push('/');
    }
  }, [isAuthenticated, currentUser, router]);

  // Load client data
  useEffect(() => {
    if (currentUser?.role === 'admin' && clientKey) {
      loadClientData();
    }
  }, [currentUser, clientKey]);

  const loadClientData = async () => {
    setIsLoading(true);
    try {
      const [clientResponse, modelsResponse, personasResponse] = await Promise.all([
        api.clients.get(clientKey),
        api.clients.getModels(clientKey),
        api.clients.getPersonas(clientKey),
      ]);

      if (clientResponse.success && clientResponse.data) {
        const clientData = clientResponse.data as unknown as Client;
        setClient(clientData);
        setEditName(clientData.name);
        setEditDescription(clientData.description || '');
        setEditPublisher(clientData.publisher || '');
      } else {
        setError('Client not found');
      }

      if (modelsResponse.success && modelsResponse.data) {
        setModels(modelsResponse.data.models || []);
      }

      if (personasResponse.success && personasResponse.data) {
        setPersonas(personasResponse.data.personas || []);
      }
    } catch (err) {
      setError('Failed to load client');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!client) return;
    setActionInProgress('save');
    setError('');

    try {
      const response = await api.clients.update(clientKey, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        publisher: editPublisher.trim() || undefined,
      });

      if (response.success && response.data) {
        setClient(response.data as unknown as Client);
        setIsEditing(false);
      } else {
        setError(response.msg || 'Failed to update client');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to update client');
    } finally {
      setActionInProgress('');
    }
  };

  const toggleStatus = async () => {
    if (!client) return;
    setActionInProgress('status');
    setError('');

    const newStatus = client.status === 'active' ? 'deprecated' : 'active';

    try {
      const response = await api.clients.update(clientKey, { status: newStatus });
      if (response.success && response.data) {
        setClient(response.data as unknown as Client);
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

  const ensureEntity = async () => {
    setActionInProgress('entity');
    setError('');

    try {
      const response = await api.clients.ensureEntity(clientKey);
      if (response.success && response.data) {
        loadClientData();
      } else {
        setError(response.msg || 'Failed to ensure entity');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Failed to ensure entity');
    } finally {
      setActionInProgress('');
    }
  };

  if (!isAuthenticated || currentUser?.role !== 'admin') {
    return null;
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-cm-coffee">Loading client...</p>
      </div>
    );
  }

  if (error && !client) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
        <Link href="/admin/clients" className="mt-4 inline-block text-cm-terracotta hover:underline">
          Back to Clients
        </Link>
      </div>
    );
  }

  if (!client) return null;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/admin/clients" className="text-cm-coffee hover:text-cm-charcoal">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-lg">
            <span>{"🖥️"}</span>
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-cm-charcoal">{client.name}</h1>
            <p className="text-sm text-cm-coffee font-mono">{client.client_key}</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-cm-sand mb-6">
        <div className="flex gap-6">
          {(['details', 'models', 'personas'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
                activeTab === tab
                  ? 'border-cm-terracotta text-cm-charcoal'
                  : 'border-transparent text-cm-coffee hover:text-cm-charcoal'
              }`}
            >
              {tab === 'details' ? 'Details' : tab === 'models' ? `Models (${models.length})` : `Personas (${personas.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Details Tab */}
      {activeTab === 'details' && (
        <div className="bg-cm-ivory border border-cm-sand rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-cm-charcoal">Client Details</h2>
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
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Publisher</label>
                <input
                  type="text"
                  value={editPublisher}
                  onChange={(e) => setEditPublisher(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                  placeholder="e.g., Anthropic, OpenAI"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">Description</label>
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  rows={3}
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
                    setEditName(client.name);
                    setEditDescription(client.description || '');
                    setEditPublisher(client.publisher || '');
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
                <p className="text-sm text-cm-coffee">Client Key</p>
                <p className="text-cm-charcoal font-mono text-sm">{client.client_key}</p>
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Name</p>
                <p className="text-cm-charcoal">{client.name}</p>
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Publisher</p>
                <p className="text-cm-charcoal">{client.publisher || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Status</p>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      client.status === 'active'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {client.status}
                  </span>
                  <button
                    onClick={toggleStatus}
                    disabled={actionInProgress === 'status'}
                    className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                  >
                    {actionInProgress === 'status'
                      ? 'Updating...'
                      : client.status === 'active'
                      ? 'Deprecate'
                      : 'Activate'}
                  </button>
                </div>
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Entity Key</p>
                <div className="flex items-center gap-2">
                  {client.entity_key ? (
                    <>
                      <Link
                        href={`/entities/${client.entity_key}`}
                        className="text-cm-terracotta hover:underline font-mono text-sm"
                      >
                        {client.entity_key}
                      </Link>
                    </>
                  ) : (
                    <>
                      <span className="text-cm-coffee text-sm">Not linked</span>
                      <button
                        onClick={ensureEntity}
                        disabled={actionInProgress === 'entity'}
                        className="text-xs text-cm-terracotta hover:underline disabled:opacity-50"
                      >
                        {actionInProgress === 'entity' ? 'Creating...' : 'Create Entity'}
                      </button>
                    </>
                  )}
                </div>
              </div>
              {client.description && (
                <div className="col-span-2">
                  <p className="text-sm text-cm-coffee">Description</p>
                  <p className="text-cm-charcoal">{client.description}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-cm-coffee">Created</p>
                <p className="text-cm-charcoal">{formatDateTime(client.created_at)}</p>
              </div>
              <div>
                <p className="text-sm text-cm-coffee">Updated</p>
                <p className="text-cm-charcoal">{formatDateTime(client.updated_at)}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && (
        <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
          <div className="p-4 border-b border-cm-sand">
            <h2 className="text-lg font-semibold text-cm-charcoal">Linked Models</h2>
            <p className="text-sm text-cm-coffee mt-1">AI models associated with this client platform.</p>
          </div>
          {models.length === 0 ? (
            <div className="p-8 text-center text-sm text-cm-coffee">
              No models linked to this client yet.
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-cm-sand/50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Model</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Provider</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Model ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.model_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-cm-charcoal">{model.name}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-cm-charcoal capitalize">{model.provider}</td>
                    <td className="px-4 py-3 text-sm text-cm-coffee font-mono">{model.model_id}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          model.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : model.status === 'deprecated'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {model.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Personas Tab */}
      {activeTab === 'personas' && (
        <div className="bg-cm-ivory border border-cm-sand rounded-lg overflow-hidden">
          <div className="p-4 border-b border-cm-sand">
            <h2 className="text-lg font-semibold text-cm-charcoal">Linked Personas</h2>
            <p className="text-sm text-cm-coffee mt-1">AI personas recommended for this client platform.</p>
          </div>
          {personas.length === 0 ? (
            <div className="p-8 text-center text-sm text-cm-coffee">
              No personas linked to this client yet.
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-cm-sand/50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Persona</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Role</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Capabilities</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-cm-charcoal">Status</th>
                </tr>
              </thead>
              <tbody>
                {personas.map((persona) => (
                  <tr key={persona.persona_key} className="border-t border-cm-sand hover:bg-cm-cream/50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-6 h-6 rounded-full flex items-center justify-center text-xs text-white"
                          style={{ backgroundColor: persona.color }}
                        >
                          {persona.name.charAt(0)}
                        </div>
                        <span className="text-sm font-medium text-cm-charcoal">{persona.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-cm-coffee font-mono">{persona.role}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(persona.capabilities || []).slice(0, 3).map((cap) => (
                          <span
                            key={cap}
                            className="px-1.5 py-0.5 text-xs bg-cm-sand rounded text-cm-coffee"
                          >
                            {cap}
                          </span>
                        ))}
                        {(persona.capabilities || []).length > 3 && (
                          <span className="text-xs text-cm-coffee">
                            +{(persona.capabilities || []).length - 3} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          persona.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : persona.status === 'archived'
                            ? 'bg-gray-100 text-gray-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {persona.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
