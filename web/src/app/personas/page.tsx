'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Persona } from '@/types';
import { PersonaCard } from '@/components/persona-card';

export default function PersonasPage() {
  const router = useRouter();
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPersonas() {
      try {
        const res = await api.personas.list({ include_archived: true });
        setPersonas(res.data?.personas || []);
      } catch (err) {
        console.error('Failed to load personas:', err);
      } finally {
        setLoading(false);
      }
    }

    loadPersonas();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading personas...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Personas
          </h1>
          <p className="text-cm-coffee mt-1">
            Manage AI model personalities and configurations
          </p>
        </div>
        <Link 
          href="/personas/new"
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
        >
          + New Persona
        </Link>
      </div>

      {personas.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-cm-coffee mb-4">No personas configured yet.</p>
          <p className="text-sm text-cm-coffee/70">
            Personas will be seeded when the API starts for the first time.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {personas.map((persona) => (
            <PersonaCard
              key={persona.persona_key}
              persona={persona}
              onClick={() => router.push(`/personas/${persona.persona_key}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
