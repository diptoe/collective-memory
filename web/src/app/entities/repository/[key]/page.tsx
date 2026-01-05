'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Entity } from '@/types';
import { cn } from '@/lib/utils';

interface RepositoryProperties {
  url?: string;
  owner?: string;
  platform?: string;
  default_branch?: string;
  language?: string;
  size_kb?: number;
  stars?: number;
  forks?: number;
  open_issues?: number;
  visibility?: string;
  is_archived?: boolean;
  is_fork?: boolean;
  topics?: string[];
  description?: string;
  created_at?: string;
  updated_at?: string;
  pushed_at?: string;
  synced_at?: string;
  [key: string]: unknown;
}

interface RepositoryEntity extends Entity {
  properties: RepositoryProperties;
}

export default function RepositoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const repositoryKey = params.key as string;

  const [repository, setRepository] = useState<RepositoryEntity | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'relationships'>('overview');

  const loadRepository = useCallback(async () => {
    try {
      const res = await api.entities.get(repositoryKey, true);
      const repo = res.data?.entity as RepositoryEntity;
      if (repo) {
        setRepository(repo);

        // Auto-sync if data is stale (>24h old)
        if (repo.properties.synced_at) {
          const syncedAt = new Date(repo.properties.synced_at);
          const hoursSinceSync = (Date.now() - syncedAt.getTime()) / (1000 * 60 * 60);
          if (hoursSinceSync > 24) {
            handleSync(repo.properties.url);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load repository:', err);
    } finally {
      setLoading(false);
    }
  }, [repositoryKey]);

  useEffect(() => {
    loadRepository();
  }, [loadRepository]);

  const handleSync = async (repoUrl?: string) => {
    if (!repoUrl || syncing) return;

    setSyncing(true);
    try {
      // Call the sync endpoint - this will update the entity via the API
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api'}/github/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository_url: repoUrl }),
      });

      if (response.ok) {
        // Reload the entity to get fresh data
        await loadRepository();
      }
    } catch (err) {
      console.error('Failed to sync repository:', err);
    } finally {
      setSyncing(false);
    }
  };

  const formatNumber = (num?: number) => {
    if (num === undefined) return '-';
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toString();
  };

  const formatSize = (kb?: number) => {
    if (kb === undefined) return '-';
    if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
    return `${kb} KB`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const isStale = () => {
    if (!repository?.properties.synced_at) return true;
    const syncedAt = new Date(repository.properties.synced_at);
    const hoursSinceSync = (Date.now() - syncedAt.getTime()) / (1000 * 60 * 60);
    return hoursSinceSync > 24;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading repository...</p>
      </div>
    );
  }

  if (!repository) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-cm-coffee mb-4">Repository not found</p>
        <button
          onClick={() => router.push('/entities?type=Repository')}
          className="text-cm-terracotta hover:underline"
        >
          Back to Repositories
        </button>
      </div>
    );
  }

  const props = repository.properties;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-cm-sand bg-cm-ivory p-4">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={() => router.push('/entities?type=Repository')}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Entities
          </button>

          <div className="flex items-center gap-2">
            {props.url && (
              <a
                href={props.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                GitHub
              </a>
            )}
            <button
              onClick={() => handleSync(props.url)}
              disabled={syncing}
              className="px-4 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {syncing ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Syncing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Sync
                </>
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-[#7c5cbf] flex items-center justify-center text-cm-ivory text-lg font-medium">
            R
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">{repository.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              {props.language && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-cm-sand text-cm-coffee">
                  {props.language}
                </span>
              )}
              {props.visibility && (
                <span className={cn(
                  'px-2 py-0.5 text-xs rounded-full',
                  props.visibility === 'public' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                )}>
                  {props.visibility}
                </span>
              )}
              {props.is_archived && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-800">
                  Archived
                </span>
              )}
              {isStale() && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-800">
                  Stale data
                </span>
              )}
            </div>
          </div>
        </div>

        {props.synced_at && (
          <p className="text-xs text-cm-coffee/70 mt-2">
            Last synced: {new Date(props.synced_at).toLocaleString()}
          </p>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-cm-cream border-b border-cm-sand">
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{formatNumber(props.stars)}</div>
          <div className="text-sm text-cm-coffee">Stars</div>
        </div>
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{formatNumber(props.forks)}</div>
          <div className="text-sm text-cm-coffee">Forks</div>
        </div>
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{formatNumber(props.open_issues)}</div>
          <div className="text-sm text-cm-coffee">Open Issues</div>
        </div>
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{formatSize(props.size_kb)}</div>
          <div className="text-sm text-cm-coffee">Size</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-cm-sand bg-cm-cream">
        <div className="flex">
          {(['overview', 'relationships'] as const).map((tab) => (
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
        {activeTab === 'overview' && (
          <div className="max-w-4xl space-y-6">
            {props.description && (
              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Description</h3>
                <p className="text-cm-charcoal">{props.description}</p>
              </div>
            )}

            {props.topics && props.topics.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Topics</h3>
                <div className="flex flex-wrap gap-2">
                  {props.topics.map((topic) => (
                    <span key={topic} className="px-2 py-1 text-xs bg-cm-sand rounded-full text-cm-coffee">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Details</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Owner</dt>
                    <dd className="text-cm-charcoal">{props.owner || '-'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Default Branch</dt>
                    <dd className="text-cm-charcoal font-mono">{props.default_branch || '-'}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Created</dt>
                    <dd className="text-cm-charcoal">{formatDate(props.created_at)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Last Push</dt>
                    <dd className="text-cm-charcoal">{formatDate(props.pushed_at)}</dd>
                  </div>
                </dl>
              </div>

              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Entity Info</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Entity Key</dt>
                    <dd className="text-cm-charcoal font-mono text-xs">{repository.entity_key}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Confidence</dt>
                    <dd className="text-cm-charcoal">{Math.round(repository.confidence * 100)}%</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Source</dt>
                    <dd className="text-cm-charcoal">{repository.source || '-'}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            {repository.relationships && (
              <>
                {repository.relationships.outgoing.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-cm-coffee mb-3">
                      Outgoing Relationships ({repository.relationships.outgoing.length})
                    </h3>
                    <div className="space-y-2">
                      {repository.relationships.outgoing.map((rel) => (
                        <div
                          key={rel.relationship_key}
                          className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg"
                        >
                          <span className="text-cm-charcoal font-medium">{repository.name}</span>
                          <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                            {rel.relationship_type}
                          </span>
                          <span className="text-cm-charcoal">
                            {rel.to_entity?.name || rel.to_entity_key}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {repository.relationships.incoming.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-cm-coffee mb-3">
                      Incoming Relationships ({repository.relationships.incoming.length})
                    </h3>
                    <div className="space-y-2">
                      {repository.relationships.incoming.map((rel) => (
                        <div
                          key={rel.relationship_key}
                          className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg"
                        >
                          <span className="text-cm-charcoal">
                            {rel.from_entity?.name || rel.from_entity_key}
                          </span>
                          <span className="px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                            {rel.relationship_type}
                          </span>
                          <span className="text-cm-charcoal font-medium">{repository.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {repository.relationships.outgoing.length === 0 && repository.relationships.incoming.length === 0 && (
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
