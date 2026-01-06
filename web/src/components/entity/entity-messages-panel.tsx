'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Entity, Message } from '@/types';
import { api } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface EntityMessagesPanelProps {
  entity: Entity;
}

const typeIcons: Record<string, string> = {
  status: '#',
  announcement: '!',
  request: '?',
  task: '\u2192',
  message: '\u2709',
  acknowledged: '\uD83D\uDC4D',
  waiting: '\u23F8\uFE0F',
  resumed: '\u25B6\uFE0F',
};

const priorityColors: Record<string, string> = {
  urgent: 'bg-red-200 text-red-800',
  high: 'bg-red-100 text-red-700',
  normal: 'bg-cm-sand text-cm-coffee',
};

export function EntityMessagesPanel({ entity }: EntityMessagesPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMessages = async () => {
      try {
        const res = await api.messages.byEntity(entity.entity_key, { limit: 50 });
        setMessages(res.data?.messages || []);
      } catch (err) {
        console.error('Failed to load messages:', err);
      } finally {
        setLoading(false);
      }
    };

    loadMessages();
  }, [entity.entity_key]);

  if (loading) {
    return <p className="text-cm-coffee/70">Loading messages...</p>;
  }

  if (messages.length === 0) {
    return <p className="text-cm-coffee/70 italic">No messages linked to this entity.</p>;
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-cm-coffee mb-3">
        {messages.length} message{messages.length !== 1 ? 's' : ''} linked to this entity
      </p>
      {messages.map((message) => (
        <Link
          key={message.message_key}
          href={`/messages/${message.message_key}`}
          className={cn(
            'block p-3 bg-cm-cream border border-cm-sand rounded-lg hover:border-cm-terracotta/50 hover:shadow-sm transition-all',
            message.autonomous && 'border-l-4 border-l-purple-500 bg-purple-50/50'
          )}
        >
          <div className="flex items-start gap-2">
            <div className={cn(
              'w-7 h-7 rounded flex items-center justify-center text-xs font-mono flex-shrink-0',
              message.autonomous
                ? 'bg-purple-600 text-white'
                : 'bg-cm-charcoal text-cm-ivory'
            )}>
              {message.autonomous ? '\uD83E\uDD16' : (typeIcons[message.message_type] || '?')}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="font-medium text-cm-charcoal text-sm">
                  {message.from_agent}
                </span>
                {message.to_agent && (
                  <>
                    <span className="text-cm-coffee/50">\u2192</span>
                    <span className="text-cm-coffee text-sm">
                      {message.to_agent}
                    </span>
                  </>
                )}
                <span
                  className={cn(
                    'px-2 py-0.5 text-xs rounded-full',
                    priorityColors[message.priority]
                  )}
                >
                  {message.priority}
                </span>
                {message.autonomous && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-purple-600 text-white">
                    autonomous
                  </span>
                )}
                {message.confirmed && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">
                    confirmed
                  </span>
                )}
              </div>

              <p className="text-xs text-cm-coffee/70 mb-1">
                #{message.channel} &middot; {message.message_type}
              </p>

              <p className="text-sm text-cm-charcoal line-clamp-2">
                {typeof message.content === 'object' && message.content !== null
                  ? (message.content as { text?: string }).text || JSON.stringify(message.content)
                  : String(message.content)}
              </p>

              <p className="text-xs text-cm-coffee/50 mt-1">
                {formatDateTime(message.created_at)}
              </p>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
