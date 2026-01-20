'use client';

import Link from 'next/link';
import { Agent, ClientType } from '@/types';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';

interface AgentStatusProps {
  agent: Agent;
  onClick?: () => void;
  href?: string;
}

const CLIENT_CONFIG: Record<ClientType, { label: string; icon: string }> = {
  'claude-code': { label: 'Claude Code', icon: '/icons/claude_code.svg' },
  'claude-desktop': { label: 'Claude Desktop', icon: '/icons/claude_desktop.svg' },
  'codex': { label: 'Codex', icon: '/icons/gpt_codex.svg' },
  'gemini-cli': { label: 'Gemini CLI', icon: '/icons/gemini_cli.svg' },
  'cursor': { label: 'Cursor', icon: '/icons/cursor.svg' },
};

export function AgentStatus({ agent, onClick, href }: AgentStatusProps) {
  // Trust the API's is_active flag (15 minute heartbeat timeout)
  const isOnline = agent.is_active;

  const progressColors: Record<string, string> = {
    not_started: 'bg-cm-sand',
    in_progress: 'bg-cm-terracotta',
    blocked: 'bg-cm-error',
    completed: 'bg-cm-success',
  };

  // Get display values
  const clientConfig = agent.client ? CLIENT_CONFIG[agent.client] : null;
  const personaName = agent.persona?.name || agent.role;
  const personaColor = agent.persona?.color;
  const modelName = agent.model?.name;
  // User initials for avatar (fallback to first 2 chars of agent_id)
  const avatarInitials = agent.user_initials?.toUpperCase() || agent.agent_id.slice(0, 2).toUpperCase();

  const cardClassName = cn(
    'block p-4 rounded-xl border border-cm-sand bg-cm-ivory transition-all',
    (onClick || href) && 'cursor-pointer hover:shadow-md hover:border-cm-terracotta/50'
  );

  const cardContent = (
    <>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-cm-ivory text-sm font-medium"
              style={{ backgroundColor: personaColor || '#2d2d2d' }}
            >
              {avatarInitials}
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
            <div className="flex items-center gap-2">
              <p className="text-xs text-cm-coffee">{personaName}</p>
              {agent.user_name && (
                <span className="text-xs text-cm-coffee/60">({agent.user_name})</span>
              )}
            </div>
          </div>
        </div>

        {/* Only show progress badge when there's an actual task */}
        {agent.status?.current_task && agent.status?.progress && (
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

      {/* Client, Model, Team, and Project badges */}
      <div className="flex flex-wrap gap-1 mb-3">
        {clientConfig && (
          <span className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee flex items-center gap-1">
            <img src={clientConfig.icon} alt="" className="w-4 h-4" />
            {clientConfig.label}
          </span>
        )}
        {modelName && (
          <span className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee">
            🧠 {modelName}
          </span>
        )}
        {/* Team or Domain badge */}
        {agent.team_name ? (
          <span className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee">
            👥 {agent.team_name}
          </span>
        ) : (
          <span className="px-2 py-0.5 text-xs bg-cm-sand/50 text-cm-coffee/70 rounded-full">
            🌐 Domain
          </span>
        )}
        {/* Project badge */}
        {agent.project_name && (
          <span className="px-2 py-0.5 text-xs bg-cm-sand rounded-full text-cm-coffee">
            📁 {agent.project_name}
          </span>
        )}
        {/* Current milestone badge */}
        {agent.current_milestone_name && (
          <span className={cn(
            'px-2 py-0.5 text-xs rounded-full',
            agent.current_milestone_status === 'started' && 'bg-cm-info/10 text-cm-info',
            agent.current_milestone_status === 'blocked' && 'bg-cm-error/10 text-cm-error',
            agent.current_milestone_status === 'completed' && 'bg-cm-success/10 text-cm-success'
          )}>
            🎯 {agent.current_milestone_name}
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
        <div className="flex items-center gap-2">
          {agent.is_focused && (
            <span className="px-1.5 py-0.5 text-xs bg-cm-terracotta/10 text-cm-terracotta rounded-full font-medium">
              🎯 FOCUSED
            </span>
          )}
          <span className={cn(isOnline ? 'text-cm-success' : 'text-cm-coffee/50')}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={cardClassName}>
        {cardContent}
      </Link>
    );
  }

  return (
    <div onClick={onClick} className={cardClassName}>
      {cardContent}
    </div>
  );
}
