import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface DebugEntry {
  id: string;
  method: string;
  url: string;
  requestBody?: unknown;
  responseBody?: unknown;
  status?: number;
  duration?: number;
  timestamp: Date;
  error?: string;
}

interface DebugState {
  entries: DebugEntry[];
  isOpen: boolean;
  filter: 'all' | 'success' | 'error';
  maxEntries: number;

  // Actions
  addEntry: (entry: DebugEntry) => void;
  clearEntries: () => void;
  toggleOpen: () => void;
  setOpen: (open: boolean) => void;
  setFilter: (filter: 'all' | 'success' | 'error') => void;
}

export const useDebugStore = create<DebugState>()(
  persist(
    (set, get) => ({
      entries: [],
      isOpen: false,
      filter: 'all',
      maxEntries: 100,

      addEntry: (entry) => {
        set((state) => {
          const newEntries = [entry, ...state.entries];
          // Keep only the last maxEntries
          return {
            entries: newEntries.slice(0, state.maxEntries),
          };
        });
      },

      clearEntries: () => {
        set({ entries: [] });
      },

      toggleOpen: () => {
        set((state) => ({ isOpen: !state.isOpen }));
      },

      setOpen: (open) => {
        set({ isOpen: open });
      },

      setFilter: (filter) => {
        set({ filter });
      },
    }),
    {
      name: 'cm-debug-store',
      partialize: (state) => ({
        isOpen: state.isOpen,
        filter: state.filter,
        // Don't persist entries
      }),
    }
  )
);

/**
 * Get filtered entries based on current filter
 */
export function getFilteredEntries(entries: DebugEntry[], filter: 'all' | 'success' | 'error'): DebugEntry[] {
  switch (filter) {
    case 'success':
      return entries.filter((e) => e.status && e.status >= 200 && e.status < 400);
    case 'error':
      return entries.filter((e) => !e.status || e.status >= 400 || e.error);
    default:
      return entries;
  }
}
