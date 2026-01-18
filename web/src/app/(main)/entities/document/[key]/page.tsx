'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity, Scope } from '@/types';
import { cn } from '@/lib/utils';

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

  // Move scope modal state
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [availableScopes, setAvailableScopes] = useState<Scope[]>([]);
  const [selectedScope, setSelectedScope] = useState<Scope | null>(null);
  const [includeRelated, setIncludeRelated] = useState(true);
  const [movingScope, setMovingScope] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [moveResult, setMoveResult] = useState<{ total: number } | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);

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

  // Load user role and available scopes for move functionality
  useEffect(() => {
    const loadUserData = async () => {
      try {
        const res = await api.auth.me();
        if (res.data) {
          setUserRole(res.data.user?.role || null);
          setAvailableScopes(res.data.available_scopes || []);
        }
      } catch (err) {
        console.error('Failed to load user data:', err);
      }
    };
    loadUserData();
  }, []);

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

  const handleMoveScope = async () => {
    if (!document || !selectedScope) return;

    setMovingScope(true);
    setMoveError(null);
    setMoveResult(null);

    try {
      const res = await api.entities.moveScope(document.entity_key, {
        scope_type: selectedScope.scope_type,
        scope_key: selectedScope.scope_key,
        include_related: includeRelated,
      });

      if (res.data) {
        setMoveResult({ total: res.data.total_updated });
        // Reload document to get updated scope
        await loadDocument();
      }
    } catch (err: unknown) {
      console.error('Failed to move entity scope:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to move entity scope';
      setMoveError(errorMessage);
    } finally {
      setMovingScope(false);
    }
  };

  const openMoveModal = () => {
    setSelectedScope(null);
    setMoveError(null);
    setMoveResult(null);
    setShowMoveModal(true);
  };

  const closeMoveModal = () => {
    setShowMoveModal(false);
    setSelectedScope(null);
    setMoveError(null);
    setMoveResult(null);
  };

  const canMoveScope = userRole === 'admin' || userRole === 'domain_admin';

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
            {canMoveScope && !editMode && (
              <button
                onClick={openMoveModal}
                className="px-3 py-1.5 text-sm bg-amber-100 text-amber-700 border border-amber-200 rounded-lg hover:bg-amber-200 transition-colors flex items-center gap-1.5"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                Move Scope
              </button>
            )}
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

      {/* Move Scope Modal */}
      {showMoveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-cm-sand bg-cm-ivory">
              <div className="flex items-center justify-between">
                <h2 className="font-serif text-xl font-semibold text-cm-charcoal">Move Entity Scope</h2>
                <button
                  onClick={closeMoveModal}
                  className="text-cm-coffee hover:text-cm-charcoal transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-sm text-cm-coffee mt-1">
                Move &quot;{document.name}&quot; to a different scope
              </p>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-4 space-y-4">
              {/* Current scope display */}
              {document.scope_type && (
                <div className="text-sm">
                  <span className="text-cm-coffee">Current scope: </span>
                  <span className={cn(
                    "inline-flex items-center gap-1 px-2 py-0.5 rounded border",
                    SCOPE_COLORS[document.scope_type] || 'bg-gray-100 text-gray-700 border-gray-200'
                  )}>
                    {SCOPE_ICONS[document.scope_type]} {document.scope_type}
                  </span>
                </div>
              )}

              {/* Scope selection */}
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-2">
                  Target Scope
                </label>
                <div className="space-y-2">
                  {availableScopes.map((scope) => (
                    <label
                      key={`${scope.scope_type}:${scope.scope_key}`}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                        selectedScope?.scope_key === scope.scope_key && selectedScope?.scope_type === scope.scope_type
                          ? SCOPE_COLORS[scope.scope_type] || 'border-cm-terracotta bg-cm-terracotta/10'
                          : "border-cm-sand hover:border-cm-coffee/30"
                      )}
                    >
                      <input
                        type="radio"
                        name="scope"
                        checked={selectedScope?.scope_key === scope.scope_key && selectedScope?.scope_type === scope.scope_type}
                        onChange={() => setSelectedScope(scope)}
                        className="sr-only"
                      />
                      <span className="text-xl">{SCOPE_ICONS[scope.scope_type]}</span>
                      <div className="flex-1">
                        <div className="font-medium text-cm-charcoal">{scope.name}</div>
                        <div className="text-xs text-cm-coffee capitalize">{scope.scope_type}</div>
                      </div>
                      {selectedScope?.scope_key === scope.scope_key && selectedScope?.scope_type === scope.scope_type && (
                        <svg className="w-5 h-5 text-cm-terracotta" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                    </label>
                  ))}
                </div>
              </div>

              {/* Include related checkbox */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeRelated}
                  onChange={(e) => setIncludeRelated(e.target.checked)}
                  className="w-4 h-4 rounded border-cm-sand text-cm-terracotta focus:ring-cm-terracotta"
                />
                <span className="text-sm text-cm-charcoal">Include related entities (recursive)</span>
              </label>

              {/* Error message */}
              {moveError && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                  {moveError}
                </div>
              )}

              {/* Success message */}
              {moveResult && (
                <div className="p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">
                  Successfully moved {moveResult.total} {moveResult.total === 1 ? 'entity' : 'entities'}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-cm-sand bg-cm-cream flex justify-end gap-3">
              <button
                onClick={closeMoveModal}
                className="px-4 py-2 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                {moveResult ? 'Close' : 'Cancel'}
              </button>
              {!moveResult && (
                <button
                  onClick={handleMoveScope}
                  disabled={!selectedScope || movingScope}
                  className="px-4 py-2 text-sm bg-cm-terracotta text-white rounded-lg hover:bg-cm-terracotta/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {movingScope ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Moving...
                    </>
                  ) : (
                    'Move'
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
