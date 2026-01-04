/**
 * Collective Memory Platform - Graph Layout Utilities
 *
 * Uses Dagre for automatic graph layout.
 */

import dagre from 'dagre';
import { Node, Edge } from '@xyflow/react';

/**
 * Entity type colors following the Collective Memory design system.
 */
export const TYPE_COLORS: Record<string, string> = {
  Person: '#d97757',      // terracotta
  Project: '#e8a756',     // amber
  Technology: '#5d8a66',  // green
  Organization: '#6b8fa8', // blue
  Document: '#a85a3b',    // sienna
  Concept: '#5c4d3c',     // coffee
  Default: '#8B7355',     // fallback coffee
};

/**
 * Get color for an entity type.
 */
export function getTypeColor(entityType: string): string {
  return TYPE_COLORS[entityType] || TYPE_COLORS.Default;
}

/**
 * Node dimensions for layout calculation.
 */
const NODE_WIDTH = 180;
const NODE_HEIGHT = 60;

/**
 * Layout direction options.
 */
export type LayoutDirection = 'TB' | 'BT' | 'LR' | 'RL';

/**
 * Apply Dagre layout to nodes and edges.
 *
 * @param nodes - React Flow nodes
 * @param edges - React Flow edges
 * @param direction - Layout direction (TB, BT, LR, RL)
 * @returns Nodes with updated positions
 */
export function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  direction: LayoutDirection = 'TB'
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR' || direction === 'RL';

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 80,
    ranksep: 100,
    edgesep: 30,
    marginx: 40,
    marginy: 40,
  });

  // Add nodes to dagre
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    });
  });

  // Add edges to dagre
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Run layout
  dagre.layout(dagreGraph);

  // Apply positions to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
      targetPosition: isHorizontal ? 'left' : 'top',
      sourcePosition: isHorizontal ? 'right' : 'bottom',
    } as Node;
  });

  return { nodes: layoutedNodes, edges };
}

/**
 * Convert entity data to React Flow node.
 */
export function entityToNode(entity: {
  entity_key: string;
  name: string;
  entity_type: string;
  properties?: Record<string, unknown>;
}): Node {
  return {
    id: entity.entity_key,
    type: 'entityNode',
    data: {
      label: entity.name,
      entityType: entity.entity_type,
      properties: entity.properties || {},
      color: getTypeColor(entity.entity_type),
    },
    position: { x: 0, y: 0 }, // Will be set by layout
  };
}

/**
 * Convert relationship data to React Flow edge.
 */
export function relationshipToEdge(relationship: {
  relationship_key: string;
  from_entity_key: string;
  to_entity_key: string;
  relationship_type: string;
  properties?: Record<string, unknown>;
}): Edge {
  return {
    id: relationship.relationship_key,
    source: relationship.from_entity_key,
    target: relationship.to_entity_key,
    type: 'relationshipEdge',
    data: {
      label: relationship.relationship_type,
      properties: relationship.properties || {},
    },
    animated: false,
  };
}

/**
 * Get unique entity types from a list of entities.
 */
export function getEntityTypes(entities: Array<{ entity_type: string }>): string[] {
  return [...new Set(entities.map((e) => e.entity_type))].sort();
}
