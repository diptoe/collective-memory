'use client';

import { Agent, ClientType } from '@/types';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';

interface AgentStatusProps {
  agent: Agent;
  onClick?: () => void;
}

const CLIENT_LABELS: Record<ClientType, string> = {
  'claude-code': 'Claude Code',
  'claude-desktop': 'Claude Desktop',
  'codex': 'Codex',
  'gemini': 'Gemini',
  'custom': 'Custom',
};

const CLIENT_COLORS: Record<ClientType, string> = {
  'claude-code': 'bg-orange-100 text-orange-800',
  'claude-desktop': 'bg-purple-100 text-purple-800',
  'codex': 'bg-green-100 text-green-800',
  'gemini': 'bg-blue-100 text-blue-800',
  'custom': 'bg-gray-100 text-gray-800',
};

export function AgentStatus({ agent, onClick }: AgentStatusProps) {
  // Trust the API's is_active flag (15 minute heartbeat timeout)
  const isOnline = agent.is_active;

  const progressColors: Record<string, string> = {
    not_started: 'bg-cm-sand',
    in_progress: 'bg-cm-terracotta',
    blocked: 'bg-cm-error',
    completed: 'bg-cm-success',
  };

  // Get display values
  const clientLabel = agent.client ? CLIENT_LABELS[agent.client] || agent.client : null;
  const clientColor = agent.client ? CLIENT_COLORS[agent.client] || 'bg-gray-100 text-gray-800' : null;
  const personaName = agent.persona?.name || agent.role;
  const personaColor = agent.persona?.color;
  const modelName = agent.model?.name;

  return (
    <div
      onClick={onClick}
      className={cn(
        'p-4 rounded-xl border border-cm-sand bg-cm-ivory transition-all',
        onClick && 'cursor-pointer hover:shadow-md hover:border-cm-terracotta/50'
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-cm-ivory text-sm font-medium"
              style={{ backgroundColor: personaColor || '#2d2d2d' }}
            >
              {agent.agent_id.slice(0, 2).toUpperCase()}
            </div>
            <div
              className={cn(
                'absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-cm-ivory',
                isOnline ? 'bg-cm-success' : 'bg-cm-sand'
              )}
            />
          </div>
          <div>
            <h3 className="font-medium text-cm-charcoal">{agent.agent_id}</h3>
            <p className="text-xs text-cm-coffee">{personaName}</p>
          </div>
        </div>

        {agent.status?.progress && (
          <span
            className={cn(
              'px-2 py-0.5 text-xs rounded-full text-cm-ivory capitalize',
              progressColors[agent.status.progress] || 'bg-cm-sand text-cm-coffee'
            )}
          >
            {agent.status.progress.replace('_', ' ')}
          </span>
        )}
      </div>

      {/* Client and Model badges */}
      <div className="flex flex-wrap gap-1 mb-3">
        {clientLabel && (
          <span className={cn('px-2 py-0.5 text-xs rounded-full', clientColor)}>
            {clientLabel}
          </span>
        )}
        {modelName && (
          <span className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee">
            {modelName}
          </span>
        )}
      </div>

      {/* Focus */}
      {agent.focus && (
        <div className="mb-3">
          <p className="text-xs text-cm-coffee/70 mb-1">Focus</p>
          <p className="text-sm text-cm-charcoal">{agent.focus}</p>
        </div>
      )}

      {agent.status?.current_task && (
        <div className="mb-3">
          <p className="text-xs text-cm-coffee/70 mb-1">Current Task</p>
          <p className="text-sm text-cm-charcoal">{agent.status.current_task}</p>
        </div>
      )}

      {agent.status?.blocker && (
        <div className="mb-3 p-2 bg-cm-error/10 rounded-lg">
          <p className="text-xs text-cm-error font-medium mb-1">Blocked</p>
          <p className="text-sm text-cm-error/80">{agent.status.blocker}</p>
        </div>
      )}

      {agent.capabilities && agent.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {agent.capabilities.slice(0, 4).map((cap) => (
            <span
              key={cap}
              className="px-2 py-0.5 text-xs bg-cm-terracotta/10 rounded-full text-cm-terracotta"
            >
              {cap}
            </span>
          ))}
          {agent.capabilities.length > 4 && (
            <span className="px-2 py-0.5 text-xs bg-cm-terracotta/10 rounded-full text-cm-terracotta">
              +{agent.capabilities.length - 4}
            </span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-cm-coffee/50">
        <span>Last heartbeat: {formatDateTime(agent.last_heartbeat)}</span>
        <span className={cn(isOnline ? 'text-cm-success' : 'text-cm-coffee/50')}>
          {isOnline ? 'Online' : 'Offline'}
        </span>
      </div>
    </div>
  );
}
