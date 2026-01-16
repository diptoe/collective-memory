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

interface RepositoryProperties {
  url?: string;
  owner?: string;
  platform?: string;
  default_branch?: string;
  language?: string;
  size_kb?: number;
  open_issues?: number;
  visibility?: string;
  is_archived?: boolean;
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

interface Commit {
  sha: string;
  message: string;
  author: string;
  date: string;
  additions: number;
  deletions: number;
  co_authors: string[];
}

interface DailyStat {
  date: string;
  commits_count: number;
  additions: number;
  deletions: number;
  files_changed: number;
  unique_authors: number;
  ai_assisted_commits: number;
}

type TabType = 'overview' | 'commits' | 'stats' | 'properties' | 'relationships' | 'json';

export default function RepositoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const repositoryKey = params.key as string;

  const [repository, setRepository] = useState<RepositoryEntity | null>(null);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [stats, setStats] = useState<DailyStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingCommits, setLoadingCommits] = useState(false);
  const [loadingStats, setLoadingStats] = useState(false);
  const [syncingStats, setSyncingStats] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

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

  const loadCommits = useCallback(async (ownerRepo: string) => {
    setLoadingCommits(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api'}/github/repo/${ownerRepo}/commits?limit=30`
      );
      if (response.ok) {
        const data = await response.json();
        setCommits(data.data?.commits || []);
      }
    } catch (err) {
      console.error('Failed to load commits:', err);
    } finally {
      setLoadingCommits(false);
    }
  }, []);

  const loadStats = useCallback(async (entityKey: string) => {
    setLoadingStats(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api'}/github/stats/${encodeURIComponent(entityKey)}?days=90`
      );
      if (response.ok) {
        const data = await response.json();
        setStats(data.data?.stats || []);
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const handleSyncStats = async () => {
    if (!repository?.properties.url || syncingStats) return;

    setSyncingStats(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api'}/github/stats/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository_url: repository.properties.url, days: 90 }),
      });

      if (response.ok) {
        // Reload stats after sync
        loadStats(repository.entity_key);
      }
    } catch (err) {
      console.error('Failed to sync stats:', err);
    } finally {
      setSyncingStats(false);
    }
  };

  useEffect(() => {
    loadRepository();
  }, [loadRepository]);

  // Load commits when switching to commits tab
  useEffect(() => {
    if (activeTab === 'commits' && repository?.properties.owner && commits.length === 0) {
      const ownerRepo = `${repository.properties.owner}/${repository.name}`;
      loadCommits(ownerRepo);
    }
  }, [activeTab, repository, commits.length, loadCommits]);

  // Load stats when switching to stats tab
  useEffect(() => {
    if (activeTab === 'stats' && repository && stats.length === 0) {
      loadStats(repository.entity_key);
    }
  }, [activeTab, repository, stats.length, loadStats]);

  const handleSync = async (repoUrl?: string) => {
    if (!repoUrl || syncing) return;

    setSyncing(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api'}/github/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository_url: repoUrl }),
      });

      if (response.ok) {
        await loadRepository();
        // Refresh commits too
        if (repository?.properties.owner) {
          const ownerRepo = `${repository.properties.owner}/${repository.name}`;
          loadCommits(ownerRepo);
        }
      }
    } catch (err) {
      console.error('Failed to sync repository:', err);
    } finally {
      setSyncing(false);
    }
  };

  const handleDelete = async () => {
    if (!repository) return;
    if (!confirm(`Delete "${repository.name}"? This will also delete all relationships. This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    try {
      await api.entities.delete(repository.entity_key);
      router.push('/entities?type=Repository');
    } catch (err) {
      console.error('Failed to delete repository:', err);
      alert('Failed to delete repository');
      setDeleting(false);
    }
  };

  const handleEntityUpdate = (updatedEntity: Entity) => {
    setRepository(updatedEntity as RepositoryEntity);
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const formatRelativeDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return formatDate(dateStr);
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
            <Link
              href={`/graph?focus=${repository.entity_key}`}
              className="px-3 py-1.5 text-sm bg-cm-terracotta/10 text-cm-terracotta border border-cm-terracotta/30 rounded-lg hover:bg-cm-terracotta/20 transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3" strokeWidth={2} />
                <circle cx="5" cy="6" r="2" strokeWidth={2} />
                <circle cx="19" cy="6" r="2" strokeWidth={2} />
                <circle cx="5" cy="18" r="2" strokeWidth={2} />
                <circle cx="19" cy="18" r="2" strokeWidth={2} />
                <path strokeWidth={2} d="M12 9V7M12 15v2M9.5 10.5l-3-3M14.5 10.5l3-3M9.5 13.5l-3 3M14.5 13.5l3 3" />
              </svg>
              View Network
            </Link>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-[#7c5cbf] flex items-center justify-center text-cm-ivory text-lg font-medium">
            R
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">{repository.name}</h1>
            <Link
              href="/entities?type=Repository"
              className="text-sm text-[#7c5cbf] hover:underline"
            >
              Repository
            </Link>
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

      {/* Tabs */}
      <div className="border-b border-cm-sand bg-cm-cream">
        <div className="flex">
          {(['overview', 'commits', 'stats', 'properties', 'relationships', 'json'] as TabType[]).map((tab) => (
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
                  {props.url && (
                    <div className="flex justify-between">
                      <dt className="text-cm-coffee/70">Git URL</dt>
                      <dd>
                        <a
                          href={props.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-cm-terracotta hover:underline font-mono text-xs"
                        >
                          {props.url}
                        </a>
                      </dd>
                    </div>
                  )}
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
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Open Issues</dt>
                    <dd className="text-cm-charcoal">{props.open_issues ?? '-'}</dd>
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

        {activeTab === 'commits' && (
          <div className="max-w-4xl">
            {loadingCommits ? (
              <p className="text-cm-coffee">Loading commits...</p>
            ) : commits.length > 0 ? (
              <div className="space-y-3">
                {commits.map((commit) => (
                  <div
                    key={commit.sha}
                    className="p-4 bg-cm-cream border border-cm-sand rounded-lg"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-cm-charcoal font-medium truncate">
                          {commit.message}
                        </p>
                        <div className="flex items-center gap-3 mt-2 text-sm text-cm-coffee">
                          <span>{commit.author}</span>
                          <span className="text-cm-coffee/50">•</span>
                          <span>{formatRelativeDate(commit.date)}</span>
                          {commit.co_authors.length > 0 && (
                            <>
                              <span className="text-cm-coffee/50">•</span>
                              <span className="text-cm-terracotta">
                                +{commit.co_authors.length} co-author{commit.co_authors.length > 1 ? 's' : ''}
                              </span>
                            </>
                          )}
                        </div>
                        {commit.co_authors.length > 0 && (
                          <div className="mt-1 text-xs text-cm-coffee/70">
                            Co-authored by: {commit.co_authors.join(', ')}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-sm flex-shrink-0">
                        <span className="text-green-600">+{commit.additions}</span>
                        <span className="text-red-600">-{commit.deletions}</span>
                        <code className="px-2 py-0.5 bg-cm-sand rounded text-xs font-mono">
                          {commit.sha}
                        </code>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No commits found. Click Sync to fetch commit history.</p>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="max-w-4xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-cm-charcoal">Daily Activity Statistics</h3>
              <button
                onClick={handleSyncStats}
                disabled={syncingStats}
                className="px-4 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {syncingStats ? (
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
                    Sync Stats
                  </>
                )}
              </button>
            </div>

            {loadingStats ? (
              <p className="text-cm-coffee">Loading stats...</p>
            ) : stats.length > 0 ? (
              <div className="space-y-6">
                {/* Summary cards */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="p-4 bg-cm-cream border border-cm-sand rounded-lg">
                    <p className="text-2xl font-semibold text-cm-charcoal">
                      {stats.reduce((sum, s) => sum + s.commits_count, 0)}
                    </p>
                    <p className="text-sm text-cm-coffee">Total Commits</p>
                  </div>
                  <div className="p-4 bg-cm-cream border border-cm-sand rounded-lg">
                    <p className="text-2xl font-semibold text-green-600">
                      +{stats.reduce((sum, s) => sum + s.additions, 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-cm-coffee">Lines Added</p>
                  </div>
                  <div className="p-4 bg-cm-cream border border-cm-sand rounded-lg">
                    <p className="text-2xl font-semibold text-red-600">
                      -{stats.reduce((sum, s) => sum + s.deletions, 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-cm-coffee">Lines Removed</p>
                  </div>
                  <div className="p-4 bg-cm-cream border border-cm-sand rounded-lg">
                    <p className="text-2xl font-semibold text-cm-terracotta">
                      {stats.reduce((sum, s) => sum + s.ai_assisted_commits, 0)}
                    </p>
                    <p className="text-sm text-cm-coffee">AI-Assisted</p>
                  </div>
                </div>

                {/* Daily activity table */}
                <div className="border border-cm-sand rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-cm-cream">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-cm-coffee">Date</th>
                        <th className="px-4 py-3 text-right font-medium text-cm-coffee">Commits</th>
                        <th className="px-4 py-3 text-right font-medium text-cm-coffee">Additions</th>
                        <th className="px-4 py-3 text-right font-medium text-cm-coffee">Deletions</th>
                        <th className="px-4 py-3 text-right font-medium text-cm-coffee">Authors</th>
                        <th className="px-4 py-3 text-right font-medium text-cm-coffee">AI</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-cm-sand">
                      {stats.slice().reverse().map((stat) => (
                        <tr key={stat.date} className="hover:bg-cm-cream/50">
                          <td className="px-4 py-3 text-cm-charcoal">{formatDate(stat.date)}</td>
                          <td className="px-4 py-3 text-right text-cm-charcoal">{stat.commits_count}</td>
                          <td className="px-4 py-3 text-right text-green-600">+{stat.additions}</td>
                          <td className="px-4 py-3 text-right text-red-600">-{stat.deletions}</td>
                          <td className="px-4 py-3 text-right text-cm-charcoal">{stat.unique_authors}</td>
                          <td className="px-4 py-3 text-right text-cm-terracotta">{stat.ai_assisted_commits}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-cm-coffee/70 italic mb-4">No stats available yet.</p>
                <p className="text-sm text-cm-coffee/50">Click "Sync Stats" to fetch and aggregate commit statistics from GitHub.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'properties' && (
          <div className="max-w-4xl">
            <EntityPropertiesPanel entity={repository} />
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            <EntityRelationshipsPanel entity={repository} />
          </div>
        )}

        {activeTab === 'json' && (
          <div className="max-w-4xl">
            <EntityJsonEditor entity={repository} onSave={handleEntityUpdate} />
          </div>
        )}
      </div>
    </div>
  );
}
