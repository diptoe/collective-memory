'use client';

import { ChatMessage as ChatMessageType } from '@/types';
import { cn } from '@/lib/utils';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className="px-4 py-2 bg-cm-sand/50 rounded-full text-sm text-cm-coffee">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      {!isUser && (
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-cm-ivory text-sm font-medium flex-shrink-0"
          style={{ backgroundColor: message.persona?.color || '#d97757' }}
        >
          {message.persona?.name?.[0] || 'A'}
        </div>
      )}

      {/* Message bubble */}
      <div
        className={cn(
          'max-w-[70%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-cm-terracotta text-cm-ivory rounded-br-md'
            : 'bg-cm-sand text-cm-charcoal rounded-bl-md'
        )}
      >
        {/* Persona name for assistant messages */}
        {!isUser && message.persona?.name && (
          <p className="text-xs font-medium mb-1 opacity-70">
            {message.persona.name}
          </p>
        )}

        {/* Message content */}
        <div className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </div>

        {/* Timestamp */}
        <p
          className={cn(
            'text-xs mt-2',
            isUser ? 'text-cm-ivory/70' : 'text-cm-coffee/70'
          )}
        >
          {new Date(message.created_at).toLocaleTimeString('en-AU', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>

      {/* User avatar placeholder */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-cm-coffee flex items-center justify-center text-cm-ivory text-sm font-medium flex-shrink-0">
          W
        </div>
      )}
    </div>
  );
}
