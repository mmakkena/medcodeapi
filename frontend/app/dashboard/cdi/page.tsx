'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  FileSearch,
  MessageSquare,
  History,
  BookOpen,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';

interface DashboardStats {
  totalAnalyses: number;
  queriesGenerated: number;
  gapsIdentified: number;
  avgConfidence: number;
}

export default function CDIDashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalAnalyses: 0,
    queriesGenerated: 0,
    gapsIdentified: 0,
    avgConfidence: 0
  });

  // Placeholder stats - in production, these would come from the API
  useEffect(() => {
    setStats({
      totalAnalyses: 156,
      queriesGenerated: 89,
      gapsIdentified: 234,
      avgConfidence: 87.5
    });
  }, []);

  const features = [
    {
      title: 'Note Analysis',
      description: 'Analyze clinical notes for documentation gaps, missing specificity, and coding opportunities',
      icon: FileSearch,
      href: '/dashboard/cdi/analyze',
      color: 'bg-blue-500',
      stats: `${stats.totalAnalyses} analyses`
    },
    {
      title: 'Query Generator',
      description: 'Generate compliant CDI queries to clarify documentation with physicians',
      icon: MessageSquare,
      href: '/dashboard/cdi/query-generator',
      color: 'bg-purple-500',
      stats: `${stats.queriesGenerated} queries`
    },
    {
      title: 'Query History',
      description: 'View and manage your past CDI analyses and generated queries',
      icon: History,
      href: '/dashboard/cdi/history',
      color: 'bg-green-500',
      stats: 'Last 30 days'
    },
    {
      title: 'CDI Guidelines',
      description: 'Browse condition-specific CDI guidelines and documentation requirements',
      icon: BookOpen,
      href: '/dashboard/cdi/guidelines',
      color: 'bg-orange-500',
      stats: '150+ conditions'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">CDI Analysis Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Clinical Documentation Improvement tools to identify gaps, generate queries, and optimize documentation
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Analyses</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalAnalyses}</p>
            </div>
            <FileSearch className="w-10 h-10 text-blue-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            <TrendingUp className="w-4 h-4 mr-1" />
            +12% this month
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Queries Generated</p>
              <p className="text-2xl font-bold text-gray-900">{stats.queriesGenerated}</p>
            </div>
            <MessageSquare className="w-10 h-10 text-purple-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            <TrendingUp className="w-4 h-4 mr-1" />
            +8% this month
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Gaps Identified</p>
              <p className="text-2xl font-bold text-gray-900">{stats.gapsIdentified}</p>
            </div>
            <AlertTriangle className="w-10 h-10 text-orange-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-gray-500">
            Across all analyses
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg. Confidence</p>
              <p className="text-2xl font-bold text-gray-900">{stats.avgConfidence}%</p>
            </div>
            <CheckCircle2 className="w-10 h-10 text-green-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            High quality results
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature) => (
          <Link
            key={feature.title}
            href={feature.href}
            className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 group"
          >
            <div className="flex items-start gap-4">
              <div className={`${feature.color} p-3 rounded-lg`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-nuvii-blue transition-colors">
                    {feature.title}
                  </h3>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-nuvii-blue transition-colors" />
                </div>
                <p className="text-gray-600 text-sm mt-1">{feature.description}</p>
                <p className="text-xs text-gray-400 mt-2">{feature.stats}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Start */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-8 text-white">
        <h2 className="text-2xl font-bold mb-4">Quick Start: Analyze a Clinical Note</h2>
        <p className="text-blue-100 mb-6">
          Get started by analyzing a clinical note to identify documentation gaps and generate CDI queries.
        </p>
        <Link
          href="/dashboard/cdi/analyze"
          className="inline-flex items-center gap-2 bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
        >
          <FileSearch className="w-5 h-5" />
          Start Analysis
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  );
}
