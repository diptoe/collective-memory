'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Agent, ClientType } from '@/types';
import { AgentStatus } from '@/components/agent-status';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';

const CLIENT_LABELS: Record<ClientType, string> = {
  'claude-code': 'Claude Code',
  'claude-desktop': 'Claude Desktop',
  'codex': 'Codex',
  'gemini-cli': 'Gemini CLI',
};

const CLIENT_COLORS: Record<ClientType, string> = {
  'claude-code': 'bg-orange-100 text-orange-800',
  'claude-desktop': 'bg-purple-100 text-purple-800',
  'codex': 'bg-green-100 text-green-800',
  'gemini-cli': 'bg-blue-100 text-blue-800',
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [filterClient, setFilterClient] = useState<string>('all');
  const [showInactive, setShowInactive] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const loadAgents = async () => {
    try {
      const params: { active_only?: boolean; client?: string } = {};
      if (!showInactive) {
        params.active_only = true;
      }
      if (filterClient !== 'all') {
        params.client = filterClient;
      }
      const res = await api.agents.list(params);
      setAgents(res.data?.agents || []);
    } catch (err) {
      console.error('Failed to load agents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, [filterClient, showInactive]);

  const handleDeleteAgent = async (agentKey: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;

    setDeleting(true);
    try {
      await api.agents.delete(agentKey);
      setSelectedAgent(null);
      await loadAgents();
    } catch (err) {
      console.error('Failed to delete agent:', err);
      alert('Failed to delete agent. It may still be active.');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteAllInactive = async () => {
    if (!confirm(`Are you sure you want to delete all ${inactiveAgents.length} inactive agents?`)) return;

    setDeleting(true);
    try {
      const res = await api.agents.deleteInactive();
      alert(`Deleted ${res.data?.deleted_count || 0} inactive agents`);
      await loadAgents();
    } catch (err) {
      console.error('Failed to delete inactive agents:', err);
      alert('Failed to delete inactive agents');
    } finally {
      setDeleting(false);
    }
  };

  const activeAgents = agents.filter((a) => a.is_active);
  const inactiveAgents = agents.filter((a) => !a.is_active);

  // Get unique clients from agents for filter buttons
  const availableClients = [...new Set(agents.map(a => a.client).filter(Boolean))] as ClientType[];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading agents...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Agent Status
          </h1>
          <p className="text-cm-coffee mt-1">
            Monitor and coordinate AI agents
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-cm-success" />
            <span className="text-sm text-cm-coffee">{activeAgents.length} Online</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-cm-sand" />
            <span className="text-sm text-cm-coffee">{inactiveAgents.length} Offline</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFilterClient('all')}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              filterClient === 'all'
                ? 'bg-cm-terracotta text-cm-ivory'
                : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
            )}
          >
            All Clients
          </button>
          {availableClients.map((client) => (
            <button
              key={client}
              onClick={() => setFilterClient(client)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                filterClient === client
                  ? 'bg-cm-terracotta text-cm-ivory'
                  : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
              )}
            >
              {CLIENT_LABELS[client] || client}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-sm text-cm-coffee">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="rounded border-cm-sand"
          />
          Show inactive
        </label>
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-cm-coffee mb-4">No agents registered yet.</p>
          <p className="text-sm text-cm-coffee/70">
            Agents will appear here once they register with the platform.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {activeAgents.length > 0 && (
            <div>
              <h2 className="font-medium text-cm-charcoal mb-4">Active Agents</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {activeAgents.map((agent) => (
                  <AgentStatus
                    key={agent.agent_key}
                    agent={agent}
                    onClick={() => setSelectedAgent(agent)}
                  />
                ))}
              </div>
            </div>
          )}

          {showInactive && inactiveAgents.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-medium text-cm-coffee">Inactive Agents</h2>
                <button
                  onClick={handleDeleteAllInactive}
                  disabled={deleting}
                  className="px-3 py-1.5 text-sm bg-cm-error/10 text-cm-error rounded-lg hover:bg-cm-error/20 transition-colors disabled:opacity-50"
                >
                  {deleting ? 'Deleting...' : 'Delete All Inactive'}
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {inactiveAgents.map((agent) => (
                  <AgentStatus
                    key={agent.agent_key}
                    agent={agent}
                    onClick={() => setSelectedAgent(agent)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detail modal */}
      {selectedAgent && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-40"
          onClick={() => setSelectedAgent(null)}
        >
          <div
            className="bg-cm-ivory rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-cm-sand flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-cm-ivory font-medium"
                  style={{ backgroundColor: selectedAgent.persona?.color || '#2d2d2d' }}
                >
                  {selectedAgent.agent_id.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-semibold text-cm-charcoal">
                    {selectedAgent.agent_id}
                  </h3>
                  <p className="text-sm text-cm-coffee">
                    {selectedAgent.persona?.name || selectedAgent.role || 'No persona'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                {/* Status indicator */}
                <div className="flex items-center gap-2">
                  <div className={cn(
                    'w-3 h-3 rounded-full',
                    selectedAgent.is_active ? 'bg-cm-success' : 'bg-cm-sand'
                  )} />
                  <span className="text-sm text-cm-charcoal">
                    {selectedAgent.is_active ? 'Online' : 'Offline'}
                  </span>
                </div>

                {/* Agent Key */}
                <div>
                  <h4 className="text-sm font-medium text-cm-coffee mb-1">Agent Key</h4>
                  <p className="font-mono text-sm text-cm-charcoal">{selectedAgent.agent_key}</p>
                </div>

                {/* Client and Model */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Client</h4>
                    {selectedAgent.client ? (
                      <span className={cn(
                        'px-2 py-1 rounded text-xs',
                        CLIENT_COLORS[selectedAgent.client] || 'bg-gray-100 text-gray-800'
                      )}>
                        {CLIENT_LABELS[selectedAgent.client] || selectedAgent.client}
                      </span>
                    ) : (
                      <span className="text-sm text-cm-coffee/50">Not specified</span>
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Model</h4>
                    {selectedAgent.model ? (
                      <span className="px-2 py-1 bg-cm-sand rounded text-xs text-cm-coffee">
                        {selectedAgent.model.name}
                      </span>
                    ) : (
                      <span className="text-sm text-cm-coffee/50">Not specified</span>
                    )}
                  </div>
                </div>

                {/* Persona */}
                {selectedAgent.persona && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Persona</h4>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center text-cm-ivory text-xs"
                        style={{ backgroundColor: selectedAgent.persona.color }}
                      >
                        {selectedAgent.persona.name[0]}
                      </div>
                      <span className="text-sm text-cm-charcoal">{selectedAgent.persona.name}</span>
                      <span className="text-xs text-cm-coffee">({selectedAgent.persona.role})</span>
                    </div>
                  </div>
                )}

                {/* Focus */}
                {selectedAgent.focus && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Current Focus</h4>
                    <p className="text-sm text-cm-charcoal bg-cm-sand/30 p-2 rounded-lg">
                      {selectedAgent.focus}
                    </p>
                    {selectedAgent.focus_updated_at && (
                      <p className="text-xs text-cm-coffee/50 mt-1">
                        Updated: {formatDateTime(selectedAgent.focus_updated_at)}
                      </p>
                    )}
                  </div>
                )}

                {/* Current Task */}
                {selectedAgent.status?.current_task && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-1">Current Task</h4>
                    <div className="flex items-center gap-2">
                      {selectedAgent.status.progress && (
                        <span className={cn(
                          'px-2 py-0.5 text-xs rounded-full',
                          selectedAgent.status.progress === 'completed' ? 'bg-cm-success text-cm-ivory' :
                          selectedAgent.status.progress === 'blocked' ? 'bg-cm-error text-cm-ivory' :
                          selectedAgent.status.progress === 'in_progress' ? 'bg-cm-terracotta text-cm-ivory' :
                          'bg-cm-sand text-cm-coffee'
                        )}>
                          {selectedAgent.status.progress.replace('_', ' ')}
                        </span>
                      )}
                      <span className="text-sm text-cm-charcoal">{selectedAgent.status.current_task}</span>
                    </div>
                  </div>
                )}

                {/* Blocker */}
                {selectedAgent.status?.blocker && (
                  <div className="p-3 bg-cm-error/10 rounded-lg">
                    <h4 className="text-sm font-medium text-cm-error mb-1">Blocker</h4>
                    <p className="text-sm text-cm-error/80">{selectedAgent.status.blocker}</p>
                  </div>
                )}

                {/* Capabilities */}
                {selectedAgent.capabilities && selectedAgent.capabilities.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-2">Capabilities</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedAgent.capabilities.map((cap) => (
                        <span
                          key={cap}
                          className="px-3 py-1 text-sm bg-cm-terracotta/10 rounded-full text-cm-terracotta"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Actions */}
                {selectedAgent.status?.recent_actions && selectedAgent.status.recent_actions.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-cm-coffee mb-2">Recent Actions</h4>
                    <ul className="text-sm text-cm-charcoal space-y-1">
                      {selectedAgent.status.recent_actions.map((action, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-cm-coffee">•</span>
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="pt-4 border-t border-cm-sand">
                  <div className="grid grid-cols-2 gap-4 text-xs text-cm-coffee">
                    <div>
                      <span className="block">Last Heartbeat</span>
                      <span className="text-cm-charcoal">{formatDateTime(selectedAgent.last_heartbeat)}</span>
                    </div>
                    <div>
                      <span className="block">Registered</span>
                      <span className="text-cm-charcoal">{formatDateTime(selectedAgent.created_at)}</span>
                    </div>
                  </div>

                  {/* Delete button for inactive agents */}
                  {!selectedAgent.is_active && (
                    <button
                      onClick={() => handleDeleteAgent(selectedAgent.agent_key)}
                      disabled={deleting}
                      className="mt-4 w-full px-4 py-2 text-sm bg-cm-error/10 text-cm-error rounded-lg hover:bg-cm-error/20 transition-colors disabled:opacity-50"
                    >
                      {deleting ? 'Deleting...' : 'Delete Agent'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
