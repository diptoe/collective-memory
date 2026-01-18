'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity, Relationship, Scope } from '@/types';
import { cn } from '@/lib/utils';
import { EntityPropertiesPanel } from '@/components/entity/entity-properties-panel';
import { EntityRelationshipsPanel } from '@/components/entity/entity-relationships-panel';
import { EntityJsonEditor } from '@/components/entity/entity-json-editor';

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

interface ProjectProperties {
  description?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  goals?: string[];
  team_size?: number;
  repository_count?: number;
  [key: string]: unknown;
}

interface ProjectEntity extends Entity {
  properties: ProjectProperties;
}

type TabType = 'overview' | 'repositories' | 'technologies' | 'team' | 'documents' | 'properties' | 'relationships' | 'json';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectKey = params.key as string;

  const [project, setProject] = useState<ProjectEntity | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Move scope modal state
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [availableScopes, setAvailableScopes] = useState<Scope[]>([]);
  const [selectedScope, setSelectedScope] = useState<Scope | null>(null);
  const [includeRelated, setIncludeRelated] = useState(true);
  const [movingScope, setMovingScope] = useState(false);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [moveResult, setMoveResult] = useState<{ total: number } | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);

  const loadProject = useCallback(async () => {
    try {
      const res = await api.entities.get(projectKey, true);
      const proj = res.data?.entity as ProjectEntity;
      if (proj) {
        setProject(proj);
      }
    } catch (err) {
      console.error('Failed to load project:', err);
    } finally {
      setLoading(false);
    }
  }, [projectKey]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

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

  const handleDelete = async () => {
    if (!project) return;
    if (!confirm(`Delete "${project.name}"? This will also delete all relationships. This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    try {
      await api.entities.delete(project.entity_key);
      router.push('/entities?type=Project');
    } catch (err) {
      console.error('Failed to delete project:', err);
      alert('Failed to delete project');
      setDeleting(false);
    }
  };

  const handleEntityUpdate = (updatedEntity: Entity) => {
    setProject(updatedEntity as ProjectEntity);
  };

  const handleMoveScope = async () => {
    if (!project || !selectedScope) return;

    setMovingScope(true);
    setMoveError(null);
    setMoveResult(null);

    try {
      const res = await api.entities.moveScope(project.entity_key, {
        scope_type: selectedScope.scope_type,
        scope_key: selectedScope.scope_key,
        include_related: includeRelated,
      });

      if (res.data) {
        setMoveResult({ total: res.data.total_updated });
        // Reload project to get updated scope
        await loadProject();
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

  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'in_progress':
        return 'bg-green-100 text-green-800';
      case 'planning':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-gray-100 text-gray-800';
      case 'on_hold':
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-cm-sand text-cm-coffee';
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  // Filter relationships by target entity type
  const getRelatedEntities = (type: string): Relationship[] => {
    if (!project?.relationships) return [];
    return [
      ...project.relationships.outgoing.filter(r => r.to_entity?.entity_type === type),
      ...project.relationships.incoming.filter(r => r.from_entity?.entity_type === type),
    ];
  };

  const repositories = getRelatedEntities('Repository');
  const technologies = getRelatedEntities('Technology');
  const team = getRelatedEntities('Person');
  const documents = getRelatedEntities('Document');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading project...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-cm-coffee mb-4">Project not found</p>
        <button
          onClick={() => router.push('/entities?type=Project')}
          className="text-cm-terracotta hover:underline"
        >
          Back to Projects
        </button>
      </div>
    );
  }

  const props = project.properties;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-cm-sand bg-cm-ivory p-4">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={() => router.push('/entities?type=Project')}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Entities
          </button>

          <div className="flex items-center gap-2">
            {canMoveScope && (
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
            <Link
              href={`/graph?focus=${project.entity_key}`}
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
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-[#e8a756] flex items-center justify-center text-cm-ivory text-lg font-medium">
            P
          </div>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">{project.name}</h1>
            <Link
              href="/entities?type=Project"
              className="text-sm text-[#e8a756] hover:underline"
            >
              Project
            </Link>
            <div className="flex items-center gap-2 mt-1">
              {props.status && (
                <span className={cn('px-2 py-0.5 text-xs rounded-full', getStatusColor(props.status))}>
                  {props.status}
                </span>
              )}
              {props.start_date && (
                <span className="text-xs text-cm-coffee">
                  Started {formatDate(props.start_date)}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-cm-cream border-b border-cm-sand">
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{repositories.length}</div>
          <div className="text-sm text-cm-coffee">Repositories</div>
        </div>
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{technologies.length}</div>
          <div className="text-sm text-cm-coffee">Technologies</div>
        </div>
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{team.length}</div>
          <div className="text-sm text-cm-coffee">Team Members</div>
        </div>
        <div className="bg-cm-ivory rounded-lg p-4 text-center">
          <div className="text-2xl font-semibold text-cm-charcoal">{documents.length}</div>
          <div className="text-sm text-cm-coffee">Documents</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-cm-sand bg-cm-cream">
        <div className="flex overflow-x-auto">
          {(['overview', 'repositories', 'technologies', 'team', 'documents', 'properties', 'relationships', 'json'] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-4 py-2 text-sm font-medium transition-colors capitalize whitespace-nowrap',
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

            {props.goals && props.goals.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Goals</h3>
                <ul className="list-disc list-inside space-y-1">
                  {props.goals.map((goal, i) => (
                    <li key={i} className="text-cm-charcoal">{goal}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Timeline</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Start Date</dt>
                    <dd className="text-cm-charcoal">{formatDate(props.start_date)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">End Date</dt>
                    <dd className="text-cm-charcoal">{formatDate(props.end_date)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Status</dt>
                    <dd className="text-cm-charcoal">{props.status || '-'}</dd>
                  </div>
                </dl>
              </div>

              <div>
                <h3 className="text-sm font-medium text-cm-coffee mb-2">Entity Info</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Entity Key</dt>
                    <dd className="text-cm-charcoal font-mono text-xs">{project.entity_key}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Confidence</dt>
                    <dd className="text-cm-charcoal">{Math.round(project.confidence * 100)}%</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-cm-coffee/70">Source</dt>
                    <dd className="text-cm-charcoal">{project.source || '-'}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'repositories' && (
          <div className="max-w-4xl">
            {repositories.length > 0 ? (
              <div className="space-y-2">
                {repositories.map((rel) => {
                  const entity = rel.to_entity?.entity_type === 'Repository' ? rel.to_entity : rel.from_entity;
                  return (
                    <div
                      key={rel.relationship_key}
                      onClick={() => entity && router.push(`/entities/repository/${entity.entity_key}`)}
                      className="flex items-center gap-3 p-3 bg-cm-cream border border-cm-sand rounded-lg cursor-pointer hover:border-cm-terracotta/50 transition-colors"
                    >
                      <div className="w-8 h-8 rounded bg-[#7c5cbf] flex items-center justify-center text-cm-ivory text-sm font-medium">
                        R
                      </div>
                      <div className="flex-1">
                        <span className="text-cm-charcoal font-medium">{entity?.name}</span>
                        <span className="ml-2 px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                          {rel.relationship_type}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No linked repositories.</p>
            )}
          </div>
        )}

        {activeTab === 'technologies' && (
          <div className="max-w-4xl">
            {technologies.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {technologies.map((rel) => {
                  const entity = rel.to_entity?.entity_type === 'Technology' ? rel.to_entity : rel.from_entity;
                  return (
                    <span
                      key={rel.relationship_key}
                      className="px-3 py-1.5 bg-[#5d8a66]/20 text-[#5d8a66] rounded-lg text-sm font-medium"
                    >
                      {entity?.name}
                    </span>
                  );
                })}
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No linked technologies.</p>
            )}
          </div>
        )}

        {activeTab === 'team' && (
          <div className="max-w-4xl">
            {team.length > 0 ? (
              <div className="space-y-2">
                {team.map((rel) => {
                  const entity = rel.to_entity?.entity_type === 'Person' ? rel.to_entity : rel.from_entity;
                  return (
                    <div
                      key={rel.relationship_key}
                      className="flex items-center gap-3 p-3 bg-cm-cream border border-cm-sand rounded-lg"
                    >
                      <div className="w-8 h-8 rounded-full bg-[#d97757] flex items-center justify-center text-cm-ivory text-sm font-medium">
                        {entity?.name?.[0] || 'P'}
                      </div>
                      <div className="flex-1">
                        <span className="text-cm-charcoal font-medium">{entity?.name}</span>
                        <span className="ml-2 px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                          {rel.relationship_type}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No team members linked.</p>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="max-w-4xl">
            {documents.length > 0 ? (
              <div className="space-y-2">
                {documents.map((rel) => {
                  const entity = rel.to_entity?.entity_type === 'Document' ? rel.to_entity : rel.from_entity;
                  return (
                    <div
                      key={rel.relationship_key}
                      onClick={() => entity && router.push(`/entities/document/${entity.entity_key}`)}
                      className="flex items-center gap-3 p-3 bg-cm-cream border border-cm-sand rounded-lg cursor-pointer hover:border-cm-terracotta/50 transition-colors"
                    >
                      <div className="w-8 h-8 rounded bg-[#6b8fa8] flex items-center justify-center text-cm-ivory text-sm font-medium">
                        D
                      </div>
                      <div className="flex-1">
                        <span className="text-cm-charcoal font-medium">{entity?.name}</span>
                        <span className="ml-2 px-2 py-0.5 bg-cm-terracotta/20 text-cm-terracotta rounded text-xs">
                          {rel.relationship_type}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-cm-coffee/70 italic">No linked documents.</p>
            )}
          </div>
        )}

        {activeTab === 'properties' && (
          <div className="max-w-4xl">
            <EntityPropertiesPanel entity={project} />
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            <EntityRelationshipsPanel entity={project} />
          </div>
        )}

        {activeTab === 'json' && (
          <div className="max-w-4xl">
            <EntityJsonEditor entity={project} onSave={handleEntityUpdate} />
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
                Move &quot;{project.name}&quot; to a different scope
              </p>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-4 space-y-4">
              {/* Current scope display */}
              {project.scope_type && (
                <div className="text-sm">
                  <span className="text-cm-coffee">Current scope: </span>
                  <span className={cn(
                    "inline-flex items-center gap-1 px-2 py-0.5 rounded border",
                    SCOPE_COLORS[project.scope_type] || 'bg-gray-100 text-gray-700 border-gray-200'
                  )}>
                    {SCOPE_ICONS[project.scope_type]} {project.scope_type}
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
