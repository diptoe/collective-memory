'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { KnowledgeStatsData, KnowledgeDomain, CrossScopeRelationship } from '@/types';
import { useAuthStore } from '@/lib/stores/auth-store';
import {
  KnowledgeNav,
  KnowledgeStats,
  ScopeTreemap,
  ScopeCard,
  DomainSwitcher,
} from '@/components/knowledge';

export default function KnowledgePage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<KnowledgeStatsData | null>(null);
  const [domains, setDomains] = useState<KnowledgeDomain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdmin = user?.role === 'admin';

  // Load domains for admin users
  useEffect(() => {
    if (!isAdmin) return;

    async function loadDomains() {
      try {
        const res = await api.knowledge.domains();
        if (res.success && res.data?.domains) {
          setDomains(res.data.domains);
        }
      } catch (err) {
        console.error('Failed to load domains:', err);
      }
    }

    loadDomains();
  }, [isAdmin]);

  // Load knowledge stats
  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      setError(null);

      try {
        const params = selectedDomain ? { domain_key: selectedDomain } : undefined;
        const res = await api.knowledge.stats(params);

        if (res.success && res.data) {
          setStats(res.data);
        } else {
          setError(res.msg || 'Failed to load knowledge stats');
        }
      } catch (err) {
        console.error('Failed to load knowledge stats:', err);
        setError('Failed to load knowledge stats');
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, [selectedDomain]);

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading knowledge overview...</p>
      </div>
    );
  }

  if (error && !stats) {
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
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Knowledge
          </h1>
          <p className="text-cm-coffee mt-1">
            Visual overview of your knowledge graph by scope
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Domain switcher for admins */}
          {isAdmin && (
            <DomainSwitcher
              domains={domains}
              selectedDomain={selectedDomain}
              onDomainChange={setSelectedDomain}
              loading={loading}
            />
          )}
          {/* Navigation toggle */}
          <KnowledgeNav currentPage="overview" />
        </div>
      </div>

      {stats && (
        <>
          {/* Summary stats */}
          <div className="mb-8">
            <KnowledgeStats totals={stats.totals} />
          </div>

          {/* Scope visualization */}
          <div className="mb-8">
            <h2 className="font-medium text-cm-charcoal mb-4">Scope Distribution</h2>
            <ScopeTreemap
              scopes={stats.scopes}
              totalEntities={stats.totals.entities}
            />
          </div>

          {/* Scope cards grid */}
          <div className="mb-8">
            <h2 className="font-medium text-cm-charcoal mb-4">Scopes by Type</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {stats.scopes.map((scope) => (
                <ScopeCard
                  key={`${scope.scope_type}-${scope.scope_key}`}
                  scope={scope}
                  totalEntities={stats.totals.entities}
                />
              ))}
            </div>
          </div>

          {/* Cross-scope relationships */}
          {stats.cross_scope_relationships.length > 0 && (
            <div>
              <h2 className="font-medium text-cm-charcoal mb-4">Cross-Scope Connections</h2>
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-4">
                <div className="flex flex-wrap gap-3">
                  {stats.cross_scope_relationships.map((rel, index) => (
                    <CrossScopeBadge key={index} relationship={rel} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Cross-scope relationship badge component
function CrossScopeBadge({ relationship }: { relationship: CrossScopeRelationship }) {
  const fromName = relationship.from_scope.name || relationship.from_scope.scope_key;
  const toName = relationship.to_scope.name || relationship.to_scope.scope_key;

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-cm-sand text-sm">
      <ScopeIcon type={relationship.from_scope.scope_type} />
      <span className="text-cm-charcoal font-medium truncate max-w-[100px]" title={fromName}>
        {fromName}
      </span>
      <span className="text-cm-coffee">→</span>
      <ScopeIcon type={relationship.to_scope.scope_type} />
      <span className="text-cm-charcoal font-medium truncate max-w-[100px]" title={toName}>
        {toName}
      </span>
      <span className="text-cm-terracotta font-medium">{relationship.count}</span>
    </div>
  );
}

// Scope icon component
function ScopeIcon({ type }: { type: string }) {
  const icons: Record<string, string> = {
    system: '⚙️',
    domain: '🌐',
    team: '👥',
    user: '👤',
  };
  return <span className="text-sm">{icons[type] || '📦'}</span>;
}
