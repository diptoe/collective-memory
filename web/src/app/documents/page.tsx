'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { cn } from '@/lib/utils';

interface DocumentEntity extends Entity {
  properties: {
    status?: string;
    content?: string;
    version?: string;
    authors?: string[];
    [key: string]: unknown;
  };
}

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    async function loadDocuments() {
      try {
        const res = await api.entities.list({ type: 'Document' });
        setDocuments((res.data?.entities || []) as DocumentEntity[]);
      } catch (err) {
        console.error('Failed to load documents:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDocuments();
  }, []);

  // Get unique statuses for filter
  const statuses = [...new Set(documents.map(d => d.properties.status || 'Draft'))];

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || (doc.properties.status || 'Draft') === statusFilter;
    return matchesSearch && matchesStatus;
  });

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
        <p className="text-cm-coffee">Loading documents...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Documents
          </h1>
          <p className="text-cm-coffee mt-1">
            View and edit specification documents, design notes, and other structured content
          </p>
        </div>
        <button
          onClick={() => router.push('/documents/new')}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
        >
          + New Document
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <input
          type="text"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 max-w-md px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal"
        />

        <div className="flex items-center gap-1">
          <button
            onClick={() => setStatusFilter('all')}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              statusFilter === 'all'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
            )}
          >
            All
          </button>
          {statuses.map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                statusFilter === status
                  ? 'bg-cm-terracotta text-cm-ivory'
                  : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
              )}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Documents list */}
      {filteredDocuments.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-cm-coffee mb-4">No documents found.</p>
          <p className="text-sm text-cm-coffee/70">
            Create your first document or adjust your filters.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.entity_key}
              onClick={() => router.push(`/documents/${doc.entity_key}`)}
              className="bg-cm-ivory border border-cm-sand rounded-lg p-4 hover:border-cm-terracotta/50 hover:shadow-sm transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-cm-charcoal">{doc.name}</h3>
                    <span className={cn('px-2 py-0.5 text-xs rounded-full', getStatusColor(doc.properties.status || 'Draft'))}>
                      {doc.properties.status || 'Draft'}
                    </span>
                    {doc.properties.version && (
                      <span className="text-xs text-cm-coffee">v{doc.properties.version}</span>
                    )}
                  </div>

                  {/* Preview of content or description */}
                  {doc.properties.content && (
                    <p className="text-sm text-cm-coffee line-clamp-2 mb-2">
                      {typeof doc.properties.content === 'string'
                        ? doc.properties.content.slice(0, 200) + (doc.properties.content.length > 200 ? '...' : '')
                        : 'Structured content'}
                    </p>
                  )}

                  <div className="flex items-center gap-4 text-xs text-cm-coffee/70">
                    {doc.properties.authors && Array.isArray(doc.properties.authors) && (
                      <span>By: {doc.properties.authors.join(', ')}</span>
                    )}
                    <span>Updated: {new Date(doc.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="text-cm-coffee/50">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
