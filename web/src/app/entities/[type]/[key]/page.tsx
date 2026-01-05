'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity, Relationship } from '@/types';
import { TYPE_COLORS } from '@/lib/graph/layout';

type TabType = 'properties' | 'relationships';

export default function EntityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const entityType = decodeURIComponent(params.type as string);
  const entityKey = params.key as string;

  const [entity, setEntity] = useState<Entity | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('properties');

  const loadEntity = useCallback(async () => {
    try {
      const res = await api.entities.get(entityKey, true);
      const ent = res.data?.entity;
      if (ent) {
        setEntity(ent);
      }
    } catch (err) {
      console.error('Failed to load entity:', err);
    } finally {
      setLoading(false);
    }
  }, [entityKey]);

  useEffect(() => {
    loadEntity();
  }, [loadEntity]);

  const handleDelete = async () => {
    if (!entity) return;
    if (!confirm(`Delete "${entity.name}"? This will also delete all relationships. This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    try {
      await api.entities.delete(entity.entity_key);
      router.push(`/entities?type=${encodeURIComponent(entity.entity_type)}`);
    } catch (err) {
      console.error('Failed to delete entity:', err);
      alert('Failed to delete entity');
      setDeleting(false);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const color = entity ? (TYPE_COLORS[entity.entity_type] || TYPE_COLORS.Default) : TYPE_COLORS.Default;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading entity...</p>
      </div>
    );
  }

  if (!entity) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-cm-coffee mb-4">Entity not found</p>
        <button
          onClick={() => router.push('/entities')}
          className="text-cm-terracotta hover:underline"
        >
          Back to Entities
        </button>
      </div>
    );
  }

  const outgoing = entity.relationships?.outgoing || [];
  const incoming = entity.relationships?.incoming || [];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-cm-sand bg-cm-ivory p-4">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={() => router.push(`/entities?type=${encodeURIComponent(entity.entity_type)}`)}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Entities
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-lg flex items-center justify-center text-cm-ivory text-lg font-medium"
            style={{ backgroundColor: color }}
          >
            {entity.entity_type[0]}
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">{entity.name}</h1>
            <Link
              href={`/entities?type=${encodeURIComponent(entity.entity_type)}`}
              className="text-sm hover:underline"
              style={{ color }}
            >
              {entity.entity_type}
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-cm-sand bg-cm-cream">
        <div className="flex overflow-x-auto">
          {(['properties', 'relationships'] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors capitalize whitespace-nowrap ${
                activeTab === tab
                  ? 'text-cm-terracotta border-b-2 border-cm-terracotta'
                  : 'text-cm-coffee hover:text-cm-charcoal'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'properties' && (
          <div className="max-w-4xl space-y-6">
            {/* Properties */}
            {entity.properties && Object.keys(entity.properties).length > 0 ? (
              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Properties</h3>
                <div className="bg-cm-cream border border-cm-sand rounded-lg divide-y divide-cm-sand">
                  {Object.entries(entity.properties).map(([key, value]) => (
                    <div key={key} className="flex px-4 py-3">
                      <span className="text-cm-coffee min-w-[150px] font-medium">{key}</span>
                      <span className="text-cm-charcoal">
                        {typeof value === 'object' ? (
                          <pre className="text-xs bg-cm-sand/30 rounded p-2 overflow-x-auto">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        ) : (
                          String(value)
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No properties defined.</p>
            )}

            {/* Metadata */}
            <div>
              <h3 className="text-sm font-medium text-cm-coffee mb-3">Entity Metadata</h3>
              <div className="bg-cm-cream border border-cm-sand rounded-lg divide-y divide-cm-sand">
                <div className="flex px-4 py-3">
                  <span className="text-cm-coffee min-w-[150px] font-medium">Entity Key</span>
                  <span className="text-cm-charcoal font-mono text-sm">{entity.entity_key}</span>
                </div>
                <div className="flex px-4 py-3">
                  <span className="text-cm-coffee min-w-[150px] font-medium">Confidence</span>
                  <span className="text-cm-charcoal">{Math.round(entity.confidence * 100)}%</span>
                </div>
                <div className="flex px-4 py-3">
                  <span className="text-cm-coffee min-w-[150px] font-medium">Source</span>
                  <span className="text-cm-charcoal">{entity.source || '-'}</span>
                </div>
                <div className="flex px-4 py-3">
                  <span className="text-cm-coffee min-w-[150px] font-medium">Created</span>
                  <span className="text-cm-charcoal">{formatDate(entity.created_at)}</span>
                </div>
                <div className="flex px-4 py-3">
                  <span className="text-cm-coffee min-w-[150px] font-medium">Updated</span>
                  <span className="text-cm-charcoal">{formatDate(entity.updated_at)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            {outgoing.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">
                  Outgoing Relationships ({outgoing.length})
                </h3>
                <div className="space-y-2">
                  {outgoing.map((rel: Relationship) => (
                    <Link
                      key={rel.relationship_key}
                      href={`/entities/${encodeURIComponent(rel.to_entity?.entity_type || 'unknown')}/${rel.to_entity_key}`}
                      className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap hover:border-cm-terracotta/50 transition-colors"
                    >
                      <span className="text-cm-charcoal font-medium">{entity.name}</span>
                      <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                        {rel.relationship_type}
                      </span>
                      <span className="text-cm-coffee">→</span>
                      <span className="text-cm-charcoal font-medium">
                        {rel.to_entity?.name || rel.to_entity_key}
                      </span>
                      {rel.to_entity?.entity_type && (
                        <span className="text-xs text-cm-coffee">
                          ({rel.to_entity.entity_type})
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {incoming.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">
                  Incoming Relationships ({incoming.length})
                </h3>
                <div className="space-y-2">
                  {incoming.map((rel: Relationship) => (
                    <Link
                      key={rel.relationship_key}
                      href={`/entities/${encodeURIComponent(rel.from_entity?.entity_type || 'unknown')}/${rel.from_entity_key}`}
                      className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap hover:border-cm-terracotta/50 transition-colors"
                    >
                      <span className="text-cm-charcoal font-medium">
                        {rel.from_entity?.name || rel.from_entity_key}
                      </span>
                      {rel.from_entity?.entity_type && (
                        <span className="text-xs text-cm-coffee">
                          ({rel.from_entity.entity_type})
                        </span>
                      )}
                      <span className="text-cm-coffee">→</span>
                      <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                        {rel.relationship_type}
                      </span>
                      <span className="text-cm-charcoal font-medium">{entity.name}</span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {outgoing.length === 0 && incoming.length === 0 && (
              <p className="text-cm-coffee/70 italic">No relationships yet.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
