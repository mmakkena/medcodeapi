'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signup(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div className="flex flex-col items-center">
          <Image
            src="/nuvii_logo.png"
            alt="Nuvii AI"
            width={450}
            height={120}
            className="h-30 w-auto mb-4"
          />
          <h2 className="text-3xl font-bold text-center">Create your account</h2>
          <p className="mt-2 text-center text-gray-600">
            Start using the Nuvii API
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">
                Must be at least 8 characters
              </p>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Creating account...' : 'Sign up'}
          </button>

          <p className="text-center text-sm">
            Already have an account?{' '}
            <Link href="/login" className="text-nuvii-blue hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}