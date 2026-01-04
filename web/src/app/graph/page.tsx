'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { Entity, Relationship } from '@/types';
import { KnowledgeGraph } from '@/components/graph';

export default function GraphPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadGraph() {
      try {
        const [entRes, relRes] = await Promise.all([
          api.entities.list(),
          api.relationships.list(),
        ]);
        setEntities(entRes.data?.entities || []);
        setRelationships(relRes.data?.relationships || []);
      } catch (err) {
        console.error('Failed to load graph data:', err);
        setError('Failed to load graph data');
      } finally {
        setLoading(false);
      }
    }

    loadGraph();
  }, []);

  const handleEntitySelect = useCallback((entity: Entity | null) => {
    // Future: could sync with URL or global state
    if (entity) {
      console.log('Selected entity:', entity.name);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading graph...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-cm-terracotta mb-2">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="text-sm text-cm-coffee hover:text-cm-charcoal underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-cm-sand bg-cm-ivory">
        <div>
          <h1 className="font-serif text-xl font-semibold text-cm-charcoal">
            Knowledge Graph
          </h1>
          <p className="text-sm text-cm-coffee">
            Visualize entities and their relationships
          </p>
        </div>
      </div>

      {/* Graph visualization */}
      <div className="flex-1 overflow-hidden">
        {entities.length === 0 ? (
          <div className="flex items-center justify-center h-full bg-cm-ivory">
            <div className="text-center">
              <div className="mb-6">
                <svg
                  className="w-24 h-24 mx-auto text-cm-terracotta/30"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                  />
                </svg>
              </div>
              <p className="text-cm-coffee mb-4">No entities in the graph yet.</p>
              <p className="text-sm text-cm-coffee/70 max-w-md">
                Create entities to see the knowledge graph visualization.
                Use the chat interface or API to add data to your knowledge graph.
              </p>
            </div>
          </div>
        ) : (
          <KnowledgeGraph
            entities={entities}
            relationships={relationships}
            onEntitySelect={handleEntitySelect}
          />
        )}
      </div>
    </div>
  );
}
