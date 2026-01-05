'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { cn } from '@/lib/utils';

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
  const [activeTab, setActiveTab] = useState<'content' | 'properties' | 'relationships'>('content');

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
          {(['content', 'properties', 'relationships'] as const).map((tab) => (
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
            <h3 className="text-sm font-medium text-cm-coffee mb-2">
              Additional Properties (JSON)
            </h3>
            {editMode ? (
              <>
                <textarea
                  value={propertiesJson}
                  onChange={(e) => {
                    setPropertiesJson(e.target.value);
                    setJsonError(null);
                  }}
                  className={cn(
                    "w-full h-[50vh] p-4 font-mono text-sm bg-cm-cream border rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 resize-none",
                    jsonError ? 'border-red-500' : 'border-cm-sand focus:border-cm-terracotta'
                  )}
                />
                {jsonError && (
                  <p className="text-red-500 text-sm mt-1">{jsonError}</p>
                )}
              </>
            ) : (
              <pre className="bg-cm-sand/30 p-4 rounded-lg overflow-auto font-mono text-sm text-cm-charcoal">
                {propertiesJson || '{}'}
              </pre>
            )}

            <div className="mt-6 pt-6 border-t border-cm-sand">
              <h3 className="text-sm font-medium text-cm-coffee mb-2">Metadata</h3>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-cm-coffee/70">Entity Key</dt>
                  <dd className="font-mono text-cm-charcoal">{document.entity_key}</dd>
                </div>
                <div>
                  <dt className="text-cm-coffee/70">Created</dt>
                  <dd className="text-cm-charcoal">{new Date(document.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="text-cm-coffee/70">Confidence</dt>
                  <dd className="text-cm-charcoal">{Math.round(document.confidence * 100)}%</dd>
                </div>
                {document.source && (
                  <div>
                    <dt className="text-cm-coffee/70">Source</dt>
                    <dd className="text-cm-charcoal">{document.source}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            {document.relationships && (
              <>
                {document.relationships.outgoing.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-cm-coffee mb-3">
                      Outgoing Relationships ({document.relationships.outgoing.length})
                    </h3>
                    <div className="space-y-2">
                      {document.relationships.outgoing.map((rel) => (
                        <div
                          key={rel.relationship_key}
                          className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap"
                        >
                          <span className="text-cm-charcoal font-medium">{document.name}</span>
                          <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                            {rel.relationship_type}
                          </span>
                          <span className="text-cm-charcoal font-medium">
                            {rel.to_entity?.name || rel.to_entity_key}
                          </span>
                          {rel.to_entity?.entity_type && (
                            <span className="text-xs text-cm-coffee">
                              ({rel.to_entity.entity_type})
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {document.relationships.incoming.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-cm-coffee mb-3">
                      Incoming Relationships ({document.relationships.incoming.length})
                    </h3>
                    <div className="space-y-2">
                      {document.relationships.incoming.map((rel) => (
                        <div
                          key={rel.relationship_key}
                          className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap"
                        >
                          <span className="text-cm-charcoal font-medium">
                            {rel.from_entity?.name || rel.from_entity_key}
                          </span>
                          {rel.from_entity?.entity_type && (
                            <span className="text-xs text-cm-coffee">
                              ({rel.from_entity.entity_type})
                            </span>
                          )}
                          <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                            {rel.relationship_type}
                          </span>
                          <span className="text-cm-charcoal font-medium">{document.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {document.relationships.outgoing.length === 0 && document.relationships.incoming.length === 0 && (
                  <p className="text-cm-coffee/70 italic">No relationships yet.</p>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
