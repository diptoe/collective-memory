'use client';

import { Entity } from '@/types';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';

interface EntityCardProps {
  entity: Entity;
  onClick?: () => void;
  selected?: boolean;
}

const entityTypeColors: Record<string, string> = {
  Person: '#d97757',
  Project: '#e8a756',
  Technology: '#5d8a66',
  Document: '#6b8fa8',
  Organization: '#a85a3b',
  Concept: '#5c4d3c',
  Repository: '#7c5cbf',
};

export function EntityCard({ entity, onClick, selected }: EntityCardProps) {
  const color = entityTypeColors[entity.entity_type] || '#5c4d3c';

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
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-cm-ivory text-sm font-medium flex-shrink-0"
          style={{ backgroundColor: color }}
        >
          {entity.entity_type[0]}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-cm-charcoal truncate">{entity.name}</h3>
            <span
              className="px-2 py-0.5 text-xs rounded-full"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {entity.entity_type}
            </span>
          </div>

          {entity.context_domain && (
            <p className="text-xs text-cm-coffee/70 mt-0.5 font-mono">
              {entity.context_domain}
            </p>
          )}

          {entity.properties && Object.keys(entity.properties).length > 0 && (
            <div className="mt-2 text-xs text-cm-coffee">
              {Object.keys(entity.properties).slice(0, 3).map((key) => (
                <span key={key} className="inline-block mr-2">
                  <span className="text-cm-coffee/50">{key}:</span>{' '}
                  {String(entity.properties[key]).slice(0, 20)}
                </span>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <div
                className="h-1.5 w-16 rounded-full bg-cm-sand overflow-hidden"
                title={`Confidence: ${Math.round(entity.confidence * 100)}%`}
              >
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${entity.confidence * 100}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
              <span className="text-xs text-cm-coffee/50">
                {Math.round(entity.confidence * 100)}%
              </span>
            </div>
            <span className="text-xs text-cm-coffee/50">
              {formatDate(entity.created_at)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
