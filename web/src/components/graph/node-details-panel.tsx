'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { X, ArrowRight, Focus, ChevronDown, ChevronUp, Pencil, Copy, Check } from 'lucide-react';
import { Entity, Relationship } from '@/types';
import { TYPE_COLORS } from '@/lib/graph/layout';

interface NodeDetailsPanelProps {
  entity: Entity;
  relationships: Relationship[];
  allEntities: Entity[];
  onClose: () => void;
  onFocus?: () => void;
  isFocused?: boolean;
}

/**
 * Panel showing details of a selected entity.
 */
export function NodeDetailsPanel({
  entity,
  relationships,
  allEntities,
  onClose,
  onFocus,
  isFocused,
}: NodeDetailsPanelProps) {
  const router = useRouter();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const color = TYPE_COLORS[entity.entity_type] || TYPE_COLORS.Default;

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} UTC`;
  };

  // Navigate to entity detail page
  const handleEdit = () => {
    router.push(`/entities/${encodeURIComponent(entity.entity_type)}/${entity.entity_key}`);
  };

  // Get entity by key
  const getEntity = (key: string) => {
    return allEntities.find((ent) => ent.entity_key === key);
  };

  // Get entity name by key
  const getEntityName = (key: string) => {
    const e = getEntity(key);
    return e?.name || key;
  };

  // Get entity type by key
  const getEntityType = (key: string) => {
    const e = getEntity(key);
    return e?.entity_type;
  };

  // Separate incoming and outgoing relationships
  const outgoing = relationships.filter((r) => r.from_entity_key === entity.entity_key);
  const incoming = relationships.filter((r) => r.to_entity_key === entity.entity_key);

  return (
    <div className="absolute top-4 right-4 w-80 bg-cm-ivory border border-cm-sand rounded-lg shadow-lg z-10 overflow-hidden">
      {/* Header */}
      <div
        className="px-4 py-3 border-b border-cm-sand"
        style={{ backgroundColor: `${color}15` }}
      >
        <div className="flex items-start justify-between">
          <div>
            <span
              className="text-[10px] font-medium uppercase tracking-wider"
              style={{ color }}
            >
              {entity.entity_type}
            </span>
            <h3 className="font-medium text-cm-charcoal mt-0.5">{entity.name}</h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleEdit}
              className="p-1.5 rounded text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand/50 transition-colors"
              title="Edit entity"
            >
              <Pencil className="w-4 h-4" />
            </button>
            {onFocus && (
              <button
                onClick={onFocus}
                className={`p-1.5 rounded transition-colors ${
                  isFocused
                    ? 'bg-cm-terracotta text-cm-ivory'
                    : 'text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand/50'
                }`}
                title={isFocused ? 'Currently focused' : 'Focus on this entity'}
              >
                <Focus className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 text-cm-coffee hover:text-cm-charcoal transition-colors"
              title={isCollapsed ? 'Expand panel' : 'Collapse panel'}
            >
              {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-1 text-cm-coffee hover:text-cm-charcoal transition-colors"
              title="Close panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
      <div className="p-4 max-h-[400px] overflow-y-auto">
        {/* Properties */}
        {entity.properties && Object.keys(entity.properties).length > 0 && (
          <div className="mb-4">
            <h4 className="text-xs font-medium text-cm-coffee uppercase tracking-wider mb-2">
              Properties
            </h4>
            <div className="space-y-1">
              {Object.entries(entity.properties).map(([key, value]) => (
                <div key={key} className="flex text-sm">
                  <span className="text-cm-coffee min-w-[80px]">{key}:</span>
                  <span className="text-cm-charcoal">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Outgoing relationships */}
        {outgoing.length > 0 && (
          <div className="mb-4">
            <h4 className="text-xs font-medium text-cm-coffee uppercase tracking-wider mb-2">
              Outgoing ({outgoing.length})
            </h4>
            <div className="space-y-2">
              {outgoing.map((rel) => (
                <div
                  key={rel.relationship_key}
                  className="flex items-center gap-2 text-sm bg-cm-sand/30 rounded px-2 py-1.5 flex-wrap"
                >
                  <span className="text-cm-terracotta font-medium">
                    {rel.relationship_type.replace(/_/g, ' ')}
                  </span>
                  <ArrowRight className="w-3 h-3 text-cm-coffee" />
                  <span className="text-cm-charcoal truncate">
                    {getEntityName(rel.to_entity_key)}
                  </span>
                  {getEntityType(rel.to_entity_key) && (
                    <span className="text-xs text-cm-coffee">
                      ({getEntityType(rel.to_entity_key)})
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Incoming relationships */}
        {incoming.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-cm-coffee uppercase tracking-wider mb-2">
              Incoming ({incoming.length})
            </h4>
            <div className="space-y-2">
              {incoming.map((rel) => (
                <div
                  key={rel.relationship_key}
                  className="flex items-center gap-2 text-sm bg-cm-sand/30 rounded px-2 py-1.5 flex-wrap"
                >
                  <span className="text-cm-charcoal truncate">
                    {getEntityName(rel.from_entity_key)}
                  </span>
                  {getEntityType(rel.from_entity_key) && (
                    <span className="text-xs text-cm-coffee">
                      ({getEntityType(rel.from_entity_key)})
                    </span>
                  )}
                  <ArrowRight className="w-3 h-3 text-cm-coffee" />
                  <span className="text-cm-terracotta font-medium">
                    {rel.relationship_type.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No relationships */}
        {relationships.length === 0 && (
          <p className="text-sm text-cm-coffee/70 text-center py-4">
            No relationships for this entity
          </p>
        )}

        {/* Metadata */}
        <div className="mt-4 pt-4 border-t border-cm-sand">
          <p className="text-[10px] text-cm-coffee/60 uppercase tracking-wider flex items-center gap-1">
            Key: {entity.entity_key}
            <button
              onClick={() => copyToClipboard(entity.entity_key)}
              className="p-0.5 text-cm-coffee/40 hover:text-cm-coffee transition-colors"
              title="Copy entity key"
            >
              {copiedKey ? <Check className="w-3 h-3 text-green-600" /> : <Copy className="w-3 h-3" />}
            </button>
          </p>
          {entity.created_at && (
            <p className="text-[10px] text-cm-coffee/60 mt-1">
              Created: {formatDateTime(entity.created_at)}
            </p>
          )}
        </div>
      </div>
      )}
    </div>
  );
}
