'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function NewDocumentPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [status, setStatus] = useState('Draft');
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Document name is required');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const res = await api.entities.create({
        entity_type: 'Document',
        name: name.trim(),
        properties: {
          status,
          content,
          version: '1.0',
          created_by: 'web-ui',
        },
      });

      if (res.success && res.data?.entity) {
        router.push(`/documents/${res.data.entity.entity_key}`);
      } else {
        setError(res.msg || 'Failed to create document');
      }
    } catch (err) {
      console.error('Failed to create document:', err);
      setError('Failed to create document');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-cm-sand bg-cm-ivory p-4">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={() => router.push('/documents')}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Documents
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/documents')}
              className="px-3 py-1.5 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={saving || !name.trim()}
              className="px-4 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create Document'}
            </button>
          </div>
        </div>

        <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
          New Document
        </h1>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-cm-coffee mb-2">
              Document Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., API Design Specification"
              className="w-full px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-coffee mb-2">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal"
            >
              <option value="Draft">Draft</option>
              <option value="Review">Review</option>
              <option value="Approved">Approved</option>
              <option value="Published">Published</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-cm-coffee mb-2">
              Content
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Document content... (supports Markdown)"
              className="w-full h-[40vh] p-4 font-mono text-sm bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta resize-none"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
