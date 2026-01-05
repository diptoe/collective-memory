'use client';

import { Persona } from '@/types';
import { cn } from '@/lib/utils';

interface PersonaCardProps {
  persona: Persona;
  onClick?: () => void;
  selected?: boolean;
}

export function PersonaCard({ persona, onClick, selected }: PersonaCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'p-4 rounded-xl border transition-all',
        onClick && 'cursor-pointer hover:shadow-md',
        selected
          ? 'border-cm-terracotta bg-cm-terracotta/5'
          : 'border-cm-sand bg-cm-ivory hover:border-cm-terracotta/50'
      )}
    >
      <div className="flex items-start gap-4">
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-cm-ivory text-lg font-medium flex-shrink-0"
          style={{ backgroundColor: persona.color }}
        >
          {persona.name[0]}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-cm-charcoal">{persona.name}</h3>
            <span
              className={cn(
                'px-2 py-0.5 text-xs rounded-full',
                persona.status === 'active'
                  ? 'bg-cm-success/20 text-cm-success'
                  : persona.status === 'inactive'
                  ? 'bg-cm-sand text-cm-coffee'
                  : 'bg-cm-error/20 text-cm-error'
              )}
            >
              {persona.status}
            </span>
          </div>

          <p className="text-sm text-cm-coffee mt-0.5">{persona.role}</p>
          {persona.suggested_clients && persona.suggested_clients.length > 0 && (
            <p className="text-xs text-cm-coffee/70 mt-1">
              For: {persona.suggested_clients.join(', ')}
            </p>
          )}

          {persona.personality?.traits && persona.personality.traits.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {persona.personality.traits.slice(0, 4).map((trait) => (
                <span
                  key={trait}
                  className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee"
                >
                  {trait}
                </span>
              ))}
            </div>
          )}

          {persona.capabilities && persona.capabilities.length > 0 && (
            <div className="mt-2 text-xs text-cm-coffee/70">
              {persona.capabilities.length} capabilities
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
