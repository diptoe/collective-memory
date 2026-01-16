'use client';

import { ChatMessage as ChatMessageType } from '@/types';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

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
        <div className="text-sm break-words">
          <ReactMarkdown
            // Do not allow raw HTML in messages
            skipHtml
            components={{
              h1: ({ children }) => <h1 className="text-base font-semibold mt-2 mb-2">{children}</h1>,
              h2: ({ children }) => <h2 className="text-sm font-semibold mt-2 mb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-medium mt-2 mb-2">{children}</h3>,
              p: ({ children }) => (
                <p className="leading-relaxed whitespace-pre-wrap mb-2 last:mb-0">{children}</p>
              ),
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  className={cn(
                    'underline underline-offset-2',
                    isUser ? 'text-cm-ivory' : 'text-cm-coffee'
                  )}
                >
                  {children}
                </a>
              ),
              ul: ({ children }) => <ul className="list-disc pl-5 mb-2 last:mb-0">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 last:mb-0">{children}</ol>,
              li: ({ children }) => <li className="mb-1 last:mb-0">{children}</li>,
              blockquote: ({ children }) => (
                <blockquote
                  className={cn(
                    'border-l-2 pl-3 italic my-2',
                    isUser ? 'border-cm-ivory/40' : 'border-cm-coffee/40'
                  )}
                >
                  {children}
                </blockquote>
              ),
              pre: ({ children }) => (
                <pre
                  className={cn(
                    'my-2 overflow-x-auto rounded-md p-3 text-xs',
                    isUser ? 'bg-black/20' : 'bg-black/5'
                  )}
                >
                  {children}
                </pre>
              ),
              code: ({ className, children }) => {
                const isBlock = typeof className === 'string' && className.includes('language-');
                const text = String(children).replace(/\n$/, '');
                return (
                  <code
                    className={cn(
                      'font-mono',
                      isBlock
                        ? 'text-xs'
                        : cn(
                            'rounded px-1 py-0.5',
                            isUser ? 'bg-black/20' : 'bg-black/5'
                          )
                    )}
                  >
                    {text}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
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
