'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Message, Agent, Team } from '@/types';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';
import { Markdown } from '@/components/markdown/markdown';
import { useAuthStore } from '@/lib/stores/auth-store';

const MESSAGE_TYPES = ['status', 'announcement', 'request', 'task', 'message', 'acknowledged', 'waiting', 'resumed'] as const;
const PRIORITIES = ['normal', 'high', 'urgent'] as const;
const TIME_FILTERS = ['1h', '24h', '7d', 'all'] as const;
type TimeFilter = typeof TIME_FILTERS[number];

const priorityColors: Record<string, string> = {
  urgent: 'bg-red-200 text-red-800',
  high: 'bg-red-100 text-red-700',
  normal: 'bg-cm-sand text-cm-coffee',
};

const typeIcons: Record<string, string> = {
  status: '#',
  announcement: '!',
  request: '?',
  task: '→',
  message: '✉',
  acknowledged: '👍',
  waiting: '⏸️',
  resumed: '▶️',
};

export default function MessagesPage() {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState('all');
  const [channels, setChannels] = useState<string[]>(['general']);
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('24h');
  const [clearing, setClearing] = useState(false);

  // Scope filter state
  const [scopeFilter, setScopeFilter] = useState<string>('all'); // 'all', 'domain', or team_key
  const [teams, setTeams] = useState<Team[]>([]);

  // New message modal state
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newMessageChannel, setNewMessageChannel] = useState('general');
  const [newMessageContent, setNewMessageContent] = useState('');
  const [newMessageType, setNewMessageType] = useState<typeof MESSAGE_TYPES[number]>('status');
  const [newMessagePriority, setNewMessagePriority] = useState<typeof PRIORITIES[number]>('normal');
  const [newMessageRecipient, setNewMessageRecipient] = useState<string>('broadcast');
  const [newMessageScope, setNewMessageScope] = useState<string>('domain'); // 'domain' or team_key
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);
  const [sending, setSending] = useState(false);

  // Calculate since timestamp based on time filter
  const getSinceTimestamp = (filter: TimeFilter): string | undefined => {
    if (filter === 'all') return undefined;
    const now = new Date();
    switch (filter) {
      case '1h':
        return new Date(now.getTime() - 60 * 60 * 1000).toISOString();
      case '24h':
        return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
      case '7d':
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
      default:
        return undefined;
    }
  };

  // Load user's teams
  const loadTeams = async () => {
    try {
      const res = await api.teams.list({ status: 'active' });
      setTeams(res.data?.teams || []);
    } catch (err) {
      console.error('Failed to load teams:', err);
    }
  };

  // Load messages and extract channels
  const loadMessages = async () => {
    setLoading(true);
    try {
      const channelParam = channel === 'all' ? undefined : channel;
      const since = getSinceTimestamp(timeFilter);

      // Determine team_key filter based on scope selection
      let teamKeyParam: string | undefined;
      if (scopeFilter === 'domain') {
        // Domain-wide: explicitly filter for null team_key (backend handles this as empty string)
        teamKeyParam = '';
      } else if (scopeFilter !== 'all') {
        // Specific team
        teamKeyParam = scopeFilter;
      }
      // 'all' means no team_key filter - show all accessible messages

      const res = await api.messages.list(channelParam, { since, team_key: teamKeyParam });
      const msgs = res.data?.messages || [];
      setMessages(msgs);

      // Extract unique channels from all messages
      if (channel === 'all') {
        const uniqueChannels = [...new Set(msgs.map(m => m.channel))].filter(Boolean);
        if (uniqueChannels.length > 0) {
          setChannels(uniqueChannels);
        }
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load active agents for recipient selection
  const loadAgents = async () => {
    try {
      const res = await api.agents.list({ active_only: true });
      setActiveAgents(res.data?.agents || []);
    } catch (err) {
      console.error('Failed to load agents:', err);
    }
  };

  useEffect(() => {
    loadMessages();
  }, [channel, timeFilter, scopeFilter]);

  useEffect(() => {
    loadAgents();
    loadTeams();
  }, []);

  const handleClearMessages = async () => {
    if (!confirm('Are you sure you want to clear all messages? This cannot be undone.')) {
      return;
    }
    setClearing(true);
    try {
      await api.messages.clearAll();
      setMessages([]);
    } catch (err) {
      console.error('Failed to clear messages:', err);
    } finally {
      setClearing(false);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessageContent.trim()) return;
    if (!user?.user_key) {
      alert('You must be logged in to send messages');
      return;
    }

    setSending(true);
    try {
      await api.messages.post({
        channel: newMessageChannel,
        from_key: user.user_key,  // Use authenticated user's key
        to_key: newMessageRecipient === 'broadcast' ? undefined : newMessageRecipient,
        message_type: newMessageType,
        content: { text: newMessageContent },
        priority: newMessagePriority,
        team_key: newMessageScope === 'domain' ? undefined : newMessageScope,
      });
      setShowNewMessage(false);
      setNewMessageContent('');
      setNewMessageRecipient('broadcast');
      setNewMessageScope('domain');
      loadMessages();
    } catch (err) {
      console.error('Failed to send message:', err);
      alert('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  // Count messages with no readers (truly unread by any agent)
  const unreadCount = messages.filter((m) => (m.read_count || 0) === 0).length;

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
          {messages.length > 0 && (
            <button
              onClick={handleClearMessages}
              disabled={clearing}
              className="px-4 py-2 bg-cm-sand text-cm-coffee rounded-lg hover:bg-cm-sand/80 transition-colors disabled:opacity-50"
            >
              {clearing ? 'Clearing...' : 'Clear All'}
            </button>
          )}
          <button
            onClick={() => setShowNewMessage(true)}
            className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors"
          >
            + New Message
          </button>
        </div>
      </div>

      {/* Channel tabs and time filter */}
      <div className="flex items-center justify-between mb-6 border-b border-cm-sand">
        <div className="flex items-center gap-1 overflow-x-auto">
          <button
            onClick={() => setChannel('all')}
            className={cn(
              'px-4 py-2 text-sm font-medium transition-colors relative whitespace-nowrap',
              channel === 'all'
                ? 'text-cm-terracotta'
                : 'text-cm-coffee hover:text-cm-charcoal'
            )}
          >
            All
            {channel === 'all' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cm-terracotta" />
            )}
          </button>
          {channels.map((ch) => (
            <button
              key={ch}
              onClick={() => setChannel(ch)}
              className={cn(
                'px-4 py-2 text-sm font-medium transition-colors relative whitespace-nowrap flex items-center gap-2',
                channel === ch
                  ? 'text-cm-terracotta'
                  : 'text-cm-coffee hover:text-cm-charcoal'
              )}
            >
              #{ch}
              {channel === ch && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cm-terracotta" />
              )}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4 pb-2">
          {/* Scope filter dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-cm-coffee">Scope:</label>
            <select
              value={scopeFilter}
              onChange={(e) => setScopeFilter(e.target.value)}
              className={cn(
                'px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta',
                scopeFilter === 'all'
                  ? 'border-cm-sand bg-cm-ivory'
                  : scopeFilter === 'domain'
                  ? 'border-cm-terracotta bg-cm-terracotta/10'
                  : 'border-purple-500 bg-purple-50'
              )}
            >
              <option value="all">All Messages</option>
              <option value="domain">🌐 Domain-wide</option>
              {teams.length > 0 && (
                <optgroup label="Teams">
                  {teams.map((team) => (
                    <option key={team.team_key} value={team.team_key}>
                      👥 {team.name}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>

          {/* Time filter */}
          <div className="flex items-center gap-1">
            {TIME_FILTERS.map((filter) => (
              <button
                key={filter}
                onClick={() => setTimeFilter(filter)}
                className={cn(
                  'px-3 py-1 text-xs font-medium rounded-full transition-colors',
                  timeFilter === filter
                    ? 'bg-cm-terracotta text-cm-ivory'
                    : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
                )}
              >
                {filter === 'all' ? 'All time' : filter}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="bg-cm-ivory rounded-xl border border-cm-sand overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-cm-coffee">Loading messages...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="p-8 text-center text-cm-coffee">
            No messages to display
          </div>
        ) : (
          <div className="divide-y divide-cm-sand">
            {messages.map((message) => (
              <Link
                key={message.message_key}
                href={`/messages/${message.message_key}`}
                className={cn(
                  'block p-4 transition-colors cursor-pointer hover:bg-cm-sand/30',
                  !message.is_read && 'bg-cm-terracotta/5',
                  message.autonomous && 'bg-purple-50 border-l-4 border-purple-500'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-mono',
                    message.autonomous
                      ? 'bg-purple-600 text-white'
                      : 'bg-cm-charcoal text-cm-ivory'
                  )}>
                    {message.autonomous ? '🤖' : (typeIcons[message.message_type] || '?')}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        {/* Reply indicator */}
                        {message.has_parent && (
                          <span className="text-cm-coffee/50" title="This is a reply">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                            </svg>
                          </span>
                        )}
                        <span className="font-medium text-cm-charcoal">
                          {message.from_key}
                        </span>
                        <span className="text-cm-coffee/50">→</span>
                        <span className="text-cm-coffee">
                          {message.to_key || 'Broadcast'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {/* Confirmed badge */}
                        {message.confirmed && (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700 font-medium flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            CONFIRMED
                          </span>
                        )}
                        {/* Autonomous task badge */}
                        {message.autonomous && (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-purple-600 text-white font-medium flex items-center gap-1">
                            🤖 AUTONOMOUS
                          </span>
                        )}
                        {/* Reply count badge */}
                        {message.reply_count !== undefined && message.reply_count > 0 && (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-cm-terracotta/10 text-cm-terracotta flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                            </svg>
                            {message.reply_count}
                          </span>
                        )}
                        <span
                          className={cn(
                            'px-2 py-0.5 text-xs rounded-full',
                            priorityColors[message.priority]
                          )}
                        >
                          {message.priority}
                        </span>
                        {message.read_count !== undefined && message.read_count > 0 ? (
                          <span className="text-xs text-green-600 flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            {message.read_count}
                          </span>
                        ) : (
                          <span className="text-xs text-cm-coffee/50">unread</span>
                        )}
                      </div>
                    </div>

                    <p className="text-xs text-cm-coffee/70 mb-2 flex items-center gap-2">
                      <span>#{message.channel}</span>
                      {message.team_key ? (
                        <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 flex items-center gap-1">
                          <span>👥</span> {message.team_name || 'Team'}
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded bg-cm-sand/50 text-cm-coffee flex items-center gap-1">
                          <span>🌐</span> Domain
                        </span>
                      )}
                    </p>

                    <div className="text-sm text-cm-charcoal">
                      <Markdown
                        content={
                          typeof message.content === 'object' && message.content !== null
                            ? (message.content as { text?: string }).text || JSON.stringify(message.content)
                            : String(message.content)
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between mt-2 text-xs text-cm-coffee/50">
                      <span className="capitalize">{message.message_type}</span>
                      <span>{formatDateTime(message.created_at)}</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* New Message Modal */}
      {showNewMessage && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowNewMessage(false)}
        >
          <div
            className="bg-cm-ivory rounded-xl shadow-xl max-w-lg w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-cm-sand">
              <h2 className="font-serif text-xl font-semibold text-cm-charcoal">
                New Message
              </h2>
            </div>

            <div className="p-4 space-y-4">
              {/* Channel and Scope */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-cm-charcoal mb-1">
                    Channel
                  </label>
                  <input
                    type="text"
                    value={newMessageChannel}
                    onChange={(e) => setNewMessageChannel(e.target.value)}
                    placeholder="general"
                    className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-cm-charcoal mb-1">
                    Scope
                  </label>
                  <select
                    value={newMessageScope}
                    onChange={(e) => setNewMessageScope(e.target.value)}
                    className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                  >
                    <option value="domain">🌐 Domain-wide</option>
                    {teams.map((team) => (
                      <option key={team.team_key} value={team.team_key}>
                        👥 {team.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Recipient */}
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Recipient
                </label>
                <select
                  value={newMessageRecipient}
                  onChange={(e) => setNewMessageRecipient(e.target.value)}
                  className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                >
                  <option value="broadcast">Broadcast (All Agents)</option>
                  {activeAgents.map((agent) => (
                    <option key={agent.agent_key} value={agent.agent_key}>
                      {agent.agent_id}
                    </option>
                  ))}
                </select>
              </div>

              {/* Type and Priority */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-cm-charcoal mb-1">
                    Type
                  </label>
                  <select
                    value={newMessageType}
                    onChange={(e) => setNewMessageType(e.target.value as typeof MESSAGE_TYPES[number])}
                    className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                  >
                    {MESSAGE_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-cm-charcoal mb-1">
                    Priority
                  </label>
                  <select
                    value={newMessagePriority}
                    onChange={(e) => setNewMessagePriority(e.target.value as typeof PRIORITIES[number])}
                    className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta"
                  >
                    {PRIORITIES.map((priority) => (
                      <option key={priority} value={priority}>
                        {priority.charAt(0).toUpperCase() + priority.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Message Content */}
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Message
                </label>
                <textarea
                  value={newMessageContent}
                  onChange={(e) => setNewMessageContent(e.target.value)}
                  placeholder="Enter your message..."
                  rows={4}
                  className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta resize-none"
                />
              </div>
            </div>

            <div className="p-4 border-t border-cm-sand flex justify-end gap-2">
              <button
                onClick={() => setShowNewMessage(false)}
                className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSendMessage}
                disabled={sending || !newMessageContent.trim()}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
              >
                {sending ? 'Sending...' : 'Send Message'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
