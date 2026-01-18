'use client';

import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ClientLayout } from '@/components/client-layout';
import { useAuthStore } from '@/lib/stores/auth-store';
import { api } from '@/lib/api';

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isLoading, setUser, logout } = useAuthStore();
  const initRef = useRef(false);

  // Initialize auth state by checking session with server
  useEffect(() => {
    // Only run once
    if (initRef.current) return;
    initRef.current = true;

    const initAuth = async () => {
      try {
        const response = await api.auth.me();
        if (response.success && response.data?.user) {
          setUser(response.data.user, response.data.session);
        } else {
          // No valid session
          setUser(null);
        }
      } catch {
        // Session check failed (e.g., no cookie, expired)
        setUser(null);
      }
    };

    initAuth();
  }, [setUser]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cm-cream">
        <div className="text-cm-coffee">Loading...</div>
      </div>
    );
  }

  // Don't render if not authenticated (redirect in progress)
  if (!isAuthenticated) {
    return null;
  }

  const handleLogout = async () => {
    try {
      await api.auth.logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    logout();
    router.push('/login');
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar Navigation */}
      <nav className="w-64 bg-cm-ivory border-r border-cm-sand flex flex-col h-screen sticky top-0">
        <div className="p-4 border-b border-cm-sand">
          <Link href="/" className="flex items-center gap-3 group">
            <img
              src="/cm-logo.svg"
              alt="Collective Memory"
              className="w-10 h-10 transition-transform group-hover:scale-105"
            />
            <div className="leading-tight">
              <span className="block font-serif text-base font-semibold text-cm-charcoal">Collective</span>
              <span className="block font-serif text-base font-semibold text-cm-charcoal">Memory</span>
            </div>
          </Link>
        </div>

        <div className="flex-1 py-4 overflow-y-auto">
          <NavLink href="/" icon="home" active={pathname === '/'}>Activity</NavLink>
          <NavLink href="/chat" icon="message-circle" active={pathname.startsWith('/chat')}>Chat</NavLink>
          <NavLink href="/personas" icon="users" active={pathname.startsWith('/personas')}>Personas</NavLink>
          <NavLink href="/models" icon="brain" active={pathname.startsWith('/models')}>Models</NavLink>
          <NavLink href="/entities" icon="database" active={pathname.startsWith('/entities')}>Entities</NavLink>
          <NavLink href="/graph" icon="git-branch" active={pathname === '/graph'}>Graph</NavLink>
          <NavLink href="/messages" icon="inbox" active={pathname.startsWith('/messages')}>Messages</NavLink>
          <NavLink href="/agents" icon="cpu" active={pathname.startsWith('/agents')}>Agents</NavLink>

          {/* Admin section */}
          {(user?.role === 'admin' || user?.role === 'domain_admin') && (
            <>
              <div className="px-6 py-2 mt-4">
                <p className="text-xs font-semibold text-cm-coffee uppercase tracking-wider">Admin</p>
              </div>
              <NavLink href="/admin/teams" icon="team" active={pathname.startsWith('/admin/teams')}>Teams</NavLink>
              {user?.role === 'admin' && (
                <>
                  <NavLink href="/admin/users" icon="shield" active={pathname.startsWith('/admin/users')}>Users</NavLink>
                  <NavLink href="/admin/domains" icon="globe" active={pathname.startsWith('/admin/domains')}>Domains</NavLink>
                  <NavLink href="/admin/sessions" icon="key" active={pathname.startsWith('/admin/sessions')}>Sessions</NavLink>
                </>
              )}
            </>
          )}
        </div>

        <div className="p-4 border-t border-cm-sand">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-cm-terracotta flex items-center justify-center text-cm-ivory text-sm font-medium">
                {user.initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-cm-charcoal truncate">{user.display_name}</p>
                <p className="text-xs text-cm-coffee capitalize">{user.role}</p>
              </div>
              <div className="flex gap-1">
                <Link
                  href="/settings"
                  className="p-1.5 text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand/50 rounded transition-colors"
                  title="Settings"
                >
                  <SettingsIcon />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-1.5 text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand/50 rounded transition-colors"
                  title="Logout"
                >
                  <LogoutIcon />
                </button>
              </div>
            </div>
          ) : (
            <Link
              href="/login"
              className="block text-center py-2 px-4 bg-cm-terracotta text-cm-ivory rounded-md text-sm font-medium hover:bg-cm-terracotta/90 transition-colors"
            >
              Sign in
            </Link>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <ClientLayout>{children}</ClientLayout>
      </main>
    </div>
  );
}

function NavLink({
  href,
  icon,
  active,
  children,
}: {
  href: string;
  icon: string;
  active?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 px-6 py-2.5 transition-colors ${
        active
          ? 'text-cm-charcoal bg-cm-sand/50'
          : 'text-cm-coffee hover:text-cm-charcoal hover:bg-cm-sand/50'
      }`}
    >
      <NavIcon name={icon} />
      <span className="text-sm font-medium">{children}</span>
    </Link>
  );
}

function NavIcon({ name }: { name: string }) {
  const icons: Record<string, string> = {
    'home': '🏠',
    'message-circle': '💬',
    'users': '👥',
    'brain': '🧠',
    'database': '🗄️',
    'file-text': '📄',
    'layers': '📊',
    'git-branch': '🔀',
    'inbox': '📥',
    'cpu': '⚙️',
    'shield': '🛡️',
    'globe': '🌐',
    'key': '🔑',
    'settings': '⚙️',
    'team': '👨‍👩‍👧‍👦',
  };
  return <span className="w-5 text-center">{icons[name] || '•'}</span>;
}

function SettingsIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  );
}
