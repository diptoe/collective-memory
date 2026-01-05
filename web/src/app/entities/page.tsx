'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { EntityCard } from '@/components/entity-card';
import { cn } from '@/lib/utils';
import { TYPE_COLORS } from '@/lib/graph/layout';

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

  // Read filter from URL query param - null means show types summary
  const filterType = searchParams.get('type');
  const browseAll = filterType === 'all';
  const showTypesSummary = !filterType;

  // Navigate to entity detail page
  // Use lowercase for type-specific routes (repository, document, project)
  const handleEntityClick = (entity: Entity) => {
    const typeLower = entity.entity_type.toLowerCase();
    router.push(`/entities/${encodeURIComponent(typeLower)}/${entity.entity_key}`);
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

  // Load entities when filter changes (only if a type is selected or browse all)
  useEffect(() => {
    async function loadEntities() {
      if (showTypesSummary) {
        setLoading(false);
        return;
      }
      try {
        const params: Record<string, string> = {};
        if (!browseAll && filterType) {
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
  }, [filterType, showTypesSummary, browseAll]);

  const filteredEntities = entities.filter((entity) =>
    entity.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalEntities = entityTypes.reduce((sum, t) => sum + t.count, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading...</p>
      </div>
    );
  }

  // Types summary view (default)
  if (showTypesSummary) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Entities
            </h1>
            <p className="text-cm-coffee mt-1">
              Browse and manage entities in the knowledge graph
            </p>
          </div>
          <Link
            href="/entities?type=all"
            className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
          >
            Browse All
          </Link>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
            <p className="text-sm text-cm-coffee">Total Types</p>
            <p className="text-3xl font-semibold text-cm-charcoal mt-1">{entityTypes.length}</p>
          </div>
          <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
            <p className="text-sm text-cm-coffee">Total Entities</p>
            <p className="text-3xl font-semibold text-cm-charcoal mt-1">{totalEntities}</p>
          </div>
          <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
            <p className="text-sm text-cm-coffee">Avg per Type</p>
            <p className="text-3xl font-semibold text-cm-charcoal mt-1">
              {entityTypes.length > 0 ? Math.round(totalEntities / entityTypes.length) : 0}
            </p>
          </div>
          <div className="bg-cm-ivory rounded-xl p-4 border border-cm-sand">
            <p className="text-sm text-cm-coffee">Most Common</p>
            <p className="text-xl font-semibold text-cm-charcoal mt-1 truncate">
              {entityTypes.length > 0 ? entityTypes.reduce((a, b) => a.count > b.count ? a : b).type : '-'}
            </p>
          </div>
        </div>

        {/* Types grid */}
        {entityTypes.length === 0 ? (
          <div className="text-center py-12 bg-cm-ivory rounded-xl border border-cm-sand">
            <p className="text-cm-coffee mb-2">No entity types found.</p>
            <p className="text-sm text-cm-coffee/70">
              Create entities to see types appear here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {entityTypes
              .sort((a, b) => b.count - a.count)
              .map((typeInfo) => {
                const percentage = totalEntities > 0
                  ? Math.round((typeInfo.count / totalEntities) * 100)
                  : 0;
                const color = TYPE_COLORS[typeInfo.type] || TYPE_COLORS.Default;

                return (
                  <Link
                    key={typeInfo.type}
                    href={`/entities?type=${encodeURIComponent(typeInfo.type)}`}
                    className="bg-cm-ivory rounded-xl border border-cm-sand p-4 hover:shadow-md transition-shadow group"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold"
                        style={{ backgroundColor: color }}
                      >
                        {typeInfo.type.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-xs text-cm-coffee bg-cm-sand px-2 py-1 rounded-full">
                        {percentage}%
                      </span>
                    </div>

                    <h3 className="font-medium text-cm-charcoal group-hover:text-cm-terracotta transition-colors">
                      {typeInfo.type}
                    </h3>

                    <p className="text-2xl font-semibold text-cm-charcoal mt-1">
                      {typeInfo.count}
                      <span className="text-sm font-normal text-cm-coffee ml-1">
                        {typeInfo.count === 1 ? 'entity' : 'entities'}
                      </span>
                    </p>

                    {/* Progress bar */}
                    <div className="mt-3 h-1.5 bg-cm-sand rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ backgroundColor: color, width: `${percentage}%` }}
                      />
                    </div>
                  </Link>
                );
              })}
          </div>
        )}
      </div>
    );
  }

  // Entity list view (when type is selected or browse all)
  const displayType = browseAll ? 'All Entities' : filterType;
  const searchPlaceholder = browseAll ? 'Search entities...' : `Search ${filterType?.toLowerCase()}s...`;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/entities"
              className="text-cm-coffee hover:text-cm-charcoal transition-colors"
            >
              Entities
            </Link>
            <span className="text-cm-coffee/50">/</span>
            <span
              className="font-medium"
              style={{ color: browseAll ? TYPE_COLORS.Default : (TYPE_COLORS[filterType!] || TYPE_COLORS.Default) }}
            >
              {displayType}
            </span>
          </div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            {displayType}
          </h1>
          <p className="text-cm-coffee mt-1">
            {filteredEntities.length} {filteredEntities.length === 1 ? 'entity' : 'entities'}
          </p>
        </div>
        {!browseAll && (
          <button className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors">
            + New {filterType}
          </button>
        )}
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder={searchPlaceholder}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-md px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal"
        />
      </div>

      {/* Entity grid */}
      {filteredEntities.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-cm-coffee mb-4">No entities found.</p>
          <p className="text-sm text-cm-coffee/70">
            {browseAll ? 'Create your first entity to get started.' : `Create your first ${filterType?.toLowerCase()} or adjust your search.`}
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
        <p className="text-cm-coffee">Loading...</p>
      </div>
    }>
      <EntitiesContent />
    </Suspense>
  );
}
