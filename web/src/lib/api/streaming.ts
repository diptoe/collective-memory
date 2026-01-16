/**
 * Collective Memory Platform - Streaming Utilities
 *
 * SSE streaming utilities for real-time AI responses.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001/api';

/**
 * Chunk received from SSE stream
 */
export interface StreamChunk {
  type: 'content' | 'context' | 'done' | 'error';
  content?: string;
  done?: boolean;
  message_key?: string;
  context?: {
    entity_count: number;
    relationship_count: number;
    token_count: number;
    truncated: boolean;
    cache_hit: boolean;
  };
  usage?: {
    input_tokens: number;
    output_tokens: number;
  };
}

/**
 * Options for streaming request
 */
export interface StreamOptions {
  content: string;
  max_tokens?: number;
  temperature?: number;
}

/**
 * Callbacks for stream events
 */
export interface StreamCallbacks {
  onChunk?: (chunk: StreamChunk) => void;
  onContent?: (content: string) => void;
  onContext?: (context: StreamChunk['context']) => void;
  onComplete?: (messageKey: string, usage?: StreamChunk['usage']) => void;
  onError?: (error: string) => void;
}

/**
 * Stream a message to a conversation and receive AI response.
 *
 * @param conversationKey - The conversation to send message to
 * @param options - Message options
 * @param callbacks - Event callbacks
 * @returns AbortController to cancel the stream
 */
export function streamMessage(
  conversationKey: string,
  options: StreamOptions,
  callbacks: StreamCallbacks
): AbortController {
  const controller = new AbortController();

  const url = `${API_BASE_URL}/conversations/${conversationKey}/messages/stream`;

  // Start streaming
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(options),
    signal: controller.signal,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }
      const reader = response.body.getReader();

      const decoder = new TextDecoder();
      let buffer = '';

      function processLine(line: string) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const chunk: StreamChunk = JSON.parse(data);

            callbacks.onChunk?.(chunk);

            switch (chunk.type) {
              case 'content':
                if (chunk.content) {
                  callbacks.onContent?.(chunk.content);
                }
                break;

              case 'context':
                if (chunk.context) {
                  callbacks.onContext?.(chunk.context);
                }
                break;

              case 'done':
                if (chunk.message_key) {
                  callbacks.onComplete?.(chunk.message_key, chunk.usage);
                }
                break;

              case 'error':
                callbacks.onError?.(chunk.content || 'Unknown error');
                break;
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }

      function read(): Promise<void> {
        return reader.read().then(({ done, value }) => {
          if (done) {
            // Process any remaining buffer
            if (buffer.trim()) {
              buffer.split('\n').forEach(processLine);
            }
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          lines.forEach(processLine);

          return read();
        });
      }

      return read();
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        callbacks.onError?.(error.message);
      }
    });

  return controller;
}

/**
 * Helper to create a streaming message with accumulated content.
 */
export function createStreamingMessage(
  conversationKey: string,
  options: StreamOptions
): Promise<{
  content: string;
  messageKey: string;
  context?: StreamChunk['context'];
  usage?: StreamChunk['usage'];
}> {
  return new Promise((resolve, reject) => {
    let content = '';
    let context: StreamChunk['context'] | undefined;

    streamMessage(conversationKey, options, {
      onContent: (chunk) => {
        content += chunk;
      },
      onContext: (ctx) => {
        context = ctx;
      },
      onComplete: (messageKey, usage) => {
        resolve({ content, messageKey, context, usage });
      },
      onError: (error) => {
        reject(new Error(error));
      },
    });
  });
}
