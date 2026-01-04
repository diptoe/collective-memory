'use client';

import { useState, useCallback, useRef } from 'react';
import { streamMessage, StreamChunk, StreamOptions } from '@/lib/api/streaming';

/**
 * Options for the useStreaming hook
 */
export interface UseStreamingOptions {
  onChunk?: (chunk: StreamChunk) => void;
  onContent?: (content: string) => void;
  onContext?: (context: StreamChunk['context']) => void;
  onComplete?: (fullContent: string, messageKey: string, usage?: StreamChunk['usage']) => void;
  onError?: (error: string) => void;
}

/**
 * Return type for the useStreaming hook
 */
export interface UseStreamingReturn {
  isStreaming: boolean;
  content: string;
  context: StreamChunk['context'] | null;
  error: string | null;
  startStream: (conversationKey: string, options: StreamOptions) => void;
  stopStream: () => void;
  resetStream: () => void;
}

/**
 * Hook for streaming AI responses with real-time content updates.
 *
 * @example
 * ```tsx
 * const { isStreaming, content, startStream, stopStream } = useStreaming({
 *   onComplete: (fullContent, messageKey) => {
 *     // Handle completed message
 *   },
 * });
 *
 * // Start streaming
 * startStream(conversationKey, { content: 'Hello!' });
 *
 * // Display streaming content
 * <div>{content}</div>
 * ```
 */
export function useStreaming(options: UseStreamingOptions = {}): UseStreamingReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [content, setContent] = useState('');
  const [context, setContext] = useState<StreamChunk['context'] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const controllerRef = useRef<AbortController | null>(null);
  const contentRef = useRef('');

  const startStream = useCallback(
    (conversationKey: string, streamOptions: StreamOptions) => {
      // Stop any existing stream
      if (controllerRef.current) {
        controllerRef.current.abort();
      }

      // Reset state
      setIsStreaming(true);
      setContent('');
      setContext(null);
      setError(null);
      contentRef.current = '';

      // Start new stream
      controllerRef.current = streamMessage(conversationKey, streamOptions, {
        onChunk: (chunk) => {
          options.onChunk?.(chunk);
        },

        onContent: (newContent) => {
          contentRef.current += newContent;
          setContent(contentRef.current);
          options.onContent?.(newContent);
        },

        onContext: (ctx) => {
          if (ctx) {
            setContext(ctx);
            options.onContext?.(ctx);
          }
        },

        onComplete: (messageKey, usage) => {
          setIsStreaming(false);
          options.onComplete?.(contentRef.current, messageKey, usage);
        },

        onError: (err) => {
          setIsStreaming(false);
          setError(err);
          options.onError?.(err);
        },
      });
    },
    [options]
  );

  const stopStream = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const resetStream = useCallback(() => {
    stopStream();
    setContent('');
    setContext(null);
    setError(null);
    contentRef.current = '';
  }, [stopStream]);

  return {
    isStreaming,
    content,
    context,
    error,
    startStream,
    stopStream,
    resetStream,
  };
}
