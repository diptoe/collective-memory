'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Message, Agent } from '@/types';
import { cn } from '@/lib/utils';
import { formatDateTime } from '@/lib/utils';

// Get person ID from environment
const PERSON_ID = process.env.NEXT_PUBLIC_PERSON_ID || 'unknown-user';

const MESSAGE_TYPES = ['status', 'announcement', 'request', 'task', 'message'] as const;
const PRIORITIES = ['normal', 'high', 'urgent'] as const;

const priorityColors: Record<string, string> = {
  urgent: 'bg-red-200 text-red-800',
  high: 'bg-red-100 text-red-700',
  normal: 'bg-cm-sand text-cm-coffee',
};

const typeIcons: Record<string, string> = {
  status: '#',
  announcement: '!',
  request: '?',
  task: '→',
  message: '✉',
};

interface MessageCardProps {
  message: Message;
  isHighlighted?: boolean;
  showReplyButton?: boolean;
  onReply?: () => void;
  disableLinks?: boolean; // Disable internal links when card is wrapped in a Link
}

function MessageCard({ message, isHighlighted, showReplyButton, onReply, disableLinks }: MessageCardProps) {

  const messageText = typeof message.content === 'object' && message.content !== null
    ? (message.content as { text?: string }).text || JSON.stringify(message.content)
    : String(message.content);

  return (
    <div
      className={cn(
        'p-4 rounded-lg border transition-colors',
        message.autonomous
          ? 'bg-purple-50 border-purple-500 border-l-4'
          : isHighlighted
            ? 'bg-cm-terracotta/10 border-cm-terracotta'
            : 'bg-cm-ivory border-cm-sand hover:border-cm-coffee/30'
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-mono flex-shrink-0',
          message.autonomous
            ? 'bg-purple-600 text-white'
            : 'bg-cm-charcoal text-cm-ivory'
        )}>
          {message.autonomous ? '🤖' : (typeIcons[message.message_type] || '?')}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className="font-medium text-cm-charcoal">
                {message.from_agent}
              </span>
              <span className="text-cm-coffee/50">→</span>
              <span className="text-cm-coffee">
                {message.to_agent || 'Broadcast'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {message.autonomous && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-purple-600 text-white font-medium">
                  🤖 AUTONOMOUS
                </span>
              )}
              <span
                className={cn(
                  'px-2 py-0.5 text-xs rounded-full',
                  priorityColors[message.priority]
                )}
              >
                {message.priority}
              </span>
            </div>
          </div>

          <p className="text-xs text-cm-coffee/70 mb-2">
            #{message.channel} · {formatDateTime(message.created_at)}
          </p>

          <div className="text-sm text-cm-charcoal whitespace-pre-wrap">
            {messageText}
          </div>

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-3 text-xs text-cm-coffee/70">
              <span className="capitalize">{message.message_type}</span>
              {message.reply_count !== undefined && message.reply_count > 0 && (
                disableLinks ? (
                  <span className="text-cm-terracotta">
                    {message.reply_count} {message.reply_count === 1 ? 'reply' : 'replies'}
                  </span>
                ) : (
                  <Link
                    href={`/messages/${message.message_key}`}
                    className="text-cm-terracotta hover:underline"
                  >
                    {message.reply_count} {message.reply_count === 1 ? 'reply' : 'replies'}
                  </Link>
                )
              )}
              {message.read_count !== undefined && message.read_count > 0 && (
                <span className="text-green-600 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {message.read_count} read
                </span>
              )}
            </div>
            {showReplyButton && (
              <button
                onClick={onReply}
                className="text-xs text-cm-terracotta hover:text-cm-sienna transition-colors"
              >
                Reply
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MessageDetailPage() {
  const params = useParams();
  const messageKey = params.key as string;

  const [message, setMessage] = useState<Message | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reply form state
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [replyType, setReplyType] = useState<typeof MESSAGE_TYPES[number]>('message');
  const [replyPriority, setReplyPriority] = useState<typeof PRIORITIES[number]>('normal');
  const [sending, setSending] = useState(false);
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);
  const [deleting, setDeleting] = useState(false);

  // Track if we've ensured the person entity exists
  const personEnsured = useRef(false);

  const loadMessage = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.messages.detail(messageKey);
      if (res.success && res.data) {
        setMessage(res.data as Message);
      } else {
        setError(res.msg || 'Failed to load message');
      }
    } catch (err) {
      console.error('Failed to load message:', err);
      setError('Failed to load message');
    } finally {
      setLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const res = await api.agents.list({ active_only: true });
      setActiveAgents(res.data?.agents || []);
    } catch (err) {
      console.error('Failed to load agents:', err);
    }
  };

  useEffect(() => {
    loadMessage();
    loadAgents();
  }, [messageKey]);

  const handleDeleteThread = async () => {
    if (!message) return;

    const replyCount = message.reply_count || message.replies?.length || 0;
    const confirmMsg = replyCount > 0
      ? `Are you sure you want to delete this message and its ${replyCount} replies? This cannot be undone.`
      : 'Are you sure you want to delete this message? This cannot be undone.';

    if (!confirm(confirmMsg)) return;

    setDeleting(true);
    try {
      await api.messages.deleteThread(message.message_key);
      // Navigate back to messages list after deletion
      window.location.href = '/messages';
    } catch (err) {
      console.error('Failed to delete thread:', err);
      alert('Failed to delete thread');
      setDeleting(false);
    }
  };

  // Ensure person entity exists in the knowledge graph
  const ensurePersonEntity = async () => {
    if (personEnsured.current || PERSON_ID === 'unknown-user') return;

    try {
      const res = await api.entities.get(PERSON_ID);
      if (res.data?.entity?.entity_key) {
        personEnsured.current = true;
        return;
      }
    } catch {
      try {
        const name = PERSON_ID.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        await api.entities.create({
          entity_key: PERSON_ID,
          entity_type: 'Person',
          name,
          properties: { source: 'web-ui' },
        });
        personEnsured.current = true;
      } catch (createErr) {
        console.error('Failed to create person entity:', createErr);
      }
    }
  };

  const handleSendReply = async () => {
    if (!replyContent.trim() || !message) return;

    setSending(true);
    try {
      await ensurePersonEntity();

      await api.messages.post({
        channel: message.channel,
        from_agent: `human:${PERSON_ID}`,
        to_agent: message.from_agent.startsWith('human:') ? undefined : message.from_agent,
        reply_to_key: message.message_key,
        message_type: replyType,
        content: { text: replyContent },
        priority: replyPriority,
      });

      setShowReplyForm(false);
      setReplyContent('');
      loadMessage(); // Refresh to show new reply
    } catch (err) {
      console.error('Failed to send reply:', err);
      alert('Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <p className="text-cm-coffee">Loading message...</p>
        </div>
      </div>
    );
  }

  if (error || !message) {
    return (
      <div className="p-6">
        <div className="flex flex-col items-center justify-center py-12 gap-4">
          <p className="text-cm-coffee">{error || 'Message not found'}</p>
          <Link
            href="/messages"
            className="text-cm-terracotta hover:text-cm-sienna transition-colors"
          >
            ← Back to messages
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/messages"
          className="text-cm-coffee hover:text-cm-charcoal transition-colors text-sm flex items-center gap-1 mb-4"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to messages
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-serif text-2xl font-semibold text-cm-charcoal">
              Message Thread
            </h1>
            <p className="text-cm-coffee mt-1">
              #{message.channel} · {formatDateTime(message.created_at)}
            </p>
          </div>
          <button
            onClick={handleDeleteThread}
            disabled={deleting}
            className="px-3 py-1.5 text-sm bg-cm-error/10 text-cm-error rounded-lg hover:bg-cm-error/20 transition-colors disabled:opacity-50"
          >
            {deleting ? 'Deleting...' : 'Delete Thread'}
          </button>
        </div>
      </div>

      {/* Parent message (if this is a reply) */}
      {message.parent && (
        <div className="mb-4">
          <h2 className="text-sm font-medium text-cm-coffee mb-2 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            In reply to
          </h2>
          <Link href={`/messages/${message.parent.message_key}`}>
            <MessageCard message={message.parent} disableLinks />
          </Link>
        </div>
      )}

      {/* Main message */}
      <div className="mb-6">
        {message.parent && (
          <h2 className="text-sm font-medium text-cm-coffee mb-2">This message</h2>
        )}
        <MessageCard
          message={message}
          isHighlighted={true}
          showReplyButton={true}
          onReply={() => setShowReplyForm(true)}
        />
      </div>

      {/* Reply form */}
      {showReplyForm && (
        <div className="mb-6 p-4 bg-cm-sand/30 rounded-lg border border-cm-sand">
          <h3 className="font-medium text-cm-charcoal mb-3">Reply to this message</h3>

          <div className="space-y-4">
            {/* Type and Priority */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Type
                </label>
                <select
                  value={replyType}
                  onChange={(e) => setReplyType(e.target.value as typeof MESSAGE_TYPES[number])}
                  className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta bg-cm-ivory"
                >
                  {MESSAGE_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-cm-charcoal mb-1">
                  Priority
                </label>
                <select
                  value={replyPriority}
                  onChange={(e) => setReplyPriority(e.target.value as typeof PRIORITIES[number])}
                  className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta bg-cm-ivory"
                >
                  {PRIORITIES.map((priority) => (
                    <option key={priority} value={priority}>
                      {priority.charAt(0).toUpperCase() + priority.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Reply Content */}
            <div>
              <label className="block text-sm font-medium text-cm-charcoal mb-1">
                Message
              </label>
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="Enter your reply..."
                rows={3}
                className="w-full px-3 py-2 border border-cm-sand rounded-lg focus:outline-none focus:ring-2 focus:ring-cm-terracotta/20 focus:border-cm-terracotta resize-none bg-cm-ivory"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowReplyForm(false)}
                className="px-4 py-2 text-cm-coffee hover:text-cm-charcoal transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSendReply}
                disabled={sending || !replyContent.trim()}
                className="px-4 py-2 bg-cm-terracotta text-cm-ivory rounded-lg hover:bg-cm-sienna transition-colors disabled:opacity-50"
              >
                {sending ? 'Sending...' : 'Send Reply'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Replies */}
      {message.replies && message.replies.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-cm-coffee mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            {message.replies.length} {message.replies.length === 1 ? 'Reply' : 'Replies'}
          </h2>
          <div className="space-y-3 pl-4 border-l-2 border-cm-sand">
            {message.replies.map((reply) => (
              <Link key={reply.message_key} href={`/messages/${reply.message_key}`}>
                <MessageCard message={reply} disableLinks />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Read by section */}
      {message.readers && message.readers.length > 0 && (
        <div className="mt-8 pt-6 border-t border-cm-sand">
          <h3 className="text-sm font-medium text-cm-coffee mb-3">
            Read by {message.read_count || message.readers.length} agent{(message.read_count || message.readers.length) !== 1 ? 's' : ''}
          </h3>
          <div className="flex flex-wrap gap-2">
            {message.readers.map((reader) => (
              <div
                key={reader.agent_id}
                className="px-3 py-1.5 bg-cm-sand/50 rounded-lg text-sm flex items-center gap-2"
              >
                <span className="text-cm-charcoal">{reader.agent_id}</span>
                {reader.read_at && (
                  <span className="text-cm-coffee/70 text-xs">
                    {formatDateTime(reader.read_at)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
