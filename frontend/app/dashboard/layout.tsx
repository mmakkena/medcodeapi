'use client';

import { useAuth } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import {
  LayoutDashboard,
  Key,
  FileText,
  CreditCard,
  LogOut,
  Sparkles,
  Mail,
  Shield,
  DollarSign,
  FileSearch,
  TrendingUp,
  ClipboardCheck,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useState } from 'react';
import { usePathname } from 'next/navigation';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    cdi: pathname.startsWith('/dashboard/cdi'),
    revenue: pathname.startsWith('/dashboard/revenue'),
    quality: pathname.startsWith('/dashboard/quality')
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

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
          <Link href="/dashboard">
            <Image
              src="/nuvii_logo.png"
              alt="Nuvii.ai Dashboard - Medical Coding API Management"
              width={360}
              height={96}
              className="h-24 w-auto"
            />
          </Link>
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
          <nav className="p-4 space-y-1">
            <NavLink href="/dashboard" icon={<LayoutDashboard className="w-5 h-5" />}>
              Dashboard
            </NavLink>
            <NavLink href="/dashboard/api-keys" icon={<Key className="w-5 h-5" />}>
              API Keys
            </NavLink>
            <NavLink href="/dashboard/playground" icon={<Sparkles className="w-5 h-5" />}>
              MedCode Playground
            </NavLink>
            <NavLink href="/dashboard/fee-schedule" icon={<DollarSign className="w-5 h-5" />}>
              Fee Schedule Analyzer
            </NavLink>

            {/* CDI Section */}
            <div className="pt-2">
              <button
                onClick={() => toggleSection('cdi')}
                className="w-full flex items-center justify-between px-4 py-2 rounded-md hover:bg-gray-100 text-gray-700"
              >
                <span className="flex items-center gap-3">
                  <FileSearch className="w-5 h-5" />
                  <span>CDI Analysis</span>
                </span>
                {expandedSections.cdi ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
              {expandedSections.cdi && (
                <div className="ml-4 mt-1 space-y-1">
                  <SubNavLink href="/dashboard/cdi">Overview</SubNavLink>
                  <SubNavLink href="/dashboard/cdi/analyze">Note Analysis</SubNavLink>
                  <SubNavLink href="/dashboard/cdi/query-generator">Query Generator</SubNavLink>
                  <SubNavLink href="/dashboard/cdi/history">History</SubNavLink>
                  <SubNavLink href="/dashboard/cdi/guidelines">Guidelines</SubNavLink>
                </div>
              )}
            </div>

            {/* Revenue Section */}
            <div>
              <button
                onClick={() => toggleSection('revenue')}
                className="w-full flex items-center justify-between px-4 py-2 rounded-md hover:bg-gray-100 text-gray-700"
              >
                <span className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5" />
                  <span>Revenue</span>
                </span>
                {expandedSections.revenue ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
              {expandedSections.revenue && (
                <div className="ml-4 mt-1 space-y-1">
                  <SubNavLink href="/dashboard/revenue">Overview</SubNavLink>
                  <SubNavLink href="/dashboard/revenue/analyze">Revenue Analysis</SubNavLink>
                  <SubNavLink href="/dashboard/revenue/em-coding">E/M Coding</SubNavLink>
                  <SubNavLink href="/dashboard/revenue/hcc">HCC Analysis</SubNavLink>
                  <SubNavLink href="/dashboard/revenue/investigations">Investigations</SubNavLink>
                </div>
              )}
            </div>

            {/* Quality Section */}
            <div>
              <button
                onClick={() => toggleSection('quality')}
                className="w-full flex items-center justify-between px-4 py-2 rounded-md hover:bg-gray-100 text-gray-700"
              >
                <span className="flex items-center gap-3">
                  <ClipboardCheck className="w-5 h-5" />
                  <span>Quality</span>
                </span>
                {expandedSections.quality ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
              {expandedSections.quality && (
                <div className="ml-4 mt-1 space-y-1">
                  <SubNavLink href="/dashboard/quality">Overview</SubNavLink>
                  <SubNavLink href="/dashboard/quality/hedis">HEDIS Evaluation</SubNavLink>
                  <SubNavLink href="/dashboard/quality/history">History</SubNavLink>
                  <SubNavLink href="/dashboard/quality/measures">Measures</SubNavLink>
                </div>
              )}
            </div>

            <div className="border-t border-gray-200 my-4"></div>

            <NavLink href="/dashboard/docs" icon={<FileText className="w-5 h-5" />}>
              Documentation
            </NavLink>
            <NavLink href="/dashboard/billing" icon={<CreditCard className="w-5 h-5" />}>
              Billing
            </NavLink>
            <NavLink href="/dashboard/contact" icon={<Mail className="w-5 h-5" />}>
              Contact
            </NavLink>
            {user.is_admin && (
              <>
                <div className="border-t border-gray-200 my-4"></div>
                <NavLink href="/dashboard/admin" icon={<Shield className="w-5 h-5" />}>
                  Admin Dashboard
                </NavLink>
              </>
            )}
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
      className="flex items-center gap-3 px-4 py-2 rounded-md hover:bg-gray-100 text-gray-700 hover:text-nuvii-blue"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}

function SubNavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={`block px-4 py-1.5 rounded-md text-sm transition-colors ${
        isActive
          ? 'bg-blue-50 text-nuvii-blue font-medium'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      }`}
    >
      {children}
    </Link>
  );
}