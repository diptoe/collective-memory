'use client';

import Link from 'next/link';
import { cn } from '@/lib/utils';

interface KnowledgeNavProps {
  currentPage: 'overview' | 'entities' | 'graph';
}

export function KnowledgeNav({ currentPage }: KnowledgeNavProps) {
  const tabs = [
    { id: 'overview' as const, label: 'Overview', href: '/knowledge' },
    { id: 'entities' as const, label: 'Entities', href: '/entities' },
    { id: 'graph' as const, label: 'Graph', href: '/graph' },
  ];

  return (
    <div className="flex items-center gap-1 bg-cm-sand/50 rounded-lg p-1">
      {tabs.map((tab) => (
        <Link
          key={tab.id}
          href={tab.href}
          className={cn(
            "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
            currentPage === tab.id
              ? "bg-white text-cm-charcoal shadow-sm"
              : "text-cm-coffee hover:text-cm-charcoal hover:bg-white/50"
          )}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}
