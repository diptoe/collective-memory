'use client';

import { ChevronDown } from 'lucide-react';
import { KnowledgeDomain } from '@/types';
import { cn } from '@/lib/utils';

interface DomainSwitcherProps {
  domains: KnowledgeDomain[];
  selectedDomain: string | null;
  onDomainChange: (domainKey: string | null) => void;
  loading?: boolean;
}

export function DomainSwitcher({
  domains,
  selectedDomain,
  onDomainChange,
  loading = false,
}: DomainSwitcherProps) {
  if (domains.length === 0) {
    return null;
  }

  const selectedDomainObj = domains.find(d => d.domain_key === selectedDomain);

  return (
    <div className="relative">
      <select
        value={selectedDomain || ''}
        onChange={(e) => onDomainChange(e.target.value || null)}
        disabled={loading}
        className={cn(
          "appearance-none pl-3 pr-8 py-2 text-sm border rounded-lg cursor-pointer min-w-[160px]",
          "focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta",
          selectedDomain
            ? "bg-cm-terracotta/10 border-cm-terracotta/30 text-cm-charcoal"
            : "bg-white border-cm-sand text-cm-coffee",
          loading && "opacity-50 cursor-not-allowed"
        )}
      >
        <option value="">All Domains</option>
        {domains.map((domain) => (
          <option key={domain.domain_key} value={domain.domain_key}>
            {domain.name}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-cm-coffee/50 pointer-events-none" />
    </div>
  );
}
