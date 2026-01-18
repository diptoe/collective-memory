'use client';

import { Message } from '@/types';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';

interface MessageListProps {
  messages: Message[];
  onMessageClick?: (message: Message) => void;
}

const priorityColors: Record<string, string> = {
  high: 'bg-cm-error/20 text-cm-error',
  normal: 'bg-cm-sand text-cm-coffee',
  low: 'bg-cm-info/20 text-cm-info',
};

const typeIcons: Record<string, string> = {
  question: '❓',
  handoff: '🤝',
  announcement: '📢',
  status: '📊',
};

export function MessageList({ messages, onMessageClick }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="p-8 text-center text-cm-coffee">
        No messages to display
      </div>
    );
  }

  return (
    <div className="divide-y divide-cm-sand">
      {messages.map((message) => (
        <div
          key={message.message_key}
          onClick={() => onMessageClick?.(message)}
          className={cn(
            'p-4 transition-colors',
            onMessageClick && 'cursor-pointer hover:bg-cm-sand/30',
            !message.is_read && 'bg-cm-terracotta/5'
          )}
        >
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-cm-charcoal flex items-center justify-center text-lg">
              {typeIcons[message.message_type] || '💬'}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-cm-charcoal">
                    {message.from_key}
                  </span>
                  <span className="text-cm-coffee/50">→</span>
                  <span className="text-cm-coffee">
                    {message.to_key || 'Broadcast'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'px-2 py-0.5 text-xs rounded-full',
                      priorityColors[message.priority]
                    )}
                  >
                    {message.priority}
                  </span>
                  {!message.is_read && (
                    <div className="w-2 h-2 rounded-full bg-cm-terracotta" />
                  )}
                </div>
              </div>

              <p className="text-xs text-cm-coffee/70 mb-2">
                Channel: <span className="font-mono">{message.channel}</span>
              </p>

              <div className="text-sm text-cm-charcoal bg-cm-sand/30 rounded-lg p-2">
                {typeof message.content === 'object' ? (
                  <pre className="whitespace-pre-wrap text-xs font-mono">
                    {JSON.stringify(message.content, null, 2)}
                  </pre>
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
        </div>
      ))}
    </div>
  );
}
