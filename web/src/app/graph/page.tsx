'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Entity, Relationship } from '@/types';

export default function GraphPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    }

    loadGraph();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading graph...</p>
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Knowledge Graph
          </h1>
          <p className="text-cm-coffee mt-1">
            Visualize entities and their relationships
          </p>
        </div>
        <div className="flex items-center gap-4 text-sm text-cm-coffee">
          <span>{entities.length} entities</span>
          <span>{relationships.length} relationships</span>
        </div>
      </div>

      {/* Graph visualization placeholder */}
      <div className="flex-1 bg-cm-ivory rounded-xl border border-cm-sand overflow-hidden">
        {entities.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-cm-coffee mb-4">No entities in the graph yet.</p>
              <p className="text-sm text-cm-coffee/70">
                Create entities to see the knowledge graph visualization.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
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
              <p className="text-cm-coffee mb-2">
                Graph Visualization Coming Soon
              </p>
              <p className="text-sm text-cm-coffee/70 max-w-md">
                React Flow integration will be added to visualize the knowledge
                graph with interactive nodes and edges.
              </p>

              {/* Preview stats */}
              <div className="mt-6 grid grid-cols-3 gap-4 max-w-md mx-auto">
                {['Person', 'Project', 'Technology'].map((type) => {
                  const count = entities.filter((e) => e.entity_type === type).length;
                  return (
                    <div key={type} className="p-3 bg-cm-sand/30 rounded-lg">
                      <p className="text-2xl font-semibold text-cm-charcoal">{count}</p>
                      <p className="text-xs text-cm-coffee">{type}s</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
