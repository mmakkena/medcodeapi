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