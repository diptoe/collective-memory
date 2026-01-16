'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ClientType } from '@/types';

export default function NewPersonaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    role: '',
    system_prompt: '',
    traits: '',
    capabilities: '',
    color: '#d97757',
  });
  
  const [selectedClients, setSelectedClients] = useState<ClientType[]>([]);

  const availableClients: ClientType[] = ['claude-code', 'claude-desktop', 'codex', 'gemini-cli', 'cursor'];

  const handleClientToggle = (client: ClientType) => {
    if (selectedClients.includes(client)) {
      setSelectedClients(selectedClients.filter(c => c !== client));
    } else {
      setSelectedClients([...selectedClients, client]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Process comma-separated lists
      const traitsList = formData.traits.split(',').map(t => t.trim()).filter(Boolean);
      const capabilitiesList = formData.capabilities.split(',').map(c => c.trim()).filter(Boolean);

      await api.personas.create({
        name: formData.name,
        role: formData.role,
        system_prompt: formData.system_prompt,
        color: formData.color,
        suggested_clients: selectedClients,
        capabilities: capabilitiesList,
        // The API expects personality as a raw object with traits
        // We need to match the structure expected by the backend
        // In the backend it's `personality=data.get('personality', {})`
        // But `Persona` type has `personality: { traits?: string[]; communication_style?: string; }`
        // The API create method in index.ts doesn't explicitly type personality, so we pass it as part of data if we modify the call or assume backend handles it.
        // Wait, looking at `api/routes/personas.py`, it expects `personality` field. 
        // But `web/src/lib/api/index.ts` `create` method signature is:
        // create: (data: { name: string; role: string; system_prompt?: string; suggested_clients?: ClientType[]; color?: string; capabilities?: string[] })
        // It seems the Typescript definition in `index.ts` might be missing `personality`.
        // I will cast it to any or extend the type in the call.
        ...({ personality: { traits: traitsList } } as any)
      });

      router.push('/personas');
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to create persona');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Create New Persona
          </h1>
          <p className="text-cm-coffee mt-1">
            Define a new AI personality and behavior
          </p>
        </div>
        <Link 
          href="/personas"
          className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal transition-colors border border-cm-sand rounded-lg"
        >
          Cancel
        </Link>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-cm-ivory rounded-xl border border-cm-sand shadow-sm p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Display Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
              placeholder="e.g. Senior Architect"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Role ID * (Unique)
            </label>
            <input
              type="text"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta font-mono text-sm"
              placeholder="e.g. architect-agent"
            />
            <p className="text-xs text-cm-coffee mt-1">Unique identifier used by the system</p>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-cm-charcoal mb-1">
            System Prompt
          </label>
          <textarea
            rows={6}
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta font-mono text-sm"
            placeholder="You are an expert software architect..."
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
              placeholder="Analytical, Patient, Detailed (comma separated)"
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
              placeholder="python, system-design, api-review (comma separated)"
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
            disabled={loading}
            className="px-6 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Persona'}
          </button>
        </div>
      </form>
    </div>
  );
}
