'use client';

import { useAuthStore } from '@/lib/stores/auth-store';

/**
 * Hook to check if the current user has write access.
 * Returns false for guest users (view-only access).
 */
export function useCanWrite(): boolean {
  const { user } = useAuthStore();
  return user !== null && user.role !== 'guest';
}
