'use client';

import { useEffect, useRef } from 'react';
import { ChatMessage as ChatMessageType } from '@/types';
import { ChatMessage } from './chat-message';

interface ChatWindowProps {
  messages: ChatMessageType[];
}

export function ChatWindow({ messages }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-cm-cream">
        <div className="text-center">
          <p className="text-cm-coffee mb-2">No messages yet</p>
          <p className="text-sm text-cm-coffee/70">
            Start the conversation by sending a message below
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-cm-cream p-4">
      <div className="max-w-3xl mx-auto">
        {messages.map((message) => (
          <ChatMessage key={message.message_key} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
