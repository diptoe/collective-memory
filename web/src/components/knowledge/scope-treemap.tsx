'use client';

import Link from 'next/link';
import { ScopeStats } from '@/types';
import { cn } from '@/lib/utils';

// Scope display helpers
const SCOPE_COLORS: Record<string, { bg: string; hover: string; text: string }> = {
  domain: { bg: 'bg-blue-100', hover: 'hover:bg-blue-200', text: 'text-blue-800' },
  team: { bg: 'bg-green-100', hover: 'hover:bg-green-200', text: 'text-green-800' },
  user: { bg: 'bg-purple-100', hover: 'hover:bg-purple-200', text: 'text-purple-800' },
};

const SCOPE_ICONS: Record<string, string> = {
  domain: '🌐',
  team: '👥',
  user: '👤',
};

interface ScopeTreemapProps {
  scopes: ScopeStats[];
  totalEntities: number;
}

export function ScopeTreemap({ scopes, totalEntities }: ScopeTreemapProps) {
  if (scopes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-cm-ivory rounded-xl border border-cm-sand">
        <div className="text-center">
          <p className="text-cm-coffee mb-2">No scopes with entities found.</p>
          <p className="text-sm text-cm-coffee/70">
            Create entities to see scope visualization.
          </p>
        </div>
      </div>
    );
  }

  // Sort by entity count descending
  const sortedScopes = [...scopes].sort((a, b) => b.entity_count - a.entity_count);

  // Calculate relative sizes (as percentages)
  const maxCount = sortedScopes[0]?.entity_count || 1;

  return (
    <div className="space-y-4">
      {/* Main visualization - responsive grid */}
      <div className="grid grid-cols-12 gap-2 min-h-[300px]">
        {sortedScopes.map((scope, index) => {
          const colors = SCOPE_COLORS[scope.scope_type] || SCOPE_COLORS.domain;
          const icon = SCOPE_ICONS[scope.scope_type] || '📦';
          const percentage = totalEntities > 0
            ? Math.round((scope.entity_count / totalEntities) * 100)
            : 0;

          // Calculate grid span based on relative size
          // Larger scopes get more columns
          const ratio = scope.entity_count / maxCount;
          let colSpan = Math.max(3, Math.round(ratio * 6)); // 3-6 columns

          // First item gets full width if it's dominant
          if (index === 0 && percentage > 40) {
            colSpan = 12;
          } else if (index === 0 && percentage > 25) {
            colSpan = 8;
          }

          // Smaller items get minimum width
          if (percentage < 10) {
            colSpan = 3;
          }

          return (
            <Link
              key={`${scope.scope_type}-${scope.scope_key}`}
              href={`/entities?scope_type=${scope.scope_type}&scope_key=${scope.scope_key}`}
              className={cn(
                "rounded-lg p-4 transition-all cursor-pointer",
                "flex flex-col justify-between min-h-[100px]",
                colors.bg,
                colors.hover,
                colors.text
              )}
              style={{ gridColumn: `span ${colSpan}` }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-lg">{icon}</span>
                  <span className="font-medium text-sm truncate max-w-[150px]">
                    {scope.name}
                  </span>
                </div>
                <span className="text-xs opacity-70">{percentage}%</span>
              </div>

              <div>
                <p className="text-2xl font-bold">{scope.entity_count}</p>
                <p className="text-xs opacity-70">
                  {scope.entity_count === 1 ? 'entity' : 'entities'}
                  {scope.relationship_count > 0 && ` · ${scope.relationship_count} rels`}
                </p>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm">
        {Object.entries(SCOPE_COLORS).map(([type, colors]) => (
          <div key={type} className="flex items-center gap-2">
            <div className={cn("w-4 h-4 rounded", colors.bg)} />
            <span className="text-cm-coffee capitalize">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
