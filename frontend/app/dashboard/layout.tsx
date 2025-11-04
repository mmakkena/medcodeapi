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