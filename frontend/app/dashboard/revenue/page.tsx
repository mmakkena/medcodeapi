'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  DollarSign,
  TrendingUp,
  FileBarChart,
  Activity,
  Stethoscope,
  ArrowRight
} from 'lucide-react';

interface RevenueStats {
  totalAnalyses: number;
  avgRevenueImpact: number;
  hccOpportunities: number;
  emOptimizations: number;
}

export default function RevenueDashboardPage() {
  const [stats, setStats] = useState<RevenueStats>({
    totalAnalyses: 0,
    avgRevenueImpact: 0,
    hccOpportunities: 0,
    emOptimizations: 0
  });

  useEffect(() => {
    // Placeholder stats
    setStats({
      totalAnalyses: 78,
      avgRevenueImpact: 12450,
      hccOpportunities: 156,
      emOptimizations: 45
    });
  }, []);

  const features = [
    {
      title: 'Full Revenue Analysis',
      description: 'Comprehensive analysis including E/M coding, HCC opportunities, and DRG optimization',
      icon: FileBarChart,
      href: '/dashboard/revenue/analyze',
      color: 'bg-green-500',
      stats: `${stats.totalAnalyses} analyses`
    },
    {
      title: 'E/M Level Analysis',
      description: 'Evaluate and optimize Evaluation & Management coding levels based on documentation',
      icon: Activity,
      href: '/dashboard/revenue/em-coding',
      color: 'bg-blue-500',
      stats: `${stats.emOptimizations} optimizations`
    },
    {
      title: 'HCC Risk Adjustment',
      description: 'Identify HCC opportunities for risk-adjusted payment models and value-based care',
      icon: TrendingUp,
      href: '/dashboard/revenue/hcc',
      color: 'bg-purple-500',
      stats: `${stats.hccOpportunities} opportunities`
    },
    {
      title: 'Investigation Recommendations',
      description: 'Get recommended investigations and tests to support clinical diagnoses',
      icon: Stethoscope,
      href: '/dashboard/revenue/investigations',
      color: 'bg-orange-500',
      stats: 'Evidence-based'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Revenue Optimization Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Maximize reimbursement through accurate coding, HCC capture, and documentation optimization
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
            <FileBarChart className="w-10 h-10 text-green-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            <TrendingUp className="w-4 h-4 mr-1" />
            +15% this month
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg. Revenue Impact</p>
              <p className="text-2xl font-bold text-gray-900">${stats.avgRevenueImpact.toLocaleString()}</p>
            </div>
            <DollarSign className="w-10 h-10 text-green-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            Per encounter analyzed
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">HCC Opportunities</p>
              <p className="text-2xl font-bold text-gray-900">{stats.hccOpportunities}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-purple-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-purple-600">
            Identified this quarter
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">E/M Optimizations</p>
              <p className="text-2xl font-bold text-gray-900">{stats.emOptimizations}</p>
            </div>
            <Activity className="w-10 h-10 text-blue-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-blue-600">
            Level adjustments made
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
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-green-600 transition-colors">
                    {feature.title}
                  </h3>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-green-600 transition-colors" />
                </div>
                <p className="text-gray-600 text-sm mt-1">{feature.description}</p>
                <p className="text-xs text-gray-400 mt-2">{feature.stats}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Start */}
      <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-lg shadow-lg p-8 text-white">
        <h2 className="text-2xl font-bold mb-4">Maximize Revenue Capture</h2>
        <p className="text-green-100 mb-6">
          Analyze clinical documentation to identify missed revenue opportunities, optimize E/M levels, and capture HCC conditions.
        </p>
        <Link
          href="/dashboard/revenue/analyze"
          className="inline-flex items-center gap-2 bg-white text-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-green-50 transition-colors"
        >
          <FileBarChart className="w-5 h-5" />
          Start Revenue Analysis
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  );
}
