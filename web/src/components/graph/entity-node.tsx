'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';

/**
 * Entity node data structure.
 */
export interface EntityNodeData extends Record<string, unknown> {
  label: string;
  entityType: string;
  properties?: Record<string, unknown>;
  color: string;
}

/**
 * Entity node type for React Flow.
 */
export type EntityNodeType = Node<EntityNodeData, 'entityNode'>;

/**
 * Custom entity node for the knowledge graph.
 */
export const EntityNode = memo(({ data, selected }: NodeProps<EntityNodeType>) => {
  const { label, entityType, color } = data;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg shadow-md border-2 min-w-[140px] max-w-[200px]
        transition-all duration-200 cursor-pointer
        ${selected ? 'ring-2 ring-offset-2 ring-cm-terracotta' : ''}
      `}
      style={{
        backgroundColor: `${color}15`,
        borderColor: color,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-cm-charcoal !w-2 !h-2"
      />

      {/* Entity type badge */}
      <div
        className="text-[10px] font-medium uppercase tracking-wider mb-1 opacity-80"
        style={{ color }}
      >
        {entityType}
      </div>

      {/* Entity name */}
      <div className="font-medium text-sm text-cm-charcoal truncate">
        {label}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-cm-charcoal !w-2 !h-2"
      />
    </div>
  );
});

EntityNode.displayName = 'EntityNode';
