'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Message, Agent, Entity } from '@/types';
import { cn } from '@/lib/utils';
import { TYPE_COLORS } from '@/lib/graph/layout';
import { formatDateTime } from '@/lib/utils';
import { Markdown } from '@/components/markdown/markdown';
import { useAuthStore } from '@/lib/stores/auth-store';

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

const typeColors: Record<string, string> = {
  status: 'bg-blue-100 text-blue-700',
  announcement: 'bg-yellow-100 text-yellow-800',
  request: 'bg-purple-100 text-purple-700',
  task: 'bg-green-100 text-green-700',
  message: 'bg-cm-sand text-cm-coffee',
  acknowledged: 'bg-cyan-100 text-cyan-700',
  waiting: 'bg-orange-100 text-orange-700',
  resumed: 'bg-emerald-100 text-emerald-700',
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
                {message.from_name || message.from_key}
              </span>
              <span className="text-cm-coffee/50">→</span>
              <span className="text-cm-coffee">
                {message.to_name || message.to_key || 'Broadcast'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {message.confirmed && (
                <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700 font-medium flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  CONFIRMED
                </span>
              )}
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

          <p className="text-xs text-cm-coffee/70 mb-2 flex items-center gap-2">
            <span>#{message.channel}</span>
            {message.team_key ? (
              <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 flex items-center gap-1">
                <span>👥</span> {message.team_name || 'Team'}
              </span>
            ) : (
              <span className="px-1.5 py-0.5 rounded bg-cm-sand/50 text-cm-coffee flex items-center gap-1">
                <span>🌐</span> Domain
              </span>
            )}
            <span>·</span>
            <span>{formatDateTime(message.created_at)}</span>
          </p>

          <Markdown content={messageText} />

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-3 text-xs text-cm-coffee/70">
              <span className={cn(
                'px-2 py-0.5 rounded-full capitalize',
                typeColors[message.message_type] || 'bg-cm-sand text-cm-coffee'
              )}>
                {message.message_type}
              </span>
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
  const { user } = useAuthStore();

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
  const [confirming, setConfirming] = useState(false);


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

  const handleConfirm = async () => {
    if (!message) return;
    if (!user?.user_key) {
      alert('You must be logged in to confirm tasks');
      return;
    }

    setConfirming(true);
    try {
      await api.messages.confirm(message.message_key, user.user_key);
      loadMessage(); // Refresh to show confirmation status
    } catch (err) {
      console.error('Failed to confirm message:', err);
      alert('Failed to confirm task completion');
    } finally {
      setConfirming(false);
    }
  };

  const handleUnconfirm = async () => {
    if (!message) return;

    if (!confirm('Remove confirmation? This indicates more work may be needed.')) return;

    setConfirming(true);
    try {
      await api.messages.unconfirm(message.message_key);
      loadMessage(); // Refresh to show confirmation status
    } catch (err) {
      console.error('Failed to remove confirmation:', err);
      alert('Failed to remove confirmation');
    } finally {
      setConfirming(false);
    }
  };

  const handleSendReply = async () => {
    if (!replyContent.trim() || !message) return;
    if (!user?.user_key) {
      alert('You must be logged in to send replies');
      return;
    }

    setSending(true);
    try {
      // Determine if we should reply directly to the sender
      // If original sender is the current user, broadcast instead of replying to self
      // Otherwise reply directly to sender (API will auto-detect the correct scope)
      const isSelfMessage = message.from_key === user.user_key;
      const toKey = isSelfMessage ? undefined : message.from_key;

      await api.messages.post({
        channel: message.channel,
        from_key: user.user_key,  // Use authenticated user's key
        to_key: toKey,
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
            <p className="text-cm-coffee mt-1 flex items-center gap-2">
              <span>#{message.channel}</span>
              {message.team_key ? (
                <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 text-xs flex items-center gap-1">
                  <span>👥</span> {message.team_name || 'Team'}
                </span>
              ) : (
                <span className="px-1.5 py-0.5 rounded bg-cm-sand/50 text-cm-coffee text-xs flex items-center gap-1">
                  <span>🌐</span> Domain
                </span>
              )}
              <span>·</span>
              <span>{formatDateTime(message.created_at)}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Confirmation status and buttons */}
            {message.confirmed ? (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Confirmed by {message.confirmed_by}
                </span>
                <button
                  onClick={handleUnconfirm}
                  disabled={confirming}
                  className="px-3 py-1.5 text-sm text-cm-coffee hover:text-cm-charcoal transition-colors disabled:opacity-50"
                  title="Remove confirmation if more work is needed"
                >
                  {confirming ? '...' : 'Undo'}
                </button>
              </div>
            ) : (
              <button
                onClick={handleConfirm}
                disabled={confirming}
                className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50 flex items-center gap-1"
                title="Confirm that this task/message has been satisfactorily completed"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {confirming ? 'Confirming...' : 'Confirm'}
              </button>
            )}
            <button
              onClick={handleDeleteThread}
              disabled={deleting}
              className="px-3 py-1.5 text-sm bg-cm-error/10 text-cm-error rounded-lg hover:bg-cm-error/20 transition-colors disabled:opacity-50"
            >
              {deleting ? 'Deleting...' : 'Delete Thread'}
            </button>
          </div>
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
            {message.readers.map((reader, index) => (
              <div
                key={`${reader.agent_id}-${index}`}
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

      {/* Linked Entities section */}
      {message.linked_entities && message.linked_entities.length > 0 && (
        <div className="mt-8 pt-6 border-t border-cm-sand">
          <h3 className="text-sm font-medium text-cm-coffee mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Linked Entities ({message.linked_entities.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {message.linked_entities.map((entity) => (
              <Link
                key={entity.entity_key}
                href={`/entities/${entity.entity_type.toLowerCase()}/${entity.entity_key}`}
                className="px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors hover:opacity-80"
                style={{
                  backgroundColor: `${TYPE_COLORS[entity.entity_type] || '#666'}20`,
                  borderLeft: `3px solid ${TYPE_COLORS[entity.entity_type] || '#666'}`,
                }}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: TYPE_COLORS[entity.entity_type] || '#666' }}
                />
                <span className="text-cm-charcoal font-medium">{entity.name}</span>
                <span className="text-cm-coffee/70 text-xs">{entity.entity_type}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
