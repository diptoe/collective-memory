'use client';

import Link from 'next/link';
import { ScopeStats } from '@/types';

// Scope display helpers - using standard brand colors
const SCOPE_ICONS: Record<string, string> = {
  domain: '🌐',
  team: '👥',
  user: '👤',
};

interface ScopeCardProps {
  scope: ScopeStats;
  totalEntities: number;
}

export function ScopeCard({ scope, totalEntities }: ScopeCardProps) {
  const icon = SCOPE_ICONS[scope.scope_type] || '📦';
  const percentage = totalEntities > 0
    ? Math.round((scope.entity_count / totalEntities) * 100)
    : 0;

  // Get top 3 entity types
  const topTypes = Object.entries(scope.entity_types)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <Link
      href={`/entities?scope_type=${scope.scope_type}&scope_key=${scope.scope_key}`}
      className="block rounded-xl border p-4 transition-all hover:shadow-md hover:-translate-y-0.5 bg-cm-ivory border-cm-sand hover:border-cm-terracotta/50"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <div>
            <h3 className="font-medium text-cm-charcoal leading-tight">{scope.name}</h3>
            <span className="text-xs text-cm-coffee capitalize">{scope.scope_type}</span>
          </div>
        </div>
        <span className="text-xs text-cm-coffee bg-cm-sand/50 px-2 py-0.5 rounded-full">
          {percentage}%
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-2xl font-semibold text-cm-charcoal">{scope.entity_count}</p>
          <p className="text-xs text-cm-coffee">entities</p>
        </div>
        <div>
          <p className="text-2xl font-semibold text-cm-charcoal">{scope.relationship_count}</p>
          <p className="text-xs text-cm-coffee">relationships</p>
        </div>
      </div>

      {/* Top entity types */}
      {topTypes.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {topTypes.map(([type, count]) => (
            <span
              key={type}
              className="text-xs bg-cm-sand/50 text-cm-coffee px-2 py-0.5 rounded"
            >
              {type}: {count}
            </span>
          ))}
          {Object.keys(scope.entity_types).length > 3 && (
            <span className="text-xs text-cm-coffee/60">
              +{Object.keys(scope.entity_types).length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Progress bar */}
      <div className="mt-3 h-1.5 bg-cm-sand/50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all bg-cm-terracotta"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </Link>
  );
}
