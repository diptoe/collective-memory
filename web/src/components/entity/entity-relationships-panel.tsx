'use client';

import Link from 'next/link';
import { Entity, Relationship } from '@/types';
import { TYPE_COLORS } from '@/lib/graph/layout';

interface EntityRelationshipsPanelProps {
  entity: Entity;
}

export function EntityRelationshipsPanel({ entity }: EntityRelationshipsPanelProps) {
  const outgoing = entity.relationships?.outgoing || [];
  const incoming = entity.relationships?.incoming || [];

  const getEntityLink = (entityType: string, entityKey: string) => {
    const typeLower = entityType.toLowerCase();
    return `/entities/${encodeURIComponent(typeLower)}/${entityKey}`;
  };

  const getTypeColor = (entityType?: string) => {
    return TYPE_COLORS[entityType || ''] || TYPE_COLORS.Default;
  };

  return (
    <div className="space-y-6">
      {outgoing.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-cm-coffee mb-3">
            Outgoing Relationships ({outgoing.length})
          </h3>
          <div className="space-y-2">
            {outgoing.map((rel: Relationship) => (
              <Link
                key={rel.relationship_key}
                href={getEntityLink(rel.to_entity?.entity_type || 'unknown', rel.to_entity_key)}
                className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap hover:border-cm-terracotta/50 hover:shadow-sm transition-all group"
              >
                <span className="text-cm-charcoal font-medium">{entity.name}</span>
                <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                  {rel.relationship_type}
                </span>
                <span className="text-cm-coffee">→</span>
                <div
                  className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-medium"
                  style={{ backgroundColor: getTypeColor(rel.to_entity?.entity_type) }}
                >
                  {rel.to_entity?.entity_type?.[0] || '?'}
                </div>
                <span className="text-cm-charcoal font-medium group-hover:text-cm-terracotta transition-colors">
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
        <div>
          <h3 className="text-sm font-medium text-cm-coffee mb-3">
            Incoming Relationships ({incoming.length})
          </h3>
          <div className="space-y-2">
            {incoming.map((rel: Relationship) => (
              <Link
                key={rel.relationship_key}
                href={getEntityLink(rel.from_entity?.entity_type || 'unknown', rel.from_entity_key)}
                className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap hover:border-cm-terracotta/50 hover:shadow-sm transition-all group"
              >
                <div
                  className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-medium"
                  style={{ backgroundColor: getTypeColor(rel.from_entity?.entity_type) }}
                >
                  {rel.from_entity?.entity_type?.[0] || '?'}
                </div>
                <span className="text-cm-charcoal font-medium group-hover:text-cm-terracotta transition-colors">
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
  );
}
