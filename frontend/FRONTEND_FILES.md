# Frontend Files to Create

Due to bash escaping complexity with JSX/TSX files, here are the key files you need to create manually.

## 1. app/page.tsx (Landing Page)

Create a landing page with:
- Hero section with "Medical Coding Lookup API" headline
- Features section (6 feature cards)
- Pricing section (4 pricing tiers: Free, Developer, Growth, Enterprise)
- CTA buttons linking to /signup
- Simple header with navigation to /login and /signup

## 2. app/login/page.tsx

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h2 className="text-3xl font-bold text-center">Sign in to Nuvii API</h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 text-red-500 p-3 rounded">{error}</div>
          )}
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
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>

          <p className="text-center text-sm">
            Don't have an account?{' '}
            <Link href="/signup" className="text-blue-600 hover:underline">
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
```

## 3. app/signup/page.tsx

```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

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
        <div>
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
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Sign up'}
          </button>

          <p className="text-center text-sm">
            Already have an account?{' '}
            <Link href="/login" className="text-blue-600 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
```

## 4. app/dashboard/layout.tsx

```typescript
'use client';

import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Link from 'next/link';
import { LayoutDashboard, Key, FileText, CreditCard, LogOut } from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Nav */}
      <header className="bg-white border-b">
        <div className="px-4 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold text-blue-600">Nuvii API</div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user.email}</span>
            <button onClick={logout} className="text-sm text-red-600 hover:underline flex items-center gap-1">
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r min-h-screen">
          <nav className="p-4 space-y-2">
            <NavLink href="/dashboard" icon={<LayoutDashboard className="w-5 h-5" />}>
              Dashboard
            </NavLink>
            <NavLink href="/dashboard/api-keys" icon={<Key className="w-5 h-5" />}>
              API Keys
            </NavLink>
            <NavLink href="/dashboard/docs" icon={<FileText className="w-5 h-5" />}>
              Documentation
            </NavLink>
            <NavLink href="/dashboard/billing" icon={<CreditCard className="w-5 h-5" />}>
              Billing
            </NavLink>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

function NavLink({ href, icon, children }: { href: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-4 py-2 rounded-md hover:bg-gray-100 text-gray-700 hover:text-blue-600"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
```

## 5. app/dashboard/page.tsx (Usage Stats)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { usageAPI } from '@/lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, logsRes] = await Promise.all([
        usageAPI.getStats(),
        usageAPI.getLogs(10)
      ]);
      setStats(statsRes.data);
      setLogs(logsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Total Requests" value={stats?.total_requests || 0} />
        <StatCard title="This Month" value={stats?.requests_this_month || 0} />
        <StatCard title="Monthly Limit" value={stats?.monthly_limit || 0} />
        <StatCard title="Usage" value={`${stats?.percentage_used || 0}%`} />
      </div>

      {/* Recent Logs */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Recent API Calls</h2>
        <div className="space-y-2">
          {logs.map((log) => (
            <div key={log.id} className="flex justify-between items-center p-3 border-b">
              <span className="font-mono text-sm">{log.method} {log.endpoint}</span>
              <span className="text-sm text-gray-600">{new Date(log.created_at).toLocaleString()}</span>
              <span className={`px-2 py-1 rounded text-sm ${
                log.status_code < 300 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {log.status_code}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <p className="text-3xl font-bold mt-2">{value}</p>
    </div>
  );
}
```

## 6. app/dashboard/api-keys/page.tsx

```typescript
'use client';

import { useEffect, useState } from 'react';
import { apiKeysAPI } from '@/lib/api';
import { Copy, Trash2 } from 'lucide-react';

export default function APIKeysPage() {
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      const response = await apiKeysAPI.list();
      setApiKeys(response.data);
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    }
  };

  const createKey = async () => {
    setLoading(true);
    try {
      const response = await apiKeysAPI.create(newKeyName || 'Unnamed Key');
      setNewKey(response.data.api_key);
      setNewKeyName('');
      await fetchKeys();
    } catch (error) {
      console.error('Failed to create API key:', error);
    } finally {
      setLoading(false);
    }
  };

  const revokeKey = async (id: string) => {
    if (confirm('Are you sure you want to revoke this API key?')) {
      try {
        await apiKeysAPI.revoke(id);
        await fetchKeys();
      } catch (error) {
        console.error('Failed to revoke API key:', error);
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">API Keys</h1>

      {/* Create New Key */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Create New API Key</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="API Key Name (optional)"
            className="flex-1 px-3 py-2 border rounded-md"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
          />
          <button
            onClick={createKey}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Key'}
          </button>
        </div>

        {newKey && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm font-medium text-green-800 mb-2">
              New API Key Created! Copy it now - you won't see it again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 p-2 bg-white border rounded text-sm font-mono">
                {newKey}
              </code>
              <button
                onClick={() => copyToClipboard(newKey)}
                className="p-2 hover:bg-green-100 rounded"
              >
                <Copy className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* API Keys List */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Your API Keys</h2>
        <div className="space-y-2">
          {apiKeys.map((key) => (
            <div key={key.id} className="flex justify-between items-center p-4 border rounded-md">
              <div>
                <p className="font-mono font-semibold">{key.key_prefix}...</p>
                <p className="text-sm text-gray-600">{key.name || 'Unnamed'}</p>
                <p className="text-xs text-gray-500">
                  Created: {new Date(key.created_at).toLocaleDateString()}
                  {key.last_used_at && ` • Last used: ${new Date(key.last_used_at).toLocaleDateString()}`}
                </p>
              </div>
              <button
                onClick={() => revokeKey(key.id)}
                className="p-2 text-red-600 hover:bg-red-50 rounded"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

## Quick Start

1. Copy these files into your frontend directory
2. Run `npm install`
3. Create `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
4. Run `npm run dev`
5. Visit http://localhost:3000

The authentication and API client are already set up in `lib/` directory!

