'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Message, Agent } from '@/types';
import { MessageList } from '@/components/message-list';
import { cn } from '@/lib/utils';

interface ChannelTab {
  id: string;
  label: string;
  isAgent: boolean;
  isActive?: boolean;
}

export default function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState('all');
  const [channels, setChannels] = useState<ChannelTab[]>([
    { id: 'all', label: 'All', isAgent: false },
  ]);
  const [agentsLoading, setAgentsLoading] = useState(true);

  // Load registered agents for channel tabs
  useEffect(() => {
    async function loadAgents() {
      setAgentsLoading(true);
      try {
        const res = await api.agents.list({ active_only: false });
        const agents = res.data?.agents || [];

        // Build channel tabs: "All" + each registered agent
        const agentTabs: ChannelTab[] = agents.map((agent: Agent) => ({
          id: agent.agent_id,
          label: agent.agent_id,
          isAgent: true,
          isActive: agent.is_active,
        }));

        setChannels([
          { id: 'all', label: 'All', isAgent: false },
          ...agentTabs,
        ]);
      } catch (err) {
        console.error('Failed to load agents:', err);
      } finally {
        setAgentsLoading(false);
      }
    }

    loadAgents();
  }, []);

  // Load messages for selected channel
  useEffect(() => {
    async function loadMessages() {
      setLoading(true);
      try {
        // Pass undefined for 'all' to get all messages, otherwise pass the agent_id as channel
        const channelParam = channel === 'all' ? undefined : channel;
        const res = await api.messages.list(channelParam);
        setMessages(res.data?.messages || []);
      } catch (err) {
        console.error('Failed to load messages:', err);
      } finally {
        setLoading(false);
      }
    }

    loadMessages();
  }, [channel]);

  const unreadCount = messages.filter((m) => !m.is_read).length;

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
            Message Queue
          </h1>
          <p className="text-cm-coffee mt-1">
            Inter-agent communication and coordination
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <span className="px-3 py-1 bg-cm-terracotta text-cm-ivory rounded-full text-sm">
              {unreadCount} unread
            </span>
          )}
          <button className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors">
            + New Message
          </button>
        </div>
      </div>

      {/* Channel tabs - dynamically loaded from registered agents */}
      <div className="flex items-center gap-1 mb-6 border-b border-cm-sand overflow-x-auto">
        {agentsLoading ? (
          <div className="px-4 py-2 text-sm text-cm-coffee">Loading agents...</div>
        ) : (
          channels.map((ch) => (
            <button
              key={ch.id}
              onClick={() => setChannel(ch.id)}
              className={cn(
                'px-4 py-2 text-sm font-medium transition-colors relative whitespace-nowrap flex items-center gap-2',
                channel === ch.id
                  ? 'text-cm-terracotta'
                  : 'text-cm-coffee hover:text-cm-charcoal'
              )}
            >
              {ch.isAgent && (
                <span
                  className={cn(
                    'w-2 h-2 rounded-full',
                    ch.isActive ? 'bg-green-500' : 'bg-gray-400'
                  )}
                  title={ch.isActive ? 'Active' : 'Inactive'}
                />
              )}
              {ch.label}
              {channel === ch.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cm-terracotta" />
              )}
            </button>
          ))
        )}
      </div>

      {/* Messages */}
      <div className="bg-cm-ivory rounded-xl border border-cm-sand overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-cm-coffee">Loading messages...</p>
          </div>
        ) : (
          <MessageList messages={messages} />
        )}
      </div>
    </div>
  );
}
