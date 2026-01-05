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
  const [searchQuery, setSearchQuery] = useState('');

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

  // Navigate to entity detail page
  const handleEntityClick = (entity: Entity) => {
    router.push(`/entities/${encodeURIComponent(entity.entity_type)}/${entity.entity_key}`);
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
              onClick={() => handleEntityClick(entity)}
            />
          ))}
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
