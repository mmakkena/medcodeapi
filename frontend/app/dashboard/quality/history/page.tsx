'use client';

import { useState, useEffect } from 'react';
import {
  History,
  Search,
  Filter,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { qualityAPI } from '@/lib/api';

interface HistoryItem {
  id: string;
  created_at: string;
  patient_age: number;
  patient_gender: string;
  total_measures: number;
  measures_met: number;
  measures_not_met: number;
  compliance_rate: number;
  priority_gaps: string[];
}

export default function QualityHistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCompliance, setFilterCompliance] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await qualityAPI.getHEDISHistory(50);
      setHistory(response.data.items || []);
    } catch (err: any) {
      setHistory([]);
      if (err.response?.status !== 404) {
        setError(err.response?.data?.detail || 'Failed to load history');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredHistory = history.filter(item => {
    const matchesSearch = searchTerm === '' ||
      item.priority_gaps.some(gap => gap.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCompliance = filterCompliance === 'all' ||
      (filterCompliance === 'high' && item.compliance_rate >= 80) ||
      (filterCompliance === 'medium' && item.compliance_rate >= 50 && item.compliance_rate < 80) ||
      (filterCompliance === 'low' && item.compliance_rate < 50);
    return matchesSearch && matchesCompliance;
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getComplianceColor = (rate: number) => {
    if (rate >= 80) return 'text-green-600 bg-green-50';
    if (rate >= 50) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <History className="w-8 h-8 text-blue-600" />
          Quality Evaluation History
        </h1>
        <p className="text-gray-600 mt-2">
          View past HEDIS evaluations and track quality trends
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by gap or action..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Compliance Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filterCompliance}
              onChange={(e) => setFilterCompliance(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Compliance Levels</option>
              <option value="high">High (80%+)</option>
              <option value="medium">Medium (50-79%)</option>
              <option value="low">Low (&lt;50%)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* History List */}
      {loading ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Loading history...
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <ClipboardCheck className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No evaluations found</h3>
          <p className="text-gray-500 mt-1">
            {searchTerm || filterCompliance !== 'all'
              ? 'Try adjusting your filters'
              : 'Start evaluating patients against HEDIS measures'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="divide-y divide-gray-200">
            {filteredHistory.map((item) => (
              <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getComplianceColor(item.compliance_rate)}`}>
                        {item.compliance_rate}% Compliance
                      </span>
                      <span className="text-sm text-gray-500">
                        {item.patient_age}yo {item.patient_gender}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1 text-gray-600">
                        <ClipboardCheck className="w-4 h-4" />
                        {item.total_measures} measures
                      </span>
                      <span className="flex items-center gap-1 text-green-600">
                        <CheckCircle2 className="w-4 h-4" />
                        {item.measures_met} met
                      </span>
                      <span className="flex items-center gap-1 text-red-600">
                        <XCircle className="w-4 h-4" />
                        {item.measures_not_met} not met
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">{formatDate(item.created_at)}</p>
                  </div>
                  <div className="ml-4">
                    {expandedId === item.id ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedId === item.id && item.priority_gaps.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Priority Gaps</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {item.priority_gaps.map((gap, i) => (
                        <li key={i}>{gap}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
