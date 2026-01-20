'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Agent, ClientType } from '@/types';
import { AgentStatus } from '@/components/agent-status';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';
import { useAuthStore } from '@/lib/stores/auth-store';

const CLIENT_CONFIG: Record<ClientType, { label: string; icon: string }> = {
  'claude-code': { label: 'Claude Code', icon: '/icons/claude_code.svg' },
  'claude-desktop': { label: 'Claude Desktop', icon: '/icons/claude_desktop.svg' },
  'codex': { label: 'Codex', icon: '/icons/gpt_codex.svg' },
  'gemini-cli': { label: 'Gemini CLI', icon: '/icons/gemini_cli.svg' },
  'cursor': { label: 'Cursor', icon: '/icons/cursor.svg' },
};

type ScopeFilter = 'my-agents' | 'all-domain' | string; // string for team_key

export default function AgentsPage() {
  const { user: currentUser } = useAuthStore();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterClient, setFilterClient] = useState<string>('all');
  const [filterScope, setFilterScope] = useState<ScopeFilter>('my-agents');
  const [showInactive, setShowInactive] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'domain_admin';
  const userTeams = currentUser?.teams || [];

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

  // Get unique clients from agents for filter buttons
  const availableClients = [...new Set(agents.map(a => a.client).filter(Boolean))] as ClientType[];

  // Filter agents by scope
  const filteredAgents = (() => {
    if (filterScope === 'my-agents') {
      // Show only agents belonging to the current user
      return agents.filter(a => a.user_key === currentUser?.user_key);
    } else if (filterScope === 'all-domain') {
      // Show all agents in the domain (admin only)
      return agents;
    } else {
      // Filter by specific team_key
      return agents.filter(a => a.team_key === filterScope);
    }
  })();

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
                'px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-2',
                filterClient === client
                  ? 'bg-cm-terracotta text-cm-ivory'
                  : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
              )}
            >
              <img src={CLIENT_CONFIG[client]?.icon} alt="" className="w-4 h-4" />
              {CLIENT_CONFIG[client]?.label || client}
            </button>
          ))}
        </div>

        {/* Scope filter dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-cm-coffee">Scope:</label>
          <select
            value={filterScope}
            onChange={(e) => setFilterScope(e.target.value as ScopeFilter)}
            className="px-3 py-1.5 text-sm border border-cm-sand rounded-lg bg-cm-cream text-cm-charcoal focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50"
          >
            <option value="my-agents">My Agents</option>
            {userTeams.map((team) => (
              <option key={team.team_key} value={team.team_key}>
                {team.name}
              </option>
            ))}
            {isAdmin && <option value="all-domain">All Domain Agents</option>}
          </select>
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
