'use client';

import { memo } from 'react';
import {
  type EdgeProps,
  type Edge,
  getBezierPath,
  EdgeLabelRenderer,
} from '@xyflow/react';

/**
 * Relationship edge data structure.
 */
export interface RelationshipEdgeData extends Record<string, unknown> {
  label: string;
  properties?: Record<string, unknown>;
}

/**
 * Relationship edge type for React Flow.
 */
export type RelationshipEdgeType = Edge<RelationshipEdgeData, 'relationshipEdge'>;

/**
 * Custom relationship edge for the knowledge graph.
 */
export const RelationshipEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
  selected,
}: EdgeProps<RelationshipEdgeType>) => {
  const label = data?.label || '';

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <path
        id={id}
        className={`
          stroke-cm-coffee fill-none transition-all duration-200
          ${selected ? 'stroke-cm-terracotta stroke-[3]' : 'stroke-[2]'}
        `}
        d={edgePath}
        markerEnd={markerEnd}
      />
      {label && (
        <EdgeLabelRenderer>
          <div
            className={`
              absolute px-2 py-0.5 rounded text-[10px] font-medium
              pointer-events-none select-none
              ${selected
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-charcoal'
              }
            `}
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
          >
            {label.replace(/_/g, ' ')}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

RelationshipEdge.displayName = 'RelationshipEdge';
