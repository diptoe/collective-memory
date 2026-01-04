'use client';

import { useCallback, useMemo, useState } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { Entity, Relationship } from '@/types';
import { EntityNode, EntityNodeData } from './entity-node';
import { RelationshipEdge } from './relationship-edge';
import { GraphLegend } from './graph-legend';
import { NodeDetailsPanel } from './node-details-panel';
import { GraphToolbar } from './graph-toolbar';
import {
  entityToNode,
  relationshipToEdge,
  getLayoutedElements,
  getEntityTypes,
  LayoutDirection,
} from '@/lib/graph/layout';

/**
 * Custom node types for React Flow.
 */
const nodeTypes = {
  entityNode: EntityNode,
};

/**
 * Custom edge types for React Flow.
 */
const edgeTypes = {
  relationshipEdge: RelationshipEdge,
};

interface KnowledgeGraphProps {
  entities: Entity[];
  relationships: Relationship[];
  onEntitySelect?: (entity: Entity | null) => void;
}

/**
 * Internal graph component with React Flow hooks.
 */
function KnowledgeGraphInner({
  entities,
  relationships,
  onEntitySelect,
}: KnowledgeGraphProps) {
  const { fitView } = useReactFlow();
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('TB');

  // Get unique entity types for legend
  const entityTypes = useMemo(() => getEntityTypes(entities), [entities]);

  // Track which entity types are visible (all visible by default)
  const [visibleTypes, setVisibleTypes] = useState<Set<string>>(() => new Set(entityTypes));

  // Update visible types when entity types change
  useMemo(() => {
    setVisibleTypes((prev) => {
      const newTypes = new Set(prev);
      // Add any new types that weren't previously known
      entityTypes.forEach((type) => {
        if (!prev.has(type) && prev.size === 0) {
          newTypes.add(type);
        } else if (prev.size > 0 && !Array.from(prev).some((t) => entityTypes.includes(t))) {
          // If we have no visible types that exist, show all
          entityTypes.forEach((t) => newTypes.add(t));
        }
      });
      return newTypes;
    });
  }, [entityTypes]);

  // Filter entities based on visible types
  const filteredEntities = useMemo(
    () => entities.filter((e) => visibleTypes.has(e.entity_type)),
    [entities, visibleTypes]
  );

  // Filter relationships to only show those between visible entities
  const filteredRelationships = useMemo(() => {
    const visibleEntityKeys = new Set(filteredEntities.map((e) => e.entity_key));
    return relationships.filter(
      (r) => visibleEntityKeys.has(r.from_entity_key) && visibleEntityKeys.has(r.to_entity_key)
    );
  }, [relationships, filteredEntities]);

  // Convert entities and relationships to React Flow format
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const rawNodes = filteredEntities.map(entityToNode);
    const rawEdges = filteredRelationships.map(relationshipToEdge);
    return getLayoutedElements(rawNodes, rawEdges, layoutDirection);
  }, [filteredEntities, filteredRelationships, layoutDirection]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes/edges when filtered data changes
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Toggle type visibility
  const handleToggleType = useCallback((type: string) => {
    setVisibleTypes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(type)) {
        newSet.delete(type);
      } else {
        newSet.add(type);
      }
      return newSet;
    });
  }, []);

  // Show all types
  const handleShowAll = useCallback(() => {
    setVisibleTypes(new Set(entityTypes));
  }, [entityTypes]);

  // Hide all types
  const handleHideAll = useCallback(() => {
    setVisibleTypes(new Set());
  }, []);

  // Handle node selection
  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
      const entity = entities.find((e) => e.entity_key === node.id);
      onEntitySelect?.(entity || null);
    },
    [entities, onEntitySelect]
  );

  // Handle pane click (deselect)
  const handlePaneClick = useCallback(() => {
    setSelectedNode(null);
    onEntitySelect?.(null);
  }, [onEntitySelect]);

  // Re-layout graph
  const handleLayout = useCallback(
    (direction: LayoutDirection) => {
      setLayoutDirection(direction);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodes,
        edges,
        direction
      );
      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
      setTimeout(() => fitView({ padding: 0.2 }), 50);
    },
    [nodes, edges, setNodes, setEdges, fitView]
  );

  // Fit view on mount
  const handleInit = useCallback(() => {
    setTimeout(() => fitView({ padding: 0.2 }), 100);
  }, [fitView]);

  // Get selected entity for details panel
  const selectedEntity = selectedNode
    ? entities.find((e) => e.entity_key === selectedNode.id)
    : null;

  // Get relationships for selected entity
  const selectedRelationships = selectedEntity
    ? relationships.filter(
        (r) =>
          r.from_entity_key === selectedEntity.entity_key ||
          r.to_entity_key === selectedEntity.entity_key
      )
    : [];

  return (
    <div className="relative w-full h-full pb-12">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        onInit={handleInit}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-left"
        className="bg-cm-ivory"
        defaultEdgeOptions={{
          type: 'relationshipEdge',
        }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#5c4d3c20"
        />
        <Controls
          position="bottom-right"
          className="!bg-cm-ivory !border-cm-sand !shadow-md"
        />
      </ReactFlow>

      {/* Graph toolbar */}
      <GraphToolbar
        layoutDirection={layoutDirection}
        onLayoutChange={handleLayout}
        entityCount={filteredEntities.length}
        relationshipCount={filteredRelationships.length}
        totalEntityCount={entities.length}
        totalRelationshipCount={relationships.length}
      />

      {/* Legend with type filtering */}
      <GraphLegend
        entityTypes={entityTypes}
        visibleTypes={visibleTypes}
        onToggleType={handleToggleType}
        onShowAll={handleShowAll}
        onHideAll={handleHideAll}
      />

      {/* Node details panel */}
      {selectedEntity && (
        <NodeDetailsPanel
          entity={selectedEntity}
          relationships={selectedRelationships}
          allEntities={entities}
          onClose={() => {
            setSelectedNode(null);
            onEntitySelect?.(null);
          }}
        />
      )}
    </div>
  );
}

/**
 * Knowledge graph visualization component.
 * Wraps React Flow with custom nodes and edges for the Collective Memory platform.
 */
export function KnowledgeGraph(props: KnowledgeGraphProps) {
  return (
    <ReactFlowProvider>
      <KnowledgeGraphInner {...props} />
    </ReactFlowProvider>
  );
}
