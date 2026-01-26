'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function LoginPage() {
  const router = useRouter();
  const { setUser, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  // Check if user has a valid session and redirect if so
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await api.auth.me();
        if (response.success && response.data?.user) {
          // User has valid session, update store and redirect
          setUser(response.data.user, response.data.session);
          router.replace('/');
          return;
        }
      } catch {
        // No valid session, show login form
      }
      setIsCheckingSession(false);
    };

    checkSession();
  }, [setUser, router]);

  // If already authenticated (from store), redirect immediately
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace('/');
    }
  }, [authLoading, isAuthenticated, router]);

  // Show loading while checking session
  if (isCheckingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cm-cream">
        <div className="text-cm-coffee">Checking session...</div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await api.auth.login(email, password, rememberMe);
      if (response.success && response.data) {
        setUser(response.data.user, response.data.session);
        router.push('/');
      } else {
        setError(response.msg || 'Login failed');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setError('');
    setIsLoading(true);
    try {
      const response = await api.auth.guestLogin();
      if (response.success && response.data) {
        setUser(response.data.user, response.data.session);
        router.push('/');
      } else {
        setError(response.msg || 'Guest login failed');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Guest login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Image
            src="/cm-logo.svg"
            alt="Collective Memory"
            width={64}
            height={64}
            className="mx-auto mb-4"
          />
          <h1 className="font-serif text-3xl font-semibold text-cm-charcoal">
            Collective Memory
          </h1>
        </div>

        {/* Login Card */}
        <div className="bg-cm-ivory border border-cm-sand rounded-lg p-8">
          <h2 className="text-xl font-semibold text-cm-charcoal mb-6">Sign in</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-cm-charcoal mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta"
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-cm-charcoal mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta"
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 border border-cm-sand rounded bg-cm-cream text-cm-terracotta focus:ring-cm-terracotta/50"
                />
                <span className="text-sm text-cm-coffee">Remember me</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-cm-terracotta text-cm-ivory rounded-md font-medium hover:bg-cm-terracotta/90 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          {/* Guest Access Section */}
          <div className="mt-6 pt-6 border-t border-cm-sand">
            <button
              type="button"
              onClick={handleGuestLogin}
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-cm-sand text-cm-charcoal rounded-md font-medium hover:bg-cm-sand/80 focus:outline-none focus:ring-2 focus:ring-cm-sand/50 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Loading...' : 'Access as Guest'}
            </button>
            <p className="mt-2 text-xs text-cm-coffee text-center">
              View-only access to explore the platform
            </p>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-cm-coffee">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="text-cm-terracotta hover:underline font-medium">
                Create one
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
