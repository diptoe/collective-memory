'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { EntityCard } from '@/components/entity-card';
import { cn } from '@/lib/utils';

interface EntityTypeInfo {
  type: string;
  count: number;
}

function EntitiesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityTypes, setEntityTypes] = useState<EntityTypeInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleting, setDeleting] = useState(false);

  // Read filter from URL query param, default to 'all'
  const filterType = searchParams.get('type') || 'all';

  // Update URL when filter changes
  const setFilterType = (type: string) => {
    if (type === 'all') {
      router.push('/entities');
    } else {
      router.push(`/entities?type=${encodeURIComponent(type)}`);
    }
  };

  // Known entity types get dedicated routes, others show modal
  const KNOWN_ENTITY_TYPES = ['Repository', 'Document', 'Project'];

  const handleEntityClick = (entity: Entity) => {
    if (KNOWN_ENTITY_TYPES.includes(entity.entity_type)) {
      router.push(`/entities/${entity.entity_type.toLowerCase()}/${entity.entity_key}`);
    } else {
      setSelectedEntity(entity);
    }
  };

  const handleDelete = async (entity: Entity) => {
    if (!confirm(`Delete "${entity.name}"? This will also delete all relationships. This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    try {
      await api.entities.delete(entity.entity_key);
      setEntities((prev) => prev.filter((e) => e.entity_key !== entity.entity_key));
      setSelectedEntity(null);
    } catch (err) {
      console.error('Failed to delete entity:', err);
      alert('Failed to delete entity');
    } finally {
      setDeleting(false);
    }
  };

  // Load entity types on mount
  useEffect(() => {
    async function loadTypes() {
      try {
        const res = await api.entities.types();
        setEntityTypes(res.data?.types || []);
      } catch (err) {
        console.error('Failed to load entity types:', err);
      }
    }
    loadTypes();
  }, []);

  // Load entities when filter changes
  useEffect(() => {
    async function loadEntities() {
      try {
        const params: Record<string, string> = {};
        if (filterType !== 'all') {
          params.type = filterType;
        }
        const res = await api.entities.list(params);
        setEntities(res.data?.entities || []);
      } catch (err) {
        console.error('Failed to load entities:', err);
      } finally {
        setLoading(false);
      }
    }

    loadEntities();
  }, [filterType]);

  const filteredEntities = entities.filter((entity) =>
    entity.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading entities...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Entities
          </h1>
          <p className="text-cm-coffee mt-1">
            Browse and manage entities in the knowledge graph
          </p>
        </div>
        <button className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors">
          + New Entity
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <input
          type="text"
          placeholder="Search entities..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 max-w-md px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal"
        />

        <div className="flex items-center gap-1 flex-wrap">
          <button
            onClick={() => setFilterType('all')}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              filterType === 'all'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
            )}
          >
            All
          </button>
          {entityTypes.map((typeInfo) => (
            <button
              key={typeInfo.type}
              onClick={() => setFilterType(typeInfo.type)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                filterType === typeInfo.type
                  ? 'bg-cm-terracotta text-cm-ivory'
                  : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
              )}
            >
              {typeInfo.type}
              <span className="ml-1 opacity-60">({typeInfo.count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Entity grid */}
      {filteredEntities.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-cm-coffee mb-4">No entities found.</p>
          <p className="text-sm text-cm-coffee/70">
            Create your first entity or adjust your filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEntities.map((entity) => (
            <EntityCard
              key={entity.entity_key}
              entity={entity}
              selected={selectedEntity?.entity_key === entity.entity_key}
              onClick={() => handleEntityClick(entity)}
            />
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selectedEntity && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-40"
          onClick={() => setSelectedEntity(null)}
        >
          <div
            className="bg-cm-ivory rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-cm-sand flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-cm-charcoal">
                  {selectedEntity.name}
                </h3>
                <p className="text-sm text-cm-coffee">{selectedEntity.entity_type}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDelete(selectedEntity)}
                  disabled={deleting}
                  className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
                >
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
                <button
                  onClick={() => setSelectedEntity(null)}
                  className="text-cm-coffee hover:text-cm-charcoal transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-cm-coffee mb-1">Key</h4>
                  <p className="font-mono text-sm text-cm-charcoal">
                    {selectedEntity.entity_key}
                  </p>
                </div>

                {selectedEntity.context_domain && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Context Domain</h4>
                    <p className="font-mono text-sm text-cm-charcoal">
                      {selectedEntity.context_domain}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium text-cm-coffee mb-1">Confidence</h4>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-32 rounded-full bg-cm-sand overflow-hidden">
                      <div
                        className="h-full rounded-full bg-cm-terracotta"
                        style={{ width: `${selectedEntity.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-cm-charcoal">
                      {Math.round(selectedEntity.confidence * 100)}%
                    </span>
                  </div>
                </div>

                {selectedEntity.properties && Object.keys(selectedEntity.properties).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-2">Properties</h4>
                    <pre className="text-sm text-cm-charcoal bg-cm-sand/30 p-3 rounded-lg overflow-auto">
                      {JSON.stringify(selectedEntity.properties, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedEntity.relationships && (
                  <>
                    {selectedEntity.relationships.outgoing.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-cm-coffee mb-2">
                          Outgoing Relationships ({selectedEntity.relationships.outgoing.length})
                        </h4>
                        <div className="space-y-2">
                          {selectedEntity.relationships.outgoing.map((rel) => (
                            <div
                              key={rel.relationship_key}
                              className="flex items-center gap-2 text-sm p-2 bg-cm-sand/30 rounded-lg flex-wrap"
                            >
                              <span className="text-cm-charcoal font-medium">{selectedEntity.name}</span>
                              <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                                {rel.relationship_type}
                              </span>
                              <span className="text-cm-charcoal font-medium">
                                {rel.to_entity?.name || rel.to_entity_key}
                              </span>
                              {rel.to_entity?.entity_type && (
                                <span className="text-xs text-cm-coffee">
                                  ({rel.to_entity.entity_type})
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedEntity.relationships.incoming.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-cm-coffee mb-2">
                          Incoming Relationships ({selectedEntity.relationships.incoming.length})
                        </h4>
                        <div className="space-y-2">
                          {selectedEntity.relationships.incoming.map((rel) => (
                            <div
                              key={rel.relationship_key}
                              className="flex items-center gap-2 text-sm p-2 bg-cm-sand/30 rounded-lg flex-wrap"
                            >
                              <span className="text-cm-charcoal font-medium">
                                {rel.from_entity?.name || rel.from_entity_key}
                              </span>
                              {rel.from_entity?.entity_type && (
                                <span className="text-xs text-cm-coffee">
                                  ({rel.from_entity.entity_type})
                                </span>
                              )}
                              <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                                {rel.relationship_type}
                              </span>
                              <span className="text-cm-charcoal font-medium">{selectedEntity.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function EntitiesPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading entities...</p>
      </div>
    }>
      <EntitiesContent />
    </Suspense>
  );
}
