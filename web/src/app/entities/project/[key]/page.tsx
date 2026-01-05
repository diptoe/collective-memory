'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Entity, Relationship } from '@/types';
import { cn } from '@/lib/utils';

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

type TabType = 'overview' | 'repositories' | 'technologies' | 'team' | 'documents' | 'relationships';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectKey = params.key as string;

  const [project, setProject] = useState<ProjectEntity | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

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
          {(['overview', 'repositories', 'technologies', 'team', 'documents', 'relationships'] as TabType[]).map((tab) => (
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

        {activeTab === 'relationships' && (
          <div className="max-w-4xl">
            {project.relationships && (
              <>
                {project.relationships.outgoing.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-cm-coffee mb-3">
                      Outgoing Relationships ({project.relationships.outgoing.length})
                    </h3>
                    <div className="space-y-2">
                      {project.relationships.outgoing.map((rel) => (
                        <div
                          key={rel.relationship_key}
                          className="flex items-center gap-2 text-sm p-3 bg-cm-cream border border-cm-sand rounded-lg flex-wrap"
                        >
                          <span className="text-cm-charcoal font-medium">{project.name}</span>
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

                {project.relationships.incoming.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-cm-coffee mb-3">
                      Incoming Relationships ({project.relationships.incoming.length})
                    </h3>
                    <div className="space-y-2">
                      {project.relationships.incoming.map((rel) => (
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
                          <span className="text-cm-charcoal font-medium">{project.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {project.relationships.outgoing.length === 0 && project.relationships.incoming.length === 0 && (
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
