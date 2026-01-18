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
  'cursor': 'Cursor',
};

const CLIENT_COLORS: Record<ClientType, string> = {
  'claude-code': 'bg-orange-100 text-orange-800',
  'claude-desktop': 'bg-purple-100 text-purple-800',
  'codex': 'bg-green-100 text-green-800',
  'gemini-cli': 'bg-blue-100 text-blue-800',
  'cursor': 'bg-cyan-100 text-cyan-800',
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterClient, setFilterClient] = useState<string>('all');
  const [filterTeam, setFilterTeam] = useState<string>('all');
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

  // Get unique clients and teams from agents for filter buttons
  const availableClients = [...new Set(agents.map(a => a.client).filter(Boolean))] as ClientType[];
  const availableTeams = [...new Set(agents.map(a => a.team_name).filter(Boolean))] as string[];

  // Filter agents by team
  const filteredAgents = filterTeam === 'all'
    ? agents
    : filterTeam === 'domain'
      ? agents.filter(a => !a.team_name)
      : agents.filter(a => a.team_name === filterTeam);

  const activeAgents = filteredAgents.filter((a) => a.is_active);
  const inactiveAgents = filteredAgents.filter((a) => !a.is_active);

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
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Client filter */}
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

        {/* Team filter */}
        {availableTeams.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="text-xs text-cm-coffee/70 mr-1">Scope:</span>
            <button
              onClick={() => setFilterTeam('all')}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                filterTeam === 'all'
                  ? 'bg-purple-600 text-white'
                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
              )}
            >
              All
            </button>
            <button
              onClick={() => setFilterTeam('domain')}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                filterTeam === 'domain'
                  ? 'bg-purple-600 text-white'
                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
              )}
            >
              Domain
            </button>
            {availableTeams.map((team) => (
              <button
                key={team}
                onClick={() => setFilterTeam(team)}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-lg transition-colors',
                  filterTeam === team
                    ? 'bg-purple-600 text-white'
                    : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                )}
              >
                {team}
              </button>
            ))}
          </div>
        )}

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
                    href={`/agents/${agent.agent_id}`}
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
                    href={`/agents/${agent.agent_id}`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
