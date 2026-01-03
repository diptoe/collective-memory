'use client';

import { DebugPanel } from './debug-panel';

export function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <DebugPanel />
    </>
  );
}
