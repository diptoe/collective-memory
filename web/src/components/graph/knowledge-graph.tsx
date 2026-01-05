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
  focusedEntityKey?: string | null;
  onFocusEntity?: (entityKey: string | null) => void;
  searchQuery?: string;
}

/**
 * Internal graph component with React Flow hooks.
 */
function KnowledgeGraphInner({
  entities,
  relationships,
  onEntitySelect,
  focusedEntityKey,
  onFocusEntity,
  searchQuery,
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

  // Get entities connected to the focused entity
  const focusedConnectedKeys = useMemo(() => {
    if (!focusedEntityKey) return null;
    const connectedKeys = new Set<string>([focusedEntityKey]);
    relationships.forEach((r) => {
      if (r.from_entity_key === focusedEntityKey) {
        connectedKeys.add(r.to_entity_key);
      }
      if (r.to_entity_key === focusedEntityKey) {
        connectedKeys.add(r.from_entity_key);
      }
    });
    return connectedKeys;
  }, [focusedEntityKey, relationships]);

  // Get entities matching search query
  const searchMatchedKeys = useMemo(() => {
    if (!searchQuery || searchQuery.trim().length < 2) return null;
    const query = searchQuery.toLowerCase().trim();
    const matchedKeys = new Set<string>();
    entities.forEach((e) => {
      if (
        e.name.toLowerCase().includes(query) ||
        e.entity_type.toLowerCase().includes(query) ||
        e.entity_key.toLowerCase().includes(query)
      ) {
        matchedKeys.add(e.entity_key);
      }
    });
    // Also include connected entities for matched ones
    relationships.forEach((r) => {
      if (matchedKeys.has(r.from_entity_key)) {
        matchedKeys.add(r.to_entity_key);
      }
      if (matchedKeys.has(r.to_entity_key)) {
        matchedKeys.add(r.from_entity_key);
      }
    });
    return matchedKeys;
  }, [searchQuery, entities, relationships]);

  // Filter entities based on visible types, focus, and search
  const filteredEntities = useMemo(() => {
    let filtered = entities.filter((e) => visibleTypes.has(e.entity_type));

    // Apply focus filter (takes precedence)
    if (focusedConnectedKeys) {
      filtered = filtered.filter((e) => focusedConnectedKeys.has(e.entity_key));
    }
    // Apply search filter (only if not focused)
    else if (searchMatchedKeys) {
      filtered = filtered.filter((e) => searchMatchedKeys.has(e.entity_key));
    }

    return filtered;
  }, [entities, visibleTypes, focusedConnectedKeys, searchMatchedKeys]);

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

  // Update nodes/edges when filtered data changes and fit view
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    // Fit view when focus or search filter changes
    setTimeout(() => fitView({ padding: 0.2 }), 50);
  }, [initialNodes, initialEdges, setNodes, setEdges, fitView]);

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
          onFocus={onFocusEntity ? () => onFocusEntity(selectedEntity.entity_key) : undefined}
          isFocused={focusedEntityKey === selectedEntity.entity_key}
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
