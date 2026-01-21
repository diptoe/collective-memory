'use client';

import Link from 'next/link';
import { cn } from '@/lib/utils';

interface ClientsNavProps {
  currentPage: 'clients' | 'models' | 'personas';
}

export function ClientsNav({ currentPage }: ClientsNavProps) {
  const tabs = [
    { id: 'clients' as const, label: 'Clients', href: '/admin/clients' },
    { id: 'models' as const, label: 'Models', href: '/admin/models' },
    { id: 'personas' as const, label: 'Personas', href: '/admin/personas' },
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
