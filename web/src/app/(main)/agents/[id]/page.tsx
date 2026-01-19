'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Agent, ClientType } from '@/types';
import { use } from 'react';
import { cn } from '@/lib/utils';
import { MilestoneMetrics } from '@/components/milestone-metrics';

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    focus: '',
    capabilities: '',
  });

  useEffect(() => {
    loadAgent();
  }, [id]);

  async function loadAgent() {
    try {
      setLoading(true);
      const res = await api.agents.get(id);
      const a = res.data?.agent || res.data;

      if (a && (a as Agent).agent_key) {
        const agent = a as Agent;
        setAgent(agent);
        setFormData({
          focus: agent.focus || '',
          capabilities: agent.capabilities?.join(', ') || '',
        });
      } else {
        setError('Agent not found');
      }
    } catch (err: any) {
      console.error('Failed to load agent:', err);
      setError(err.response?.data?.msg || 'Failed to load agent');
    } finally {
      setLoading(false);
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      // Update focus
      if (formData.focus !== agent?.focus) {
        await api.agents.updateFocus(id, formData.focus);
      }

      await loadAgent();
      setIsEditing(false);
    } catch (err: any) {
      setError(err.response?.data?.msg || 'Failed to update agent');
    } finally {
      setSaving(false);
    }
  };

  const getClientColor = (client?: ClientType) => {
    switch (client) {
      case 'claude-code': return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'claude-desktop': return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'codex': return 'bg-green-50 text-green-700 border-green-200';
      case 'gemini-cli': return 'bg-blue-50 text-blue-700 border-blue-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive
      ? 'bg-green-50 text-green-700 border-green-200'
      : 'bg-gray-100 text-gray-500 border-gray-200';
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading agent...</p>
      </div>
    );
  }

  if (!agent && !loading) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          {error || 'Agent not found'}
        </div>
        <Link href="/agents" className="mt-4 inline-block text-cm-terracotta hover:underline">
          &larr; Back to Agents
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/agents"
            className="text-cm-coffee hover:text-cm-charcoal transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal flex items-center gap-3">
              {agent?.agent_id}
              <span className={`px-2 py-0.5 text-xs rounded-full border ${getStatusColor(agent?.is_active || false)}`}>
                {agent?.is_active ? 'active' : 'inactive'}
              </span>
            </h1>
            <p className="text-cm-coffee text-sm mt-1">
              Last seen: {agent?.last_heartbeat && formatTimeAgo(agent.last_heartbeat)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {isEditing ? (
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal border border-cm-sand rounded-lg"
            >
              Cancel
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna"
            >
              Edit Focus
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {isEditing ? (
        <form onSubmit={handleSave} className="bg-cm-ivory rounded-xl border border-cm-sand shadow-sm p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-cm-charcoal mb-1">
              Current Focus
            </label>
            <textarea
              rows={4}
              value={formData.focus}
              onChange={(e) => setFormData({ ...formData, focus: e.target.value })}
              className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
              placeholder="What is this agent currently working on?"
            />
          </div>

          <div className="flex justify-end pt-4 border-t border-cm-sand">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="col-span-2 space-y-6">
              {/* Focus */}
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Current Focus</h3>
                <div className="bg-cm-sand/20 rounded-lg p-4 text-cm-charcoal">
                  {agent?.focus || <span className="text-cm-coffee/50 italic">No focus set</span>}
                </div>
                {agent?.focus_updated_at && (
                  <p className="text-xs text-cm-coffee/70 mt-2">
                    Updated: {formatTimeAgo(agent.focus_updated_at)}
                  </p>
                )}
              </div>

              {/* Status */}
              {agent?.status && (
                <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                  <h3 className="text-sm font-medium text-cm-coffee mb-3">Status</h3>
                  <div className="space-y-3">
                    {agent.status.current_task && (
                      <div>
                        <span className="text-xs text-cm-coffee uppercase tracking-wider">Current Task</span>
                        <p className="text-sm text-cm-charcoal mt-1">{agent.status.current_task}</p>
                      </div>
                    )}
                    {agent.status.progress && (
                      <div>
                        <span className="text-xs text-cm-coffee uppercase tracking-wider">Progress</span>
                        <p className="mt-1">
                          <span className={`px-2 py-1 text-xs rounded-full border ${
                            agent.status.progress === 'completed' ? 'bg-green-50 text-green-700 border-green-200' :
                            agent.status.progress === 'in_progress' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                            agent.status.progress === 'blocked' ? 'bg-red-50 text-red-700 border-red-200' :
                            'bg-gray-50 text-gray-700 border-gray-200'
                          }`}>
                            {agent.status.progress}
                          </span>
                        </p>
                      </div>
                    )}
                    {agent.status.blocker && (
                      <div>
                        <span className="text-xs text-cm-coffee uppercase tracking-wider">Blocker</span>
                        <p className="text-sm text-red-600 mt-1">{agent.status.blocker}</p>
                      </div>
                    )}
                    {agent.status.recent_actions && agent.status.recent_actions.length > 0 && (
                      <div>
                        <span className="text-xs text-cm-coffee uppercase tracking-wider">Recent Actions</span>
                        <ul className="mt-1 space-y-1">
                          {agent.status.recent_actions.map((action, i) => (
                            <li key={i} className="text-sm text-cm-charcoal">{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Capabilities */}
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Capabilities</h3>
                <div className="flex flex-wrap gap-2">
                  {agent?.capabilities?.map(cap => (
                    <span key={cap} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-100">
                      {cap}
                    </span>
                  ))}
                  {(!agent?.capabilities || agent.capabilities.length === 0) && (
                    <span className="text-cm-coffee/50 text-sm italic">None registered</span>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {/* Context - Owner, Scope, Project */}
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-4">Context</h3>

                <div className="space-y-4">
                  {/* Owner */}
                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Owner</span>
                    <div className="mt-1 flex items-center gap-2">
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center text-cm-ivory text-xs font-medium"
                        style={{ backgroundColor: agent?.persona?.color || '#2d2d2d' }}
                      >
                        {agent?.user_initials?.toUpperCase() || agent?.agent_id.slice(0, 2).toUpperCase()}
                      </div>
                      <span className="text-sm text-cm-charcoal">
                        {agent?.user_name || 'Unknown'}
                      </span>
                    </div>
                  </div>

                  {/* Scope */}
                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Scope</span>
                    <p className="mt-1">
                      {agent?.team_name ? (
                        <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full border border-purple-200">
                          {agent.team_name}
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs bg-cm-sand/50 text-cm-coffee rounded-full border border-cm-sand">
                          Domain
                        </span>
                      )}
                    </p>
                  </div>

                  {/* Project */}
                  {agent?.project_name && (
                    <div>
                      <span className="text-xs text-cm-coffee uppercase tracking-wider">Project</span>
                      <p className="mt-1">
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full border border-blue-200">
                          {agent.project_name}
                        </span>
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Current Milestone */}
              {agent?.current_milestone_key && (
                <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                  <h3 className="text-sm font-medium text-cm-coffee mb-4">Current Milestone</h3>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {agent.current_milestone_status === 'started' && '🚀'}
                        {agent.current_milestone_status === 'completed' && '✅'}
                        {agent.current_milestone_status === 'blocked' && '🚫'}
                      </span>
                      <span className="text-sm font-medium text-cm-charcoal">
                        {agent.current_milestone_name}
                      </span>
                    </div>

                    <div>
                      <span className={cn(
                        'px-2 py-0.5 text-xs rounded-full',
                        agent.current_milestone_status === 'started' && 'bg-amber-100 text-amber-800',
                        agent.current_milestone_status === 'blocked' && 'bg-red-100 text-red-800',
                        agent.current_milestone_status === 'completed' && 'bg-green-100 text-green-800'
                      )}>
                        {agent.current_milestone_status}
                      </span>
                    </div>

                    {agent.current_milestone_started_at && (
                      <div className="text-xs text-cm-coffee">
                        Started: {new Date(agent.current_milestone_started_at).toLocaleString()}
                      </div>
                    )}

                    {/* Milestone metrics */}
                    <MilestoneMetrics entityKey={agent.current_milestone_key} className="mt-3" />
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-4">Metadata</h3>

                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Agent Key</span>
                    <p className="font-mono text-sm text-cm-charcoal mt-1 break-all">{agent?.agent_key}</p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Client</span>
                    <p className="mt-1">
                      <span className={`px-2 py-1 text-xs rounded-full border ${getClientColor(agent?.client)}`}>
                        {agent?.client || 'unknown'}
                      </span>
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Created</span>
                    <p className="text-sm text-cm-charcoal mt-1">
                      {agent?.created_at && new Date(agent.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div>
                    <span className="text-xs text-cm-coffee uppercase tracking-wider">Last Heartbeat</span>
                    <p className="text-sm text-cm-charcoal mt-1">
                      {agent?.last_heartbeat && new Date(agent.last_heartbeat).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Model */}
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Model</h3>
                {agent?.model ? (
                  <Link
                    href={`/models/${agent.model.model_key}`}
                    className="block p-3 bg-cm-sand/20 rounded-lg hover:bg-cm-sand/40 transition-colors"
                  >
                    <p className="font-medium text-cm-charcoal">{agent.model.name}</p>
                    <p className="text-xs text-cm-coffee mt-1">{agent.model.provider}</p>
                  </Link>
                ) : agent?.model_key ? (
                  <Link
                    href={`/models/${agent.model_key}`}
                    className="block p-3 bg-cm-sand/20 rounded-lg hover:bg-cm-sand/40 transition-colors"
                  >
                    <p className="font-mono text-sm text-cm-charcoal">{agent.model_key}</p>
                  </Link>
                ) : (
                  <span className="text-cm-coffee/50 text-sm italic">No model assigned</span>
                )}
              </div>

              {/* Persona */}
              <div className="bg-cm-ivory rounded-xl border border-cm-sand p-6">
                <h3 className="text-sm font-medium text-cm-coffee mb-3">Persona</h3>
                {agent?.persona ? (
                  <Link
                    href={`/personas/${agent.persona.persona_key}`}
                    className="block p-3 rounded-lg hover:opacity-80 transition-opacity"
                    style={{ backgroundColor: `${agent.persona.color}20` }}
                  >
                    <p className="font-medium text-cm-charcoal">{agent.persona.name}</p>
                    <p className="text-xs text-cm-coffee mt-1">{agent.persona.role}</p>
                  </Link>
                ) : agent?.persona_key ? (
                  <Link
                    href={`/personas/${agent.persona_key}`}
                    className="block p-3 bg-cm-sand/20 rounded-lg hover:bg-cm-sand/40 transition-colors"
                  >
                    <p className="font-mono text-sm text-cm-charcoal">{agent.persona_key}</p>
                  </Link>
                ) : (
                  <span className="text-cm-coffee/50 text-sm italic">No persona assigned</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
