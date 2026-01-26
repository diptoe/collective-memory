'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/stores/auth-store';

export function GuestBanner() {
  const { user } = useAuthStore();

  if (user?.role !== 'guest') return null;

  return (
    <div className="bg-cm-amber/20 border-b border-cm-amber/30 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <p className="text-sm text-cm-coffee">
          <span className="font-medium">Guest Mode:</span> You have view-only access
        </p>
        <Link href="/register" className="text-sm font-medium text-cm-terracotta hover:underline">
          Create account for full access
        </Link>
      </div>
    </div>
  );
}
