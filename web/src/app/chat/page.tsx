'use client';

import { useEffect, useState, useCallback } from 'react';
import { api } from '@/lib/api';
import { useStreaming } from '@/hooks/use-streaming';
import { Conversation, Persona, ChatMessage } from '@/types';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { ChatWindow } from '@/components/chat/chat-window';
import { ChatInput } from '@/components/chat/chat-input';

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [streamingMessageKey, setStreamingMessageKey] = useState<string | null>(null);

  // Load conversations and personas
  useEffect(() => {
    async function loadData() {
      try {
        const [convRes, personaRes] = await Promise.all([
          api.conversations.list(),
          api.personas.list(),
        ]);

        setConversations(convRes.data?.conversations || []);
        setPersonas(personaRes.data?.personas || []);
      } catch (err) {
        console.error('Failed to load chat data:', err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Load messages when active conversation changes
  useEffect(() => {
    if (!activeConversation) {
      setMessages([]);
      return;
    }

    async function loadMessages() {
      try {
        const res = await api.conversations.getMessages(activeConversation!.conversation_key);
        setMessages(res.data?.messages || []);
      } catch (err) {
        console.error('Failed to load messages:', err);
      }
    }

    loadMessages();
  }, [activeConversation?.conversation_key]);

  const handleSelectConversation = (conversation: Conversation) => {
    setActiveConversation(conversation);
  };

  const handleNewConversation = async (persona: Persona) => {
    try {
      const res = await api.conversations.create({
        persona_key: persona.persona_key,
        title: `Chat with ${persona.name}`,
      });

      if (res.success && res.data?.conversation) {
        const newConv = res.data.conversation;
        // Add persona to the conversation for display
        newConv.persona = persona;
        setConversations([newConv, ...conversations]);
        setActiveConversation(newConv);
      }
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  // Initialize streaming hook
  const { isStreaming, content: streamingContent, startStream, stopStream } = useStreaming({
    onContent: (newContent) => {
      // Update the streaming message content in real-time
      setMessages((prev) =>
        prev.map((m) =>
          m.message_key === streamingMessageKey
            ? { ...m, content: m.content + newContent }
            : m
        )
      );
    },
    onComplete: (fullContent, messageKey) => {
      // Replace streaming message with final message
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
      // Update message to show error
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
    if (!activeConversation || !content.trim() || isStreaming) return;

    try {
      // Add user message immediately for responsiveness
      const userMessageKey = `user-${Date.now()}`;
      const userMessage: ChatMessage = {
        message_key: userMessageKey,
        conversation_key: activeConversation.conversation_key,
        role: 'user',
        content,
        extra_data: {},
        created_at: new Date().toISOString(),
      };

      // Add streaming assistant message placeholder
      const streamingKey = `streaming-${Date.now()}`;
      const assistantMessage: ChatMessage = {
        message_key: streamingKey,
        conversation_key: activeConversation.conversation_key,
        persona_key: activeConversation.persona_key,
        role: 'assistant',
        content: '',
        extra_data: { streaming: true },
        created_at: new Date().toISOString(),
        persona: activeConversation.persona ? {
          name: activeConversation.persona.name,
          color: activeConversation.persona.color,
        } : undefined,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setStreamingMessageKey(streamingKey);

      // Start streaming response
      startStream(activeConversation.conversation_key, { content });
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  }, [activeConversation, isStreaming, startStream]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-cm-coffee">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <ChatSidebar
        conversations={conversations}
        personas={personas}
        activeConversation={activeConversation}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {activeConversation ? (
          <>
            {/* Chat header */}
            <div className="flex items-center gap-3 p-4 border-b border-cm-sand bg-cm-ivory">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-cm-ivory text-sm font-medium"
                style={{ backgroundColor: activeConversation.persona?.color || '#d97757' }}
              >
                {activeConversation.persona?.name?.[0] || 'A'}
              </div>
              <div>
                <h2 className="font-medium text-cm-charcoal">
                  {activeConversation.title || `Chat with ${activeConversation.persona?.name}`}
                </h2>
                <p className="text-xs text-cm-coffee">
                  {activeConversation.persona?.role}
                </p>
              </div>
            </div>

            {/* Messages */}
            <ChatWindow messages={messages} />

            {/* Input */}
            <ChatInput onSend={handleSendMessage} disabled={isStreaming} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-cm-coffee mb-4">
                Select a conversation or start a new one
              </p>
              <p className="text-sm text-cm-coffee/70">
                Choose a persona from the sidebar to begin
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
