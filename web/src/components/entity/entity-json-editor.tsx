'use client';

import { useState, useEffect } from 'react';
import { Entity } from '@/types';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface EntityJsonEditorProps {
  entity: Entity;
  onSave?: (updatedEntity: Entity) => void;
}

export function EntityJsonEditor({ entity, onSave }: EntityJsonEditorProps) {
  const [jsonValue, setJsonValue] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Build the editable entity object (excluding read-only fields)
  const buildEditableEntity = (ent: Entity) => {
    return {
      name: ent.name,
      entity_type: ent.entity_type,
      properties: ent.properties || {},
      confidence: ent.confidence,
      source: ent.source,
      context_domain: ent.context_domain,
    };
  };

  useEffect(() => {
    setJsonValue(JSON.stringify(buildEditableEntity(entity), null, 2));
  }, [entity]);

  const handleSave = async () => {
    setError(null);
    setSuccess(false);

    // Validate JSON
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(jsonValue);
    } catch {
      setError('Invalid JSON syntax');
      return;
    }

    // Validate required fields
    if (!parsed.name || typeof parsed.name !== 'string') {
      setError('Name is required and must be a string');
      return;
    }

    setSaving(true);
    try {
      const response = await api.entities.update(entity.entity_key, {
        name: parsed.name,
        properties: parsed.properties || {},
        confidence: parsed.confidence,
        source: parsed.source,
        context_domain: parsed.context_domain,
      });

      if (response.success && response.data?.entity) {
        setSuccess(true);
        setEditMode(false);
        onSave?.(response.data.entity);
        setTimeout(() => setSuccess(false), 3000);
      } else {
        setError(response.msg || 'Failed to save entity');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save entity');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setJsonValue(JSON.stringify(buildEditableEntity(entity), null, 2));
    setEditMode(false);
    setError(null);
  };

  const handleFormat = () => {
    try {
      const parsed = JSON.parse(jsonValue);
      setJsonValue(JSON.stringify(parsed, null, 2));
      setError(null);
    } catch {
      setError('Cannot format: Invalid JSON');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-cm-coffee">Entity JSON</h3>
          <p className="text-xs text-cm-coffee/70 mt-1">
            Edit the entity&apos;s name, properties, confidence, and source directly as JSON
          </p>
        </div>
        <div className="flex items-center gap-2">
          {editMode ? (
            <>
              <button
                onClick={handleFormat}
                className="px-3 py-1.5 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                Format
              </button>
              <button
                onClick={handleCancel}
                className="px-3 py-1.5 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </>
          ) : (
            <button
              onClick={() => setEditMode(true)}
              className="px-4 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
            >
              Edit JSON
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          Entity saved successfully!
        </div>
      )}

      <div className="relative">
        <textarea
          value={jsonValue}
          onChange={(e) => {
            setJsonValue(e.target.value);
            setError(null);
          }}
          readOnly={!editMode}
          className={cn(
            'w-full h-[60vh] p-4 font-mono text-sm rounded-lg border focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 resize-none',
            editMode
              ? 'bg-cm-cream border-cm-sand focus:border-cm-terracotta'
              : 'bg-cm-sand/30 border-cm-sand cursor-default',
            error && editMode && 'border-red-500'
          )}
          spellCheck={false}
        />
        {!editMode && (
          <div className="absolute top-2 right-2 px-2 py-1 bg-cm-sand text-cm-coffee text-xs rounded">
            Read-only
          </div>
        )}
      </div>

      <div className="text-xs text-cm-coffee/70">
        <p className="font-medium mb-1">Editable fields:</p>
        <ul className="list-disc list-inside space-y-0.5">
          <li><code className="bg-cm-sand/50 px-1 rounded">name</code> - Entity display name</li>
          <li><code className="bg-cm-sand/50 px-1 rounded">properties</code> - Custom properties object</li>
          <li><code className="bg-cm-sand/50 px-1 rounded">confidence</code> - Confidence score (0-1)</li>
          <li><code className="bg-cm-sand/50 px-1 rounded">source</code> - Data source</li>
          <li><code className="bg-cm-sand/50 px-1 rounded">context_domain</code> - Context domain</li>
        </ul>
        <p className="mt-2 text-cm-coffee/50">
          Note: entity_key and entity_type cannot be changed after creation.
        </p>
      </div>
    </div>
  );
}
