'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { TYPE_COLORS } from '@/lib/graph/layout';
import { EntityPropertiesPanel } from '@/components/entity/entity-properties-panel';
import { EntityRelationshipsPanel } from '@/components/entity/entity-relationships-panel';
import { EntityJsonEditor } from '@/components/entity/entity-json-editor';

type TabType = 'properties' | 'relationships' | 'json';

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

  const handleEntityUpdate = (updatedEntity: Entity) => {
    setEntity(updatedEntity);
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
          {(['properties', 'relationships', 'json'] as TabType[]).map((tab) => (
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
          <div className="max-w-4xl">
            <EntityPropertiesPanel entity={entity} />
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            <EntityRelationshipsPanel entity={entity} />
          </div>
        )}

        {activeTab === 'json' && (
          <div className="max-w-4xl">
            <EntityJsonEditor entity={entity} onSave={handleEntityUpdate} />
          </div>
        )}
      </div>
    </div>
  );
}
