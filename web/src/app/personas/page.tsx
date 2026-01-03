'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Persona } from '@/types';
import { PersonaCard } from '@/components/persona-card';

export default function PersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);

  useEffect(() => {
    async function loadPersonas() {
      try {
        const res = await api.personas.list();
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
        <button className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors">
          + New Persona
        </button>
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
              selected={selectedPersona?.persona_key === persona.persona_key}
              onClick={() => setSelectedPersona(persona)}
            />
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selectedPersona && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-cm-ivory rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b border-cm-sand flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-cm-ivory font-medium"
                  style={{ backgroundColor: selectedPersona.color }}
                >
                  {selectedPersona.name[0]}
                </div>
                <div>
                  <h3 className="font-semibold text-cm-charcoal">
                    {selectedPersona.name}
                  </h3>
                  <p className="text-sm text-cm-coffee">{selectedPersona.role}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedPersona(null)}
                className="text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-cm-coffee mb-1">Model</h4>
                  <p className="font-mono text-cm-charcoal">{selectedPersona.model}</p>
                </div>

                {selectedPersona.system_prompt && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">System Prompt</h4>
                    <pre className="text-sm text-cm-charcoal bg-cm-sand/30 p-3 rounded-lg whitespace-pre-wrap">
                      {selectedPersona.system_prompt}
                    </pre>
                  </div>
                )}

                {selectedPersona.personality?.traits && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-2">Personality Traits</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedPersona.personality.traits.map((trait) => (
                        <span
                          key={trait}
                          className="px-3 py-1 text-sm bg-cm-sand rounded-full text-cm-coffee"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedPersona.capabilities && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-2">Capabilities</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedPersona.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="px-3 py-1 text-sm bg-cm-terracotta/10 rounded-full text-cm-terracotta"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
