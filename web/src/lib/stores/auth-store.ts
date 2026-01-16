import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Session, UserRole, UserStatus } from '@/types';

// Re-export types for convenience
export type { User, Session, UserRole, UserStatus };

interface AuthState {
  user: User | null;
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setUser: (user: User | null, session?: Session | null) => void;
  setLoading: (loading: boolean) => void;
  updateUser: (updates: Partial<User>) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      session: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user, session = null) =>
        set({
          user,
          session,
          isAuthenticated: !!user,
          isLoading: false,
        }),

      setLoading: (isLoading) => set({ isLoading }),

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      logout: () =>
        set({
          user: null,
          session: null,
          isAuthenticated: false,
          isLoading: false,
        }),
    }),
    {
      name: 'cm-auth-store',
      partialize: (state) => ({
        // Only persist user data, not loading state
        user: state.user,
      }),
    }
  )
);

/**
 * Check if user is an admin
 */
export function isAdmin(user: User | null): boolean {
  return user?.role === 'admin';
}

/**
 * Check if user is active
 */
export function isActive(user: User | null): boolean {
  return user?.status === 'active';
}
