'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Message, Agent } from '@/types';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';

// Get person ID from environment
const PERSON_ID = process.env.NEXT_PUBLIC_PERSON_ID || 'unknown-user';

// Derive display name from person ID (e.g., 'wayne-houlden' -> 'Wayne Houlden')
function personIdToName(personId: string): string {
  return personId
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

const MESSAGE_TYPES = ['status', 'announcement', 'request', 'task', 'message'] as const;
const PRIORITIES = ['normal', 'high', 'urgent'] as const;

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
};

export default function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState('all');
  const [channels, setChannels] = useState<string[]>(['general']);
  const [clearing, setClearing] = useState(false);

  // New message modal state
  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newMessageChannel, setNewMessageChannel] = useState('general');
  const [newMessageContent, setNewMessageContent] = useState('');
  const [newMessageType, setNewMessageType] = useState<typeof MESSAGE_TYPES[number]>('status');
  const [newMessagePriority, setNewMessagePriority] = useState<typeof PRIORITIES[number]>('normal');
  const [newMessageRecipient, setNewMessageRecipient] = useState<string>('broadcast');
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);
  const [sending, setSending] = useState(false);


  // Track if we've ensured the person entity exists
  const personEnsured = useRef(false);

  // Load messages and extract channels
  const loadMessages = async () => {
    setLoading(true);
    try {
      const channelParam = channel === 'all' ? undefined : channel;
      const res = await api.messages.list(channelParam);
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
  }, [channel]);

  useEffect(() => {
    loadAgents();
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

  // Ensure person entity exists in the knowledge graph
  const ensurePersonEntity = async () => {
    if (personEnsured.current || PERSON_ID === 'unknown-user') return;

    try {
      // Check if person exists
      const res = await api.entities.get(PERSON_ID);
      if (res.data?.entity?.entity_key) {
        personEnsured.current = true;
        return;
      }
    } catch {
      // Entity doesn't exist, create it with PERSON_ID as the key
      try {
        await api.entities.create({
          entity_key: PERSON_ID,
          entity_type: 'Person',
          name: personIdToName(PERSON_ID),
          properties: { source: 'web-ui' },
        });
        personEnsured.current = true;
      } catch (createErr) {
        console.error('Failed to create person entity:', createErr);
      }
    }
  };

  const handleSendMessage = async () => {
    if (!newMessageContent.trim()) return;

    setSending(true);
    try {
      // Ensure person entity exists before first message
      await ensurePersonEntity();

      await api.messages.post({
        channel: newMessageChannel,
        from_agent: `human:${PERSON_ID}`,
        to_agent: newMessageRecipient === 'broadcast' ? undefined : newMessageRecipient,
        message_type: newMessageType,
        content: { text: newMessageContent },
        priority: newMessagePriority,
      });
      setShowNewMessage(false);
      setNewMessageContent('');
      setNewMessageRecipient('broadcast');
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

      {/* Channel tabs */}
      <div className="flex items-center gap-1 mb-6 border-b border-cm-sand overflow-x-auto">
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
                  !message.is_read && 'bg-cm-terracotta/5'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-cm-charcoal text-cm-ivory flex items-center justify-center text-sm font-mono">
                    {typeIcons[message.message_type] || '?'}
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
                          {message.from_agent}
                        </span>
                        <span className="text-cm-coffee/50">→</span>
                        <span className="text-cm-coffee">
                          {message.to_agent || 'Broadcast'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
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

                    <p className="text-xs text-cm-coffee/70 mb-2">
                      #{message.channel}
                    </p>

                    <div className="text-sm text-cm-charcoal">
                      {typeof message.content === 'object' && message.content !== null ? (
                        (message.content as { text?: string }).text || JSON.stringify(message.content)
                      ) : (
                        String(message.content)
                      )}
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
              {/* Channel */}
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
                    <option key={agent.agent_key} value={agent.agent_id}>
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
