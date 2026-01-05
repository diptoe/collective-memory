'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { useStreaming } from '@/hooks/use-streaming';
import { ChatMessage, Conversation } from '@/types';
import { ChatWindow } from '@/components/chat/chat-window';
import { ChatInput } from '@/components/chat/chat-input';
import { Trash2 } from 'lucide-react';

// Fixed model for initial implementation
const CHAT_MODEL = 'gemini-3-flash-preview';
const CHAT_MODEL_DISPLAY = 'Gemini 3 Flash Preview';

export default function ChatPage() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [streamingMessageKey, setStreamingMessageKey] = useState<string | null>(null);
  const conversationRef = useRef<Conversation | null>(null);

  // Initialize or get existing session conversation
  useEffect(() => {
    async function initSession() {
      try {
        // Check for existing session conversation
        const convRes = await api.conversations.list({ limit: 1 });
        const existingConversations = convRes.data?.conversations || [];

        // Find a session-type conversation or create one
        let sessionConv = existingConversations.find(c => c.title === 'Chat Session');

        if (sessionConv) {
          // Load existing messages
          const msgRes = await api.conversations.getMessages(sessionConv.conversation_key);
          setMessages(msgRes.data?.messages || []);
          setConversation(sessionConv);
          conversationRef.current = sessionConv;
        } else {
          // Create new session conversation - use default persona
          const personaRes = await api.personas.list();
          const personas = personaRes.data?.personas || [];
          const defaultPersona = personas.find(p => p.name.toLowerCase().includes('assistant')) || personas[0];

          if (defaultPersona) {
            const createRes = await api.conversations.create({
              persona_key: defaultPersona.persona_key,
              title: 'Chat Session',
            });

            if (createRes.success && createRes.data?.conversation) {
              setConversation(createRes.data.conversation);
              conversationRef.current = createRes.data.conversation;
            }
          }
        }
      } catch (err) {
        console.error('Failed to initialize chat session:', err);
      } finally {
        setLoading(false);
      }
    }

    initSession();
  }, []);

  // Streaming hook
  const { isStreaming, startStream } = useStreaming({
    onContent: (newContent) => {
      setMessages((prev) =>
        prev.map((m) =>
          m.message_key === streamingMessageKey
            ? { ...m, content: m.content + newContent }
            : m
        )
      );
    },
    onComplete: (fullContent, messageKey) => {
      setMessages((prev) =>
        prev.map((m) =>
          m.message_key === streamingMessageKey
            ? { ...m, message_key: messageKey, content: fullContent }
            : m
        )
      );
      setStreamingMessageKey(null);
    },
    onError: (error) => {
      console.error('Streaming error:', error);
      setMessages((prev) =>
        prev.map((m) =>
          m.message_key === streamingMessageKey
            ? { ...m, content: `Error: ${error}` }
            : m
        )
      );
      setStreamingMessageKey(null);
    },
  });

  const handleSendMessage = useCallback(async (content: string) => {
    const conv = conversationRef.current;
    if (!conv || !content.trim() || isStreaming) return;

    try {
      // Add user message immediately
      const userMessageKey = `user-${Date.now()}`;
      const userMessage: ChatMessage = {
        message_key: userMessageKey,
        conversation_key: conv.conversation_key,
        role: 'user',
        content,
        extra_data: {},
        created_at: new Date().toISOString(),
      };

      // Add streaming assistant message placeholder
      const streamingKey = `streaming-${Date.now()}`;
      const assistantMessage: ChatMessage = {
        message_key: streamingKey,
        conversation_key: conv.conversation_key,
        role: 'assistant',
        content: '',
        extra_data: { streaming: true },
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setStreamingMessageKey(streamingKey);

      // Start streaming response
      startStream(conv.conversation_key, { content });
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  }, [isStreaming, startStream]);

  const handleClearChat = async () => {
    if (!conversation || clearing) return;

    setClearing(true);
    try {
      // Clear messages locally
      setMessages([]);

      // Note: If we had a clear messages endpoint, we'd call it here
      // For now, we just clear the local state
    } finally {
      setClearing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Initializing chat...</p>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-cm-coffee mb-2">Unable to initialize chat session</p>
          <p className="text-sm text-cm-coffee/70">
            Please ensure personas are configured in the system.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-cm-sand bg-cm-ivory">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
            AI
          </div>
          <div>
            <h2 className="font-serif text-lg font-semibold text-cm-charcoal">
              Chat
            </h2>
            <p className="text-xs text-cm-coffee">
              {CHAT_MODEL_DISPLAY}
            </p>
          </div>
        </div>

        <button
          onClick={handleClearChat}
          disabled={clearing || messages.length === 0}
          className="flex items-center gap-2 px-3 py-2 text-sm text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Clear chat"
        >
          <Trash2 className="w-4 h-4" />
          Clear Chat
        </button>
      </div>

      {/* Messages */}
      <ChatWindow messages={messages} />

      {/* Input */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={isStreaming}
        placeholder="Ask about entities, relationships, or anything in the knowledge graph..."
      />
    </div>
  );
}
