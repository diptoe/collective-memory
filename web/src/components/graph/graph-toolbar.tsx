'use client';

import { LayoutGrid, ArrowDown, ArrowRight, ArrowUp, ArrowLeft } from 'lucide-react';
import { LayoutDirection } from '@/lib/graph/layout';

interface GraphToolbarProps {
  layoutDirection: LayoutDirection;
  onLayoutChange: (direction: LayoutDirection) => void;
  entityCount: number;
  relationshipCount: number;
  totalEntityCount?: number;
  totalRelationshipCount?: number;
}

/**
 * Layout direction options with icons.
 */
const layoutOptions: { direction: LayoutDirection; icon: typeof ArrowDown; label: string }[] = [
  { direction: 'TB', icon: ArrowDown, label: 'Top to Bottom' },
  { direction: 'BT', icon: ArrowUp, label: 'Bottom to Top' },
  { direction: 'LR', icon: ArrowRight, label: 'Left to Right' },
  { direction: 'RL', icon: ArrowLeft, label: 'Right to Left' },
];

/**
 * Graph toolbar with layout controls and stats.
 */
export function GraphToolbar({
  layoutDirection,
  onLayoutChange,
  entityCount,
  relationshipCount,
  totalEntityCount,
  totalRelationshipCount,
}: GraphToolbarProps) {
  const isFiltered = totalEntityCount !== undefined && entityCount !== totalEntityCount;

  return (
    <div className="absolute top-4 left-4 flex items-center gap-3 z-10">
      {/* Layout controls */}
      <div className="flex items-center gap-1 bg-cm-ivory border border-cm-sand rounded-lg p-1 shadow-sm">
        <div className="px-2 py-1 text-cm-coffee">
          <LayoutGrid className="w-4 h-4" />
        </div>
        {layoutOptions.map(({ direction, icon: Icon, label }) => (
          <button
            key={direction}
            onClick={() => onLayoutChange(direction)}
            className={`
              p-1.5 rounded transition-colors
              ${layoutDirection === direction
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'text-cm-coffee hover:bg-cm-sand'
              }
            `}
            title={label}
          >
            <Icon className="w-4 h-4" />
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-3 bg-cm-ivory border border-cm-sand rounded-lg px-3 py-1.5 shadow-sm text-sm">
        <span className="text-cm-charcoal font-medium">
          {entityCount}
          {isFiltered && (
            <span className="text-cm-coffee font-normal">/{totalEntityCount}</span>
          )}
        </span>
        <span className="text-cm-coffee">entities</span>
        <span className="text-cm-sand">|</span>
        <span className="text-cm-charcoal font-medium">
          {relationshipCount}
          {isFiltered && totalRelationshipCount !== undefined && (
            <span className="text-cm-coffee font-normal">/{totalRelationshipCount}</span>
          )}
        </span>
        <span className="text-cm-coffee">relationships</span>
        {isFiltered && (
          <>
            <span className="text-cm-sand">|</span>
            <span className="text-cm-terracotta text-xs">filtered</span>
          </>
        )}
      </div>
    </div>
  );
}
