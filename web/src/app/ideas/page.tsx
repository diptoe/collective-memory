'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { cn, formatDateTime } from '@/lib/utils';

// Idea statuses with colors
const STATUSES = {
  proposed: { label: 'Proposed', color: 'bg-blue-100 text-blue-800', icon: '💡' },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-800', icon: '✓' },
  in_progress: { label: 'In Progress', color: 'bg-yellow-100 text-yellow-800', icon: '🔄' },
  implemented: { label: 'Implemented', color: 'bg-purple-100 text-purple-800', icon: '✅' },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-800', icon: '✗' },
  deferred: { label: 'Deferred', color: 'bg-gray-100 text-gray-600', icon: '⏸' },
} as const;

// Priority levels with colors
const PRIORITIES = {
  critical: { label: 'Critical', color: 'bg-red-500 text-white' },
  high: { label: 'High', color: 'bg-orange-500 text-white' },
  medium: { label: 'Medium', color: 'bg-yellow-500 text-white' },
  low: { label: 'Low', color: 'bg-gray-400 text-white' },
} as const;

// Effort levels
const EFFORTS = {
  small: { label: 'Small', color: 'text-green-600' },
  medium: { label: 'Medium', color: 'text-yellow-600' },
  large: { label: 'Large', color: 'text-red-600' },
} as const;

type IdeaStatus = keyof typeof STATUSES;
type IdeaPriority = keyof typeof PRIORITIES;
type IdeaEffort = keyof typeof EFFORTS;

interface IdeaCardProps {
  idea: Entity;
  onClick: () => void;
}

function IdeaCard({ idea, onClick }: IdeaCardProps) {
  const status = (idea.properties.status as IdeaStatus) || 'proposed';
  const priority = (idea.properties.priority as IdeaPriority) || 'medium';
  const effort = (idea.properties.effort as IdeaEffort) || 'medium';
  const tags = (idea.properties.tags as string[]) || [];
  const description = idea.properties.description as string || '';

  const statusInfo = STATUSES[status] || STATUSES.proposed;
  const priorityInfo = PRIORITIES[priority] || PRIORITIES.medium;
  const effortInfo = EFFORTS[effort] || EFFORTS.medium;

  return (
    <div
      onClick={onClick}
      className="bg-cm-ivory rounded-xl border border-cm-sand p-4 hover:shadow-md hover:border-cm-terracotta/50 transition-all cursor-pointer"
    >
      {/* Header with priority badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{statusInfo.icon}</span>
          <span className={cn('px-2 py-0.5 text-xs rounded-full font-medium', statusInfo.color)}>
            {statusInfo.label}
          </span>
        </div>
        <span className={cn('px-2 py-0.5 text-xs rounded-full font-medium', priorityInfo.color)}>
          {priorityInfo.label}
        </span>
      </div>

      {/* Title */}
      <h3 className="font-medium text-cm-charcoal mb-2 line-clamp-2">
        {idea.name}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-sm text-cm-coffee mb-3 line-clamp-2">
          {description}
        </p>
      )}

      {/* Effort and Tags */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className={cn('text-xs font-medium', effortInfo.color)}>
          {effortInfo.label} effort
        </span>
        {tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee"
          >
            {tag}
          </span>
        ))}
        {tags.length > 3 && (
          <span className="text-xs text-cm-coffee/50">+{tags.length - 3}</span>
        )}
      </div>

      {/* Footer */}
      <div className="text-xs text-cm-coffee/50">
        Created {formatDateTime(idea.created_at)}
      </div>
    </div>
  );
}

function IdeasContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [ideas, setIdeas] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Filters from URL
  const statusFilter = searchParams.get('status');
  const priorityFilter = searchParams.get('priority');

  // Update URL with filters
  const setFilter = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`/ideas?${params.toString()}`);
  };

  // Load ideas
  useEffect(() => {
    async function loadIdeas() {
      try {
        const res = await api.entities.list({ type: 'Idea' });
        setIdeas(res.data?.entities || []);
      } catch (err) {
        console.error('Failed to load ideas:', err);
      } finally {
        setLoading(false);
      }
    }
    loadIdeas();
  }, []);

  // Filter ideas
  const filteredIdeas = ideas.filter((idea) => {
    const matchesSearch = idea.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (idea.properties.description as string || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = !statusFilter || idea.properties.status === statusFilter;
    const matchesPriority = !priorityFilter || idea.properties.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Group by status for summary
  const statusCounts = ideas.reduce((acc, idea) => {
    const status = (idea.properties.status as string) || 'proposed';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const handleIdeaClick = (idea: Entity) => {
    router.push(`/entities/idea/${idea.entity_key}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading ideas...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Ideas
          </h1>
          <p className="text-cm-coffee mt-1">
            Track and manage feature ideas and improvements
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
        >
          + New Idea
        </button>
      </div>

      {/* Status summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {Object.entries(STATUSES).map(([key, info]) => {
          const count = statusCounts[key] || 0;
          const isActive = statusFilter === key;
          return (
            <button
              key={key}
              onClick={() => setFilter('status', isActive ? null : key)}
              className={cn(
                'p-3 rounded-lg border transition-all text-left',
                isActive
                  ? 'border-cm-terracotta bg-cm-terracotta/10'
                  : 'border-cm-sand bg-cm-ivory hover:border-cm-terracotta/50'
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <span>{info.icon}</span>
                <span className="text-xs text-cm-coffee">{info.label}</span>
              </div>
              <p className="text-xl font-semibold text-cm-charcoal">{count}</p>
            </button>
          );
        })}
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Search */}
        <input
          type="text"
          placeholder="Search ideas..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 min-w-[200px] max-w-md px-4 py-2 bg-cm-cream border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta text-cm-charcoal"
        />

        {/* Priority filter */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-cm-coffee">Priority:</span>
          <div className="flex gap-1">
            {Object.entries(PRIORITIES).map(([key, info]) => (
              <button
                key={key}
                onClick={() => setFilter('priority', priorityFilter === key ? null : key)}
                className={cn(
                  'px-2 py-1 text-xs rounded-full transition-all',
                  priorityFilter === key
                    ? info.color
                    : 'bg-cm-sand text-cm-coffee hover:bg-cm-terracotta/20'
                )}
              >
                {info.label}
              </button>
            ))}
          </div>
        </div>

        {/* Clear filters */}
        {(statusFilter || priorityFilter) && (
          <button
            onClick={() => router.push('/ideas')}
            className="text-sm text-cm-terracotta hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results count */}
      <p className="text-sm text-cm-coffee mb-4">
        Showing {filteredIdeas.length} of {ideas.length} ideas
      </p>

      {/* Ideas grid */}
      {filteredIdeas.length === 0 ? (
        <div className="text-center py-12 bg-cm-ivory rounded-xl border border-cm-sand">
          <p className="text-cm-coffee mb-2">No ideas found.</p>
          <p className="text-sm text-cm-coffee/70">
            {ideas.length === 0
              ? 'Create your first idea to get started.'
              : 'Try adjusting your search or filters.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredIdeas.map((idea) => (
            <IdeaCard
              key={idea.entity_key}
              idea={idea}
              onClick={() => handleIdeaClick(idea)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateIdeaModal
          onClose={() => setShowCreateModal(false)}
          onCreated={(idea) => {
            setIdeas([idea, ...ideas]);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}

interface CreateIdeaModalProps {
  onClose: () => void;
  onCreated: (idea: Entity) => void;
}

function CreateIdeaModal({ onClose, onCreated }: CreateIdeaModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [rationale, setRationale] = useState('');
  const [status, setStatus] = useState<IdeaStatus>('proposed');
  const [priority, setPriority] = useState<IdeaPriority>('medium');
  const [effort, setEffort] = useState<IdeaEffort>('medium');
  const [tags, setTags] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    try {
      const res = await api.entities.create({
        entity_type: 'Idea',
        name: name.trim(),
        properties: {
          description: description.trim(),
          rationale: rationale.trim(),
          status,
          priority,
          effort,
          tags: tags.split(',').map(t => t.trim()).filter(Boolean),
          success_criteria: [],
        },
      });
      if (res.data?.entity) {
        onCreated(res.data.entity);
      }
    } catch (err) {
      console.error('Failed to create idea:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-cm-cream rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-serif text-xl font-semibold text-cm-charcoal">
              New Idea
            </h2>
            <button
              onClick={onClose}
              className="text-cm-coffee hover:text-cm-charcoal"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Brief title for the idea"
                className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What is this idea about?"
                rows={3}
                className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              />
            </div>

            {/* Rationale */}
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Rationale
              </label>
              <textarea
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder="Why should we implement this?"
                rows={2}
                className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              />
            </div>

            {/* Status, Priority, Effort row */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as IdeaStatus)}
                  className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  {Object.entries(STATUSES).map(([key, info]) => (
                    <option key={key} value={key}>{info.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as IdeaPriority)}
                  className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  {Object.entries(PRIORITIES).map(([key, info]) => (
                    <option key={key} value={key}>{info.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Effort
                </label>
                <select
                  value={effort}
                  onChange={(e) => setEffort(e.target.value as IdeaEffort)}
                  className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
                >
                  {Object.entries(EFFORTS).map(([key, info]) => (
                    <option key={key} value={key}>{info.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Tags
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="Comma-separated tags (e.g., ui, backend, performance)"
                className="w-full px-3 py-2 bg-cm-ivory border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving || !name.trim()}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna disabled:opacity-50 transition-colors"
              >
                {saving ? 'Creating...' : 'Create Idea'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function IdeasPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading...</p>
      </div>
    }>
      <IdeasContent />
    </Suspense>
  );
}
