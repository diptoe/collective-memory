'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Message } from '@/types';
import { MessageList } from '@/components/message-list';
import { cn } from '@/lib/utils';

export default function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState('general');
  const [channels] = useState(['general', 'backend', 'frontend', 'architect', 'testing']);

  useEffect(() => {
    async function loadMessages() {
      setLoading(true);
      try {
        const res = await api.messages.list(channel);
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

      {/* Channel tabs */}
      <div className="flex items-center gap-1 mb-6 border-b border-cm-sand">
        {channels.map((ch) => (
          <button
            key={ch}
            onClick={() => setChannel(ch)}
            className={cn(
              'px-4 py-2 text-sm font-medium transition-colors relative',
              channel === ch
                ? 'text-cm-terracotta'
                : 'text-cm-coffee hover:text-cm-charcoal'
            )}
          >
            {ch}
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
        ) : (
          <MessageList messages={messages} />
        )}
      </div>
    </div>
  );
}
