'use client';

import { Persona } from '@/types';

interface PersonaPickerProps {
  personas: Persona[];
  onSelect: (persona: Persona) => void;
  onClose: () => void;
}

export function PersonaPicker({ personas, onSelect, onClose }: PersonaPickerProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-cm-ivory rounded-xl shadow-xl max-w-md w-full mx-4">
        <div className="p-4 border-b border-cm-sand flex items-center justify-between">
          <h3 className="font-serif font-semibold text-cm-charcoal">
            Start a New Conversation
          </h3>
          <button
            onClick={onClose}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4">
          <p className="text-sm text-cm-coffee mb-4">
            Choose a persona to chat with:
          </p>

          <div className="space-y-2 max-h-80 overflow-y-auto">
            {personas.map((persona) => (
              <button
                key={persona.persona_key}
                onClick={() => onSelect(persona)}
                className="w-full flex items-center gap-4 p-3 rounded-lg hover:bg-cm-sand transition-colors text-left"
              >
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center text-cm-ivory text-lg font-medium flex-shrink-0"
                  style={{ backgroundColor: persona.color }}
                >
                  {persona.name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-cm-charcoal">{persona.name}</p>
                  <p className="text-sm text-cm-coffee truncate">{persona.role}</p>
                  {persona.personality?.traits && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {persona.personality.traits.slice(0, 3).map((trait) => (
                        <span
                          key={trait}
                          className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>

          {personas.length === 0 && (
            <p className="text-center text-cm-coffee py-8">
              No personas available. Create one first.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
