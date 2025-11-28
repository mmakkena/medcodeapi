'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ClipboardCheck,
  TrendingUp,
  Target,
  BarChart3,
  ArrowRight,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

interface QualityStats {
  totalEvaluations: number;
  measuresTracked: number;
  complianceRate: number;
  gapsIdentified: number;
}

export default function QualityDashboardPage() {
  const [stats, setStats] = useState<QualityStats>({
    totalEvaluations: 0,
    measuresTracked: 0,
    complianceRate: 0,
    gapsIdentified: 0
  });

  useEffect(() => {
    // Placeholder stats
    setStats({
      totalEvaluations: 234,
      measuresTracked: 42,
      complianceRate: 87.5,
      gapsIdentified: 89
    });
  }, []);

  const features = [
    {
      title: 'HEDIS Evaluation',
      description: 'Evaluate clinical documentation against HEDIS quality measures and identify gaps',
      icon: ClipboardCheck,
      href: '/dashboard/quality/hedis',
      color: 'bg-teal-500',
      stats: `${stats.measuresTracked} measures`
    },
    {
      title: 'Quality History',
      description: 'View past quality evaluations and track improvement trends',
      icon: BarChart3,
      href: '/dashboard/quality/history',
      color: 'bg-blue-500',
      stats: `${stats.totalEvaluations} evaluations`
    },
    {
      title: 'Measure Reference',
      description: 'Browse available HEDIS measures and their requirements',
      icon: Target,
      href: '/dashboard/quality/measures',
      color: 'bg-purple-500',
      stats: '150+ measures'
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Quality Measures Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Evaluate documentation against HEDIS measures and improve quality performance
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Evaluations</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalEvaluations}</p>
            </div>
            <ClipboardCheck className="w-10 h-10 text-teal-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            <TrendingUp className="w-4 h-4 mr-1" />
            +18% this month
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Measures Tracked</p>
              <p className="text-2xl font-bold text-gray-900">{stats.measuresTracked}</p>
            </div>
            <Target className="w-10 h-10 text-purple-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-gray-500">
            HEDIS 2024
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Compliance Rate</p>
              <p className="text-2xl font-bold text-gray-900">{stats.complianceRate}%</p>
            </div>
            <CheckCircle2 className="w-10 h-10 text-green-500 opacity-50" />
          </div>
          <div className="mt-2 flex items-center text-xs text-green-600">
            Above target
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
          <div className="mt-2 flex items-center text-xs text-orange-600">
            Action needed
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature) => (
          <Link
            key={feature.title}
            href={feature.href}
            className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 group"
          >
            <div className="flex flex-col h-full">
              <div className={`${feature.color} p-3 rounded-lg w-fit`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1 mt-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-teal-600 transition-colors">
                    {feature.title}
                  </h3>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-teal-600 transition-colors" />
                </div>
                <p className="text-gray-600 text-sm mt-2">{feature.description}</p>
              </div>
              <p className="text-xs text-gray-400 mt-4">{feature.stats}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Start */}
      <div className="bg-gradient-to-r from-teal-600 to-cyan-600 rounded-lg shadow-lg p-8 text-white">
        <h2 className="text-2xl font-bold mb-4">Improve Quality Performance</h2>
        <p className="text-teal-100 mb-6">
          Evaluate patient encounters against HEDIS measures to identify care gaps and improve quality scores.
        </p>
        <Link
          href="/dashboard/quality/hedis"
          className="inline-flex items-center gap-2 bg-white text-teal-600 px-6 py-3 rounded-lg font-semibold hover:bg-teal-50 transition-colors"
        >
          <ClipboardCheck className="w-5 h-5" />
          Start HEDIS Evaluation
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </div>
  );
}
