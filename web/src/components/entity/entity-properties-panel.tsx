'use client';

import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Entity } from '@/types';

interface EntityPropertiesPanelProps {
  entity: Entity;
  excludeKeys?: string[];
}

export function EntityPropertiesPanel({ entity, excludeKeys = [] }: EntityPropertiesPanelProps) {
  const [copiedKey, setCopiedKey] = useState(false);

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    // Format as YYYY-MM-DD HH:MM:SS UTC
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds} UTC`;
  };

  const renderValue = (value: unknown): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-cm-coffee/50 italic">-</span>;
    }

    if (typeof value === 'boolean') {
      return (
        <span className={value ? 'text-green-600' : 'text-red-600'}>
          {value ? 'Yes' : 'No'}
        </span>
      );
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="text-cm-coffee/50 italic">Empty list</span>;
      }
      const isPrimitiveArray = value.every(
        (item) => typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean'
      );
      if (isPrimitiveArray) {
        return (
          <ul className="space-y-1">
            {value.map((item, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-cm-coffee/50">-</span>
                <span>{String(item)}</span>
              </li>
            ))}
          </ul>
        );
      }
      return (
        <pre className="text-xs bg-cm-sand/30 rounded p-2 overflow-x-auto max-h-48">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }

    if (typeof value === 'object' && value !== null) {
      return (
        <pre className="text-xs bg-cm-sand/30 rounded p-2 overflow-x-auto max-h-48">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }

    // Check if it's a URL
    if (typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))) {
      return (
        <a
          href={value}
          target="_blank"
          rel="noopener noreferrer"
          className="text-cm-terracotta hover:underline break-all"
        >
          {value}
        </a>
      );
    }

    // Check if it looks like a date
    if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
      return formatDateTime(value);
    }

    return String(value);
  };

  const filteredProperties = entity.properties
    ? Object.entries(entity.properties).filter(([key]) => !excludeKeys.includes(key))
    : [];

  return (
    <div className="space-y-6">
      {/* Properties */}
      {filteredProperties.length > 0 ? (
        <div>
          <h3 className="text-sm font-medium text-cm-coffee mb-3">Properties</h3>
          <div className="bg-cm-cream border border-cm-sand rounded-lg divide-y divide-cm-sand">
            {filteredProperties.map(([key, value]) => (
              <div key={key} className="flex px-4 py-3">
                <span className="text-cm-coffee min-w-[150px] font-medium capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <div className="text-cm-charcoal flex-1">
                  {renderValue(value)}
                </div>
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
            <span className="text-cm-charcoal font-mono text-sm flex items-center gap-2">
              {entity.entity_key}
              <button
                onClick={() => copyToClipboard(entity.entity_key)}
                className="p-1 text-cm-coffee/50 hover:text-cm-coffee transition-colors"
                title="Copy entity key"
              >
                {copiedKey ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
              </button>
            </span>
          </div>
          <div className="flex px-4 py-3">
            <span className="text-cm-coffee min-w-[150px] font-medium">Type</span>
            <span className="text-cm-charcoal">{entity.entity_type}</span>
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
            <span className="text-cm-coffee min-w-[150px] font-medium">Scope</span>
            <span className="text-cm-charcoal">
              {entity.scope_type ? (
                <span className="inline-flex items-center gap-2">
                  <span className={`px-2 py-0.5 text-xs rounded-full ${
                    entity.scope_type === 'domain' ? 'bg-blue-100 text-blue-700' :
                    entity.scope_type === 'team' ? 'bg-green-100 text-green-700' :
                    'bg-purple-100 text-purple-700'
                  }`}>
                    {entity.scope_type}
                  </span>
                  {entity.scope_name && (
                    <span className="text-cm-coffee">{entity.scope_name}</span>
                  )}
                  {!entity.scope_name && entity.scope_key && (
                    <span className="text-cm-coffee/50 text-xs font-mono">{entity.scope_key}</span>
                  )}
                </span>
              ) : (
                <span className="text-cm-coffee/50 italic">Domain (default)</span>
              )}
            </span>
          </div>
          <div className="flex px-4 py-3">
            <span className="text-cm-coffee min-w-[150px] font-medium">Created</span>
            <span className="text-cm-charcoal">{formatDateTime(entity.created_at)}</span>
          </div>
          <div className="flex px-4 py-3">
            <span className="text-cm-coffee min-w-[150px] font-medium">Updated</span>
            <span className="text-cm-charcoal">{formatDateTime(entity.updated_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
