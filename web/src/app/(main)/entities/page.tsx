'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity, Scope } from '@/types';
import { EntityCard } from '@/components/entity-card';
import { KnowledgeNav } from '@/components/knowledge';
import { cn } from '@/lib/utils';
import { TYPE_COLORS } from '@/lib/graph/layout';
import { useCanWrite } from '@/hooks/use-can-write';

interface EntityTypeInfo {
  type: string;
  count: number;
}

// Scope display helpers
const SCOPE_ICONS: Record<string, string> = {
  domain: '🌐',
  team: '👥',
  user: '👤',
};

const SCOPE_COLORS: Record<string, string> = {
  domain: 'bg-blue-100 text-blue-700 border-blue-200',
  team: 'bg-green-100 text-green-700 border-green-200',
  user: 'bg-purple-100 text-purple-700 border-purple-200',
};

function EntitiesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const canWrite = useCanWrite();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityTypes, setEntityTypes] = useState<EntityTypeInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Scope filtering state
  const [availableScopes, setAvailableScopes] = useState<Scope[]>([]);
  const [selectedScope, setSelectedScope] = useState<Scope | null>(null);
  const [scopesLoading, setScopesLoading] = useState(true);

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

  // Load available scopes from /auth/me on mount
  useEffect(() => {
    async function loadScopes() {
      try {
        const res = await api.auth.me();
        if (res.data?.available_scopes) {
          setAvailableScopes(res.data.available_scopes);
          // Don't auto-select a scope - show all accessible entities by default
        }
      } catch (err) {
        console.error('Failed to load scopes:', err);
      } finally {
        setScopesLoading(false);
      }
    }
    loadScopes();
  }, []);

  // Load entity types when scope changes
  useEffect(() => {
    async function loadTypes() {
      try {
        const params: { scope_type?: string; scope_key?: string } = {};
        if (selectedScope) {
          params.scope_type = selectedScope.scope_type;
          params.scope_key = selectedScope.scope_key;
        }
        const res = await api.entities.types(params);
        setEntityTypes(res.data?.types || []);
      } catch (err) {
        console.error('Failed to load entity types:', err);
      }
    }
    loadTypes();
  }, [selectedScope]);

  // Load entities when filter or scope changes (only if a type is selected or browse all)
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
        // Add scope filter if selected
        if (selectedScope) {
          params.scope_type = selectedScope.scope_type;
          params.scope_key = selectedScope.scope_key;
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
  }, [filterType, showTypesSummary, browseAll, selectedScope]);

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

  // Scope filter dropdown component
  const ScopeFilter = () => (
    <div className="relative">
      <select
        value={selectedScope ? `${selectedScope.scope_type}:${selectedScope.scope_key}` : ''}
        onChange={(e) => {
          if (e.target.value === '') {
            setSelectedScope(null);
          } else {
            const [scopeType, scopeKey] = e.target.value.split(':');
            const scope = availableScopes.find(
              s => s.scope_type === scopeType && s.scope_key === scopeKey
            );
            setSelectedScope(scope || null);
          }
          setLoading(true);
        }}
        className={cn(
          "px-3 py-2 pr-8 rounded-lg border transition-colors text-sm appearance-none bg-cm-cream cursor-pointer",
          "focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta",
          selectedScope
            ? SCOPE_COLORS[selectedScope.scope_type] || 'border-cm-sand'
            : 'border-cm-sand text-cm-coffee'
        )}
        disabled={scopesLoading}
      >
        <option value="">All Scopes</option>
        {availableScopes.map((scope) => (
          <option key={`${scope.scope_type}:${scope.scope_key}`} value={`${scope.scope_type}:${scope.scope_key}`}>
            {SCOPE_ICONS[scope.scope_type]} {scope.name}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-cm-coffee">
        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
          <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
        </svg>
      </div>
    </div>
  );

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
          <div className="flex items-center gap-3">
            <ScopeFilter />
            <Link
              href="/entities?type=all"
              className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
            >
              Browse All
            </Link>
            <KnowledgeNav currentPage="entities" />
          </div>
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
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            {displayType}
          </h1>
          <p className="text-cm-coffee mt-1">
            {filteredEntities.length} {filteredEntities.length === 1 ? 'entity' : 'entities'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Search box */}
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-64 px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal text-sm"
          />
          <ScopeFilter />
          {!browseAll && (
            <button
              disabled={!canWrite}
              title={!canWrite ? 'Guest users cannot create entities' : undefined}
              className={cn(
                "px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg transition-colors text-sm",
                canWrite ? "hover:bg-cm-sienna" : "opacity-50 cursor-not-allowed"
              )}
            >
              + New {filterType}
            </button>
          )}
          <KnowledgeNav currentPage="entities" />
        </div>
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
