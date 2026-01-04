'use client';

import { TYPE_COLORS } from '@/lib/graph/layout';
import { cn } from '@/lib/utils';

interface GraphLegendProps {
  entityTypes: string[];
  visibleTypes?: Set<string>;
  onToggleType?: (type: string) => void;
  onShowAll?: () => void;
  onHideAll?: () => void;
}

/**
 * Legend showing entity type colors with toggle functionality.
 * Renders as a horizontal scrollable bar across the bottom of the graph.
 */
export function GraphLegend({
  entityTypes,
  visibleTypes,
  onToggleType,
  onShowAll,
  onHideAll,
}: GraphLegendProps) {
  if (entityTypes.length === 0) return null;

  const isInteractive = !!onToggleType;
  const allVisible = !visibleTypes || visibleTypes.size === entityTypes.length;
  const noneVisible = visibleTypes && visibleTypes.size === 0;
  const visibleCount = visibleTypes?.size ?? entityTypes.length;

  return (
    <div className="absolute bottom-0 left-0 right-0 bg-cm-ivory border-t border-cm-sand z-10">
      <div className="flex items-center gap-4 px-4 py-2">
        {/* Label and controls */}
        <div className="flex items-center gap-2 shrink-0">
          <p className="text-xs font-medium text-cm-coffee uppercase tracking-wider">
            Filter
          </p>
          {isInteractive && (
            <div className="flex gap-1">
              <button
                onClick={onShowAll}
                disabled={allVisible}
                className={cn(
                  'text-xs px-2 py-1 rounded border transition-colors',
                  allVisible
                    ? 'text-cm-coffee/40 border-cm-sand/50 cursor-not-allowed'
                    : 'text-cm-terracotta border-cm-terracotta/30 hover:bg-cm-terracotta/10'
                )}
              >
                All
              </button>
              <button
                onClick={onHideAll}
                disabled={noneVisible}
                className={cn(
                  'text-xs px-2 py-1 rounded border transition-colors',
                  noneVisible
                    ? 'text-cm-coffee/40 border-cm-sand/50 cursor-not-allowed'
                    : 'text-cm-coffee border-cm-sand hover:bg-cm-sand'
                )}
              >
                None
              </button>
            </div>
          )}
          {isInteractive && visibleCount < entityTypes.length && (
            <span className="text-xs text-cm-coffee/60">
              ({visibleCount}/{entityTypes.length})
            </span>
          )}
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-cm-sand shrink-0" />

        {/* Scrollable type buttons */}
        <div className="flex-1 overflow-x-auto">
          <div className="flex items-center gap-2">
            {entityTypes.map((type) => {
              const color = TYPE_COLORS[type] || TYPE_COLORS.Default;
              const isVisible = !visibleTypes || visibleTypes.has(type);

              return (
                <button
                  key={type}
                  onClick={() => onToggleType?.(type)}
                  disabled={!isInteractive}
                  className={cn(
                    'flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all whitespace-nowrap shrink-0',
                    isInteractive && 'cursor-pointer',
                    !isInteractive && 'cursor-default',
                    isVisible
                      ? 'border-transparent'
                      : 'border-cm-sand bg-transparent opacity-50'
                  )}
                  style={{
                    backgroundColor: isVisible ? `${color}20` : 'transparent',
                    borderColor: isVisible ? `${color}40` : undefined,
                  }}
                >
                  <div
                    className={cn(
                      'w-3 h-3 rounded-full transition-all shrink-0',
                      !isVisible && 'ring-1 ring-cm-coffee/30'
                    )}
                    style={{
                      backgroundColor: isVisible ? color : 'transparent',
                    }}
                  />
                  <span className={cn(
                    'text-sm transition-colors',
                    isVisible ? 'text-cm-charcoal' : 'text-cm-coffee line-through'
                  )}>
                    {type}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
