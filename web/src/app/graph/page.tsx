'use client';

import { useEffect, useState, useCallback } from 'react';
import { X, Search, Focus } from 'lucide-react';
import { api } from '@/lib/api';
import { Entity, Relationship } from '@/types';
import { KnowledgeGraph } from '@/components/graph';

export default function GraphPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusedEntityKey, setFocusedEntityKey] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    async function loadGraph() {
      try {
        // Fetch more entities for the graph (default is 100)
        const [entRes, relRes] = await Promise.all([
          api.entities.list({ limit: '1000' }),
          api.relationships.list({ limit: 5000 }),
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

  const handleFocusEntity = useCallback((entityKey: string | null) => {
    setFocusedEntityKey(entityKey);
    // Clear search when focusing
    if (entityKey) {
      setSearchQuery('');
    }
  }, []);

  // Get focused entity name for display
  const focusedEntity = focusedEntityKey
    ? entities.find((e) => e.entity_key === focusedEntityKey)
    : null;

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
      <div className="flex items-center justify-between p-4 border-b border-cm-sand bg-cm-ivory gap-4">
        <div className="flex-shrink-0">
          <h1 className="font-serif text-xl font-semibold text-cm-charcoal">
            Knowledge Graph
          </h1>
          <p className="text-sm text-cm-coffee">
            Visualize entities and their relationships
          </p>
        </div>

        {/* Focus indicator */}
        {focusedEntity && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-cm-terracotta/10 border border-cm-terracotta/30 rounded-lg">
            <Focus className="w-4 h-4 text-cm-terracotta" />
            <span className="text-sm text-cm-charcoal">
              Focused: <strong>{focusedEntity.name}</strong>
            </span>
            <button
              onClick={() => setFocusedEntityKey(null)}
              className="p-0.5 text-cm-terracotta hover:text-cm-sienna transition-colors"
              title="Clear focus"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Search box */}
        <div className="relative flex-shrink-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cm-coffee/50" />
          <input
            type="text"
            placeholder="Filter entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-64 pl-9 pr-8 py-2 text-sm border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta bg-white"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-cm-coffee/50 hover:text-cm-coffee transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
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
            focusedEntityKey={focusedEntityKey}
            onFocusEntity={handleFocusEntity}
            searchQuery={searchQuery}
          />
        )}
      </div>
    </div>
  );
}
