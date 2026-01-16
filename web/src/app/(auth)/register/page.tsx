'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.auth.register({
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });

      if (response.success && response.data) {
        setUser(response.data.user, response.data.session);
        router.push('/');
      } else {
        setError(response.msg || 'Registration failed');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { msg?: string } } };
      setError(error.response?.data?.msg || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-serif text-3xl font-semibold text-cm-charcoal">
            Collective Memory
          </h1>
          <p className="text-sm text-cm-coffee mt-2">by Diptoe</p>
        </div>

        {/* Register Card */}
        <div className="bg-cm-ivory border border-cm-sand rounded-lg p-8">
          <h2 className="text-xl font-semibold text-cm-charcoal mb-6">Create an account</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-cm-charcoal mb-1">
                  First name
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta"
                  placeholder="John"
                  required
                  autoComplete="given-name"
                />
              </div>
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-cm-charcoal mb-1">
                  Last name
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta"
                  placeholder="Doe"
                  required
                  autoComplete="family-name"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-cm-charcoal mb-1">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
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
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta"
                placeholder="Minimum 8 characters"
                required
                autoComplete="new-password"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-cm-charcoal mb-1">
                Confirm password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-cm-sand rounded-md bg-cm-cream text-cm-charcoal placeholder:text-cm-coffee/50 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:border-cm-terracotta"
                placeholder="Confirm your password"
                required
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-cm-terracotta text-cm-ivory rounded-md font-medium hover:bg-cm-terracotta/90 focus:outline-none focus:ring-2 focus:ring-cm-terracotta/50 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-cm-coffee">
              Already have an account?{' '}
              <Link href="/login" className="text-cm-terracotta hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
