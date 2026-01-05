'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Persona, ClientType } from '@/types';
import { use } from 'react';

export default function PersonaDetailPage({ params }: { params: Promise<{ key: string }> }) {
  // Unwrap params using React.use()
  const { key } = use(params);
  
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    system_prompt: '',
    traits: '',
    capabilities: '',
    color: '#d97757',
  });
  const [selectedClients, setSelectedClients] = useState<ClientType[]>([]);

  const availableClients: ClientType[] = ['claude-code', 'claude-desktop', 'codex', 'gemini-cli'];

  useEffect(() => {
    loadPersona();
  }, [key]);

  async function loadPersona() {
    try {
      setLoading(true);
      const res = await api.personas.get(key, true);
      const p = res.data;

      if (p && p.persona_key) {
        setPersona(p);
        // Initialize form data
        setFormData({
          name: p.name,
          role: p.role,
          system_prompt: p.system_prompt || '',
          traits: p.personality?.traits?.join(', ') || '',
          capabilities: p.capabilities?.join(', ') || '',
          color: p.color || '#d97757',
        });
        setSelectedClients(p.suggested_clients || []);
      } else {
        setError('Persona not found');
      }
    } catch (err: any) {
      console.error('Failed to load persona:', err);
      setError(err.response?.data?.msg || 'Failed to load persona');
    } finally {
      setLoading(false);
    }
  }

  const handleClientToggle = (client: ClientType) => {
    if (selectedClients.includes(client)) {
      setSelectedClients(selectedClients.filter(c => c !== client));
    } else {
      setSelectedClients([...selectedClients, client]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const traitsList = formData.traits.split(',').map(t => t.trim()).filter(Boolean);
      const capabilitiesList = formData.capabilities.split(',').map(c => c.trim()).filter(Boolean);

      await api.personas.update(key, {
        name: formData.name,
        role: formData.role,
        system_prompt: formData.system_prompt,
        color: formData.color,
        suggested_clients: selectedClients,
        capabilities: capabilitiesList,
        personality: { traits: traitsList }
      });

      // Reload to get fresh data
      await loadPersona();
      setIsEditing(false);
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to update persona');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!persona) return;
    
    try {
      if (persona.status === 'active') {
        await api.personas.delete(key); // Archive
      } else {
        await api.personas.activate(key);
      }
      loadPersona();
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to update status');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading persona...</p>
      </div>
    );
  }

  if (!persona && !loading) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          {error || 'Persona not found'}
        </div>
        <Link href="/personas" className="mt-4 inline-block text-cm-terracotta hover:underline">
          &larr; Back to Personas
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link 
            href="/personas"
            className="text-cm-coffee hover:text-cm-charcoal transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal flex items-center gap-3">
              {persona?.name}
              <span className={`px-2 py-0.5 text-xs rounded-full border ${
                persona?.status === 'active' 
                  ? 'bg-green-50 text-green-700 border-green-200' 
                  : 'bg-gray-100 text-gray-500 border-gray-200'
              }`}>
                {persona?.status}
              </span>
            </h1>
            <p className="text-cm-coffee font-mono text-sm mt-1">
              {persona?.role}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {!isEditing && (
            <button
              onClick={handleToggleStatus}
              className={`px-4 py-2 rounded-lg transition-colors border ${
                persona?.status === 'active'
                  ? 'border-red-200 text-red-600 hover:bg-red-50'
                  : 'border-green-200 text-green-600 hover:bg-green-50'
              }`}
            >
              {persona?.status === 'active' ? 'Archive' : 'Activate'}
            </button>
          )}
          
          {isEditing ? (
            <button 
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal border border-cm-sand rounded-lg"
            >
              Cancel
            </button>
          ) : (
            <button 
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna"
            >
              Edit Persona
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {isEditing ? (
        <form onSubmit={handleSave} className="bg-cm-ivory rounded-xl border border-cm-sand shadow-sm p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Display Name
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Role ID (Unique)
              </label>
              <input
                type="text"
                required
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta font-mono text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              System Prompt
            </label>
            <textarea
              rows={8}
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta font-mono text-sm"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Personality Traits
              </label>
              <input
                type="text"
                value={formData.traits}
                onChange={(e) => setFormData({ ...formData, traits: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                placeholder="Comma separated"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Capabilities
              </label>
              <input
                type="text"
                value={formData.capabilities}
                onChange={(e) => setFormData({ ...formData, capabilities: e.target.value })}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                placeholder="Comma separated"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-2">
              Suggested Clients
            </label>
            <div className="flex flex-wrap gap-2">
              {availableClients.map((client) => (
                <button
                  key={client}
                  type="button"
                  onClick={() => handleClientToggle(client)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors border ${
                    selectedClients.includes(client)
                      ? 'bg-cm-terracotta text-cm-ivory border-cm-terracotta'
                      : 'bg-transparent text-cm-coffee border-cm-sand hover:border-cm-terracotta'
                  }`}
                >
                  {client}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Theme Color
            </label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="h-10 w-20 rounded cursor-pointer border border-cm-sand"
              />
              <span className="text-sm font-mono text-cm-coffee">{formData.color}</span>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-cm-sand">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="col-span-2 space-y-6">
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">System Prompt</h3>
                <div className="bg-cm-sand/20 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap text-cm-charcoal">
                  {persona?.system_prompt || <span className="text-cm-coffee/50 italic">No system prompt defined</span>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                  <h3 className="text-sm font-medium text-cm-coffee mb-3">Personality Traits</h3>
                  <div className="flex flex-wrap gap-2">
                    {persona?.personality?.traits?.map(trait => (
                      <span key={trait} className="px-3 py-1 bg-cm-sand text-cm-coffee rounded-full text-sm">
                        {trait}
                      </span>
                    ))}
                    {(!persona?.personality?.traits || persona.personality.traits.length === 0) && (
                      <span className="text-cm-coffee/50 text-sm italic">None defined</span>
                    )}
                  </div>
                </div>

                <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                  <h3 className="text-sm font-medium text-cm-coffee mb-3">Capabilities</h3>
                  <div className="flex flex-wrap gap-2">
                    {persona?.capabilities?.map(cap => (
                      <span key={cap} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-100">
                        {cap}
                      </span>
                    ))}
                    {(!persona?.capabilities || persona.capabilities.length === 0) && (
                      <span className="text-cm-coffee/50 text-sm italic">None defined</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-4">Metadata</h3>
                
                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Persona Key</span>
                    <p className="font-mono text-sm text-cm-charcoal mt-1 break-all">{persona?.persona_key}</p>
                  </div>
                  
                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Created</span>
                    <p className="text-sm text-cm-charcoal mt-1">
                      {persona?.created_at && new Date(persona.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Theme Color</span>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="w-6 h-6 rounded border border-cm-sand" style={{ backgroundColor: persona?.color }} />
                      <span className="font-mono text-sm text-cm-charcoal">{persona?.color}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Suggested Clients</h3>
                <div className="flex flex-wrap gap-2">
                  {persona?.suggested_clients?.map(client => (
                    <span key={client} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm border border-purple-100">
                      {client}
                    </span>
                  ))}
                  {(!persona?.suggested_clients || persona.suggested_clients.length === 0) && (
                    <span className="text-cm-coffee/50 text-sm italic">Any client</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
