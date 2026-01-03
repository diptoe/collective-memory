'use client';

import { Conversation, Persona } from '@/types';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface ChatSidebarProps {
  conversations: Conversation[];
  personas: Persona[];
  activeConversation: Conversation | null;
  onSelectConversation: (conversation: Conversation) => void;
  onNewConversation: (persona: Persona) => void;
}

export function ChatSidebar({
  conversations,
  personas,
  activeConversation,
  onSelectConversation,
  onNewConversation,
}: ChatSidebarProps) {
  const [showPersonaPicker, setShowPersonaPicker] = useState(false);

  return (
    <div className="w-80 border-r border-cm-sand bg-cm-ivory flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-cm-sand">
        <div className="flex items-center justify-between">
          <h2 className="font-serif font-semibold text-cm-charcoal">Conversations</h2>
          <button
            onClick={() => setShowPersonaPicker(!showPersonaPicker)}
            className="px-3 py-1.5 text-sm bg-cm-terracotta text-cm-ivory rounded-md hover:bg-cm-sienna transition-colors"
          >
            + New
          </button>
        </div>
      </div>

      {/* Persona picker dropdown */}
      {showPersonaPicker && (
        <div className="p-4 border-b border-cm-sand bg-cm-sand/30">
          <p className="text-sm text-cm-coffee mb-3">Select a persona:</p>
          <div className="space-y-2">
            {personas.map((persona) => (
              <button
                key={persona.persona_key}
                onClick={() => {
                  onNewConversation(persona);
                  setShowPersonaPicker(false);
                }}
                className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-cm-sand transition-colors text-left"
              >
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-cm-ivory text-sm font-medium"
                  style={{ backgroundColor: persona.color }}
                >
                  {persona.name[0]}
                </div>
                <div>
                  <p className="text-sm font-medium text-cm-charcoal">{persona.name}</p>
                  <p className="text-xs text-cm-coffee">{persona.role}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-cm-coffee text-sm">
            No conversations yet.
            <br />
            Click &quot;+ New&quot; to start one.
          </div>
        ) : (
          <div className="py-2">
            {conversations.map((conversation) => (
              <button
                key={conversation.conversation_key}
                onClick={() => onSelectConversation(conversation)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                  activeConversation?.conversation_key === conversation.conversation_key
                    ? 'bg-cm-sand'
                    : 'hover:bg-cm-sand/50'
                )}
              >
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-cm-ivory text-sm font-medium flex-shrink-0"
                  style={{ backgroundColor: conversation.persona?.color || '#d97757' }}
                >
                  {conversation.persona?.name?.[0] || 'A'}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-cm-charcoal truncate">
                    {conversation.title || `Chat with ${conversation.persona?.name}`}
                  </p>
                  <p className="text-xs text-cm-coffee truncate">
                    {conversation.message_count} messages
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
