'use client';

import { useEffect, useState, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { X, Search, Focus, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';
import { Entity, Relationship, Scope } from '@/types';
import { KnowledgeGraph } from '@/components/graph';
import { KnowledgeNav } from '@/components/knowledge';
import { cn } from '@/lib/utils';

// Entity types that can be used as project/scope filters
const SCOPE_ENTITY_TYPES = ['Project', 'Repository'];

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

function GraphPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Scope filtering state
  const [availableScopes, setAvailableScopes] = useState<Scope[]>([]);
  const [selectedScope, setSelectedScope] = useState<Scope | null>(null);
  const [scopesLoading, setScopesLoading] = useState(true);

  // Read focus from URL on mount
  const urlFocus = searchParams.get('focus');
  const [focusedEntityKey, setFocusedEntityKey] = useState<string | null>(urlFocus);

  // Get scope entities (Projects, Repositories) for dropdown
  const scopeEntities = entities.filter(e => SCOPE_ENTITY_TYPES.includes(e.entity_type));

  // Load available scopes from /auth/me on mount
  useEffect(() => {
    async function loadScopes() {
      try {
        const res = await api.auth.me();
        if (res.data?.available_scopes) {
          setAvailableScopes(res.data.available_scopes);
        }
      } catch (err) {
        console.error('Failed to load scopes:', err);
      } finally {
        setScopesLoading(false);
      }
    }
    loadScopes();
  }, []);

  // Load graph data when scope changes
  useEffect(() => {
    async function loadGraph() {
      setLoading(true);
      try {
        // Build params with scope filter
        const params: Record<string, string> = { limit: '1000' };
        if (selectedScope) {
          params.scope_type = selectedScope.scope_type;
          params.scope_key = selectedScope.scope_key;
        }

        // Fetch entities and relationships
        const [entRes, relRes] = await Promise.all([
          api.entities.list(params),
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
  }, [selectedScope]);

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
    // Update URL to enable deep-linking
    const params = new URLSearchParams(searchParams.toString());
    if (entityKey) {
      params.set('focus', entityKey);
    } else {
      params.delete('focus');
    }
    router.replace(`/graph?${params.toString()}`, { scroll: false });
  }, [searchParams, router]);

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
      <div className="flex items-center justify-between p-6 pb-4 gap-4">
        <div className="flex-shrink-0">
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Graph
          </h1>
          <p className="text-cm-coffee mt-1">
            Visualize entities and their relationships
          </p>
        </div>

        {/* Controls row */}
        <div className="flex items-center gap-3">
          {/* Scope filter dropdown */}
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
              }}
              className={cn(
                "px-3 py-2 pr-8 rounded-lg border transition-colors text-sm appearance-none cursor-pointer min-w-[140px]",
                "focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta",
                selectedScope
                  ? SCOPE_COLORS[selectedScope.scope_type] || 'border-cm-sand bg-white'
                  : 'border-cm-sand text-cm-coffee bg-white'
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
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-cm-coffee/50 pointer-events-none" />
          </div>

          {/* Project/Repository focus dropdown */}
          {scopeEntities.length > 0 && (
            <div className="relative">
              <select
                value={focusedEntityKey || ''}
                onChange={(e) => handleFocusEntity(e.target.value || null)}
                className="appearance-none pl-3 pr-8 py-2 text-sm border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta bg-white cursor-pointer min-w-[180px]"
              >
                <option value="">All entities</option>
                <optgroup label="Projects">
                  {scopeEntities.filter(e => e.entity_type === 'Project').map(e => (
                    <option key={e.entity_key} value={e.entity_key}>{e.name}</option>
                  ))}
                </optgroup>
                <optgroup label="Repositories">
                  {scopeEntities.filter(e => e.entity_type === 'Repository').map(e => (
                    <option key={e.entity_key} value={e.entity_key}>{e.name}</option>
                  ))}
                </optgroup>
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-cm-coffee/50 pointer-events-none" />
            </div>
          )}

          {/* Focus indicator (for non-scope entities) */}
          {focusedEntity && !SCOPE_ENTITY_TYPES.includes(focusedEntity.entity_type) && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-cm-terracotta/10 border border-cm-terracotta/30 rounded-lg">
              <Focus className="w-4 h-4 text-cm-terracotta" />
              <span className="text-sm text-cm-charcoal">
                Focused: <strong>{focusedEntity.name}</strong>
              </span>
              <button
                onClick={() => handleFocusEntity(null)}
                className="p-0.5 text-cm-terracotta hover:text-cm-sienna transition-colors"
                title="Clear focus"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Search box */}
          <div className="relative">
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

          {/* Navigation toggle */}
          <KnowledgeNav currentPage="graph" />
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

// Wrap in Suspense for useSearchParams
export default function GraphPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading graph...</p>
      </div>
    }>
      <GraphPageContent />
    </Suspense>
  );
}
