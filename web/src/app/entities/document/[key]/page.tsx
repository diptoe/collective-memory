'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { cn } from '@/lib/utils';
import { EntityPropertiesPanel } from '@/components/entity/entity-properties-panel';
import { EntityRelationshipsPanel } from '@/components/entity/entity-relationships-panel';
import { EntityJsonEditor } from '@/components/entity/entity-json-editor';

interface DocumentProperties {
  status?: string;
  content?: string;
  version?: string;
  authors?: string[];
  [key: string]: unknown;
}

interface DocumentEntity extends Entity {
  properties: DocumentProperties;
}

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentKey = params.key as string;

  const [document, setDocument] = useState<DocumentEntity | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'content' | 'properties' | 'relationships' | 'json'>('content');

  // Editable fields
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('Draft');
  const [propertiesJson, setPropertiesJson] = useState('');
  const [jsonError, setJsonError] = useState<string | null>(null);

  const loadDocument = useCallback(async () => {
    try {
      const res = await api.entities.get(documentKey, true);
      const doc = res.data?.entity as DocumentEntity;
      if (doc) {
        setDocument(doc);
        setName(doc.name);
        setContent(doc.properties.content || '');
        setStatus(doc.properties.status || 'Draft');
        // Remove content and status from properties for the JSON editor
        const { content: _, status: __, ...otherProps } = doc.properties;
        setPropertiesJson(JSON.stringify(otherProps, null, 2));
      }
    } catch (err) {
      console.error('Failed to load document:', err);
    } finally {
      setLoading(false);
    }
  }, [documentKey]);

  useEffect(() => {
    loadDocument();
  }, [loadDocument]);

  const handleSave = async () => {
    if (!document) return;

    // Validate JSON
    let additionalProps: Record<string, unknown> = {};
    try {
      additionalProps = JSON.parse(propertiesJson);
      setJsonError(null);
    } catch {
      setJsonError('Invalid JSON in properties');
      return;
    }

    setSaving(true);
    try {
      const updatedProperties = {
        ...additionalProps,
        content,
        status,
      };

      await api.entities.update(documentKey, {
        name,
        properties: updatedProperties,
      });

      await loadDocument();
      setEditMode(false);
    } catch (err) {
      console.error('Failed to save document:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (document) {
      setName(document.name);
      setContent(document.properties.content || '');
      setStatus(document.properties.status || 'Draft');
      const { content: _, status: __, ...otherProps } = document.properties;
      setPropertiesJson(JSON.stringify(otherProps, null, 2));
    }
    setEditMode(false);
    setJsonError(null);
  };

  const handleDelete = async () => {
    if (!document) return;
    if (!confirm(`Delete "${document.name}"? This will also delete all relationships. This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    try {
      await api.entities.delete(document.entity_key);
      router.push('/entities?type=Document');
    } catch (err) {
      console.error('Failed to delete document:', err);
      alert('Failed to delete document');
      setDeleting(false);
    }
  };

  const handleEntityUpdate = (updatedEntity: Entity) => {
    const doc = updatedEntity as DocumentEntity;
    setDocument(doc);
    setName(doc.name);
    setContent(doc.properties.content || '');
    setStatus(doc.properties.status || 'Draft');
    const { content: _, status: __, ...otherProps } = doc.properties;
    setPropertiesJson(JSON.stringify(otherProps, null, 2));
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'published':
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'review':
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      case 'archived':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-cm-sand text-cm-coffee';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading document...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-cm-coffee mb-4">Document not found</p>
        <button
          onClick={() => router.push('/entities?type=Document')}
          className="text-cm-terracotta hover:underline"
        >
          Back to Documents
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
            onClick={() => router.push('/entities?type=Document')}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Entities
          </button>

          <div className="flex items-center gap-2">
            {editMode ? (
              <>
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
              <>
                <button
                  onClick={() => setEditMode(true)}
                  className="px-4 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
                >
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-[#6b8fa8] flex items-center justify-center text-cm-ivory text-lg font-medium">
            D
          </div>
          <div>
            {editMode ? (
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="font-serif text-2xl font-semibold text-cm-charcoal bg-transparent border-b-2 border-cm-terracotta focus:outline-none"
              />
            ) : (
              <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">{document.name}</h1>
            )}
            <Link
              href="/entities?type=Document"
              className="text-sm text-[#6b8fa8] hover:underline"
            >
              Document
            </Link>
            <div className="flex items-center gap-2 mt-1">
              {editMode ? (
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="px-2 py-0.5 text-xs rounded-full border border-cm-sand bg-cm-cream focus:outline-none focus:ring-1 focus:ring-cm-terracotta"
                >
                  <option value="Draft">Draft</option>
                  <option value="Review">Review</option>
                  <option value="Approved">Approved</option>
                  <option value="Published">Published</option>
                  <option value="Archived">Archived</option>
                </select>
              ) : (
                <span className={cn('px-2 py-0.5 text-xs rounded-full', getStatusColor(document.properties.status || 'Draft'))}>
                  {document.properties.status || 'Draft'}
                </span>
              )}
            </div>
          </div>
        </div>

        <p className="text-sm text-cm-coffee mt-2">
          Last updated: {new Date(document.updated_at).toLocaleString()}
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-cm-sand bg-cm-cream">
        <div className="flex">
          {(['content', 'properties', 'relationships', 'json'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-4 py-2 text-sm font-medium transition-colors capitalize',
                activeTab === tab
                  ? 'text-cm-terracotta border-b-2 border-cm-terracotta'
                  : 'text-cm-coffee hover:text-cm-charcoal'
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'content' && (
          <div className="max-w-4xl">
            {editMode ? (
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Document content... (supports Markdown)"
                className="w-full h-[60vh] p-4 font-mono text-sm bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta resize-none"
              />
            ) : content ? (
              <div className="prose prose-cm max-w-none">
                <pre className="whitespace-pre-wrap font-sans text-cm-charcoal bg-cm-cream p-4 rounded-lg">
                  {content}
                </pre>
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No content yet. Click Edit to add content.</p>
            )}
          </div>
        )}

        {activeTab === 'properties' && (
          <div className="max-w-4xl">
            <EntityPropertiesPanel entity={document} excludeKeys={['content', 'status']} />
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            <EntityRelationshipsPanel entity={document} />
          </div>
        )}

        {activeTab === 'json' && (
          <div className="max-w-4xl">
            <EntityJsonEditor entity={document} onSave={handleEntityUpdate} />
          </div>
        )}
      </div>
    </div>
  );
}
