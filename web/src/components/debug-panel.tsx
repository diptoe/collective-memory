'use client';

import { useEffect, useState } from 'react';
import { useDebugStore, getFilteredEntries, DebugEntry } from '@/lib/stores/debug-store';
import { cn } from '@/lib/utils';
import { formatDuration } from '@/lib/utils';

function StatusBadge({ status }: { status?: number }) {
  if (!status) {
    return <span className="px-2 py-0.5 text-xs rounded bg-cm-sand text-cm-coffee">Pending</span>;
  }

  const isSuccess = status >= 200 && status < 400;
  return (
    <span
      className={cn(
        'px-2 py-0.5 text-xs rounded font-mono',
        isSuccess ? 'bg-cm-success/20 text-cm-success' : 'bg-cm-error/20 text-cm-error'
      )}
    >
      {status}
    </span>
  );
}

function MethodBadge({ method }: { method: string }) {
  const colors: Record<string, string> = {
    GET: 'bg-cm-info/20 text-cm-info',
    POST: 'bg-cm-success/20 text-cm-success',
    PUT: 'bg-cm-warning/20 text-cm-warning',
    PATCH: 'bg-cm-warning/20 text-cm-warning',
    DELETE: 'bg-cm-error/20 text-cm-error',
  };

  return (
    <span className={cn('px-2 py-0.5 text-xs rounded font-mono', colors[method] || 'bg-cm-sand text-cm-coffee')}>
      {method}
    </span>
  );
}

function EntryRow({ entry, isExpanded, onToggle }: { entry: DebugEntry; isExpanded: boolean; onToggle: () => void }) {
  return (
    <div className="border-b border-cm-sand last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-3 py-2 hover:bg-cm-sand/30 transition-colors text-left"
      >
        <MethodBadge method={entry.method} />
        <span className="flex-1 text-sm text-cm-charcoal truncate font-mono">{entry.url}</span>
        <StatusBadge status={entry.status} />
        {entry.duration !== undefined && (
          <span className="text-xs text-cm-coffee font-mono">{formatDuration(entry.duration)}</span>
        )}
        <svg
          className={cn('w-4 h-4 text-cm-coffee transition-transform', isExpanded && 'rotate-180')}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="px-3 py-2 bg-cm-sand/20 text-xs font-mono">
          <div className="grid grid-cols-2 gap-4">
            {entry.requestBody !== undefined && entry.requestBody !== null && (
              <div>
                <p className="text-cm-coffee mb-1 font-sans font-medium">Request</p>
                <pre className="bg-cm-charcoal text-cm-cream p-2 rounded overflow-auto max-h-40">
                  {JSON.stringify(entry.requestBody, null, 2)}
                </pre>
              </div>
            )}
            {entry.responseBody !== undefined && entry.responseBody !== null && (
              <div>
                <p className="text-cm-coffee mb-1 font-sans font-medium">Response</p>
                <pre className="bg-cm-charcoal text-cm-cream p-2 rounded overflow-auto max-h-40">
                  {JSON.stringify(entry.responseBody, null, 2)}
                </pre>
              </div>
            )}
          </div>
          {entry.error && (
            <div className="mt-2">
              <p className="text-cm-error mb-1 font-sans font-medium">Error</p>
              <pre className="bg-cm-error/10 text-cm-error p-2 rounded">{entry.error}</pre>
            </div>
          )}
          <p className="text-cm-coffee/70 mt-2 font-sans">
            {new Date(entry.timestamp).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}

export function DebugPanel() {
  const { entries, isOpen, filter, toggleOpen, setFilter, clearEntries } = useDebugStore();
  const filteredEntries = getFilteredEntries(entries, filter);

  // Keyboard shortcut (Ctrl+Shift+D)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        toggleOpen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleOpen]);

  if (!isOpen) {
    return (
      <button
        onClick={toggleOpen}
        className="fixed bottom-4 right-4 px-3 py-2 bg-cm-charcoal text-cm-cream rounded-lg shadow-lg hover:bg-cm-coffee transition-colors text-sm font-medium z-50"
        title="Open Debug Panel (Ctrl+Shift+D)"
      >
        Debug ({entries.length})
      </button>
    );
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 h-80 bg-cm-ivory border-t-2 border-cm-terracotta shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-cm-sand bg-cm-sand/30">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold text-cm-charcoal">API Debug</h3>
          <div className="flex items-center gap-1">
            {(['all', 'success', 'error'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  'px-2 py-1 text-xs rounded transition-colors capitalize',
                  filter === f
                    ? 'bg-cm-terracotta text-cm-ivory'
                    : 'bg-cm-sand text-cm-coffee hover:bg-cm-sand/80'
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearEntries}
            className="px-2 py-1 text-xs text-cm-coffee hover:text-cm-charcoal transition-colors"
          >
            Clear
          </button>
          <button
            onClick={toggleOpen}
            className="text-cm-coffee hover:text-cm-charcoal transition-colors"
            title="Close (Ctrl+Shift+D)"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Entries list */}
      <div className="flex-1 overflow-y-auto">
        {filteredEntries.length === 0 ? (
          <div className="flex items-center justify-center h-full text-cm-coffee text-sm">
            No API requests yet
          </div>
        ) : (
          <ExpandableList entries={filteredEntries} />
        )}
      </div>
    </div>
  );
}

function ExpandableList({ entries }: { entries: DebugEntry[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <>
      {entries.map((entry) => (
        <EntryRow
          key={entry.id}
          entry={entry}
          isExpanded={expandedId === entry.id}
          onToggle={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
        />
      ))}
    </>
  );
}

