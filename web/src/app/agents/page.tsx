'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Agent } from '@/types';
import { AgentStatus } from '@/components/agent-status';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAgents() {
      try {
        const res = await api.agents.list();
        setAgents(res.data?.agents || []);
      } catch (err) {
        console.error('Failed to load agents:', err);
      } finally {
        setLoading(false);
      }
    }

    loadAgents();
  }, []);

  const activeAgents = agents.filter((a) => a.is_active);
  const inactiveAgents = agents.filter((a) => !a.is_active);

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
                  <AgentStatus key={agent.agent_key} agent={agent} />
                ))}
              </div>
            </div>
          )}

          {inactiveAgents.length > 0 && (
            <div>
              <h2 className="font-medium text-cm-coffee mb-4">Inactive Agents</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {inactiveAgents.map((agent) => (
                  <AgentStatus key={agent.agent_key} agent={agent} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
