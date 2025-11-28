'use client';

import { useState, useEffect } from 'react';
import { History, Search, Filter, ChevronDown, ChevronRight, AlertTriangle, FileText } from 'lucide-react';
import { cdiAPI } from '@/lib/api';

interface QueryHistoryItem {
  id: string;
  created_at: string;
  clinical_note_excerpt: string;
  query_type: 'analysis' | 'query_generation' | 'gap_detection';
  gap_type?: string;
  condition?: string;
  generated_query?: string;
  gaps_found?: number;
  completeness_score?: number;
}

export default function CDIHistoryPage() {
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await cdiAPI.getQueryHistory(50);
      setHistory(response.data.items || []);
    } catch (err: any) {
      // If no history or API not available, show empty state
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
      item.clinical_note_excerpt.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.condition?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || item.query_type === filterType;
    return matchesSearch && matchesType;
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'analysis': return 'Note Analysis';
      case 'query_generation': return 'Query Generated';
      case 'gap_detection': return 'Gap Detection';
      default: return type;
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'analysis': return 'bg-blue-100 text-blue-700';
      case 'query_generation': return 'bg-purple-100 text-purple-700';
      case 'gap_detection': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <History className="w-8 h-8 text-green-600" />
          CDI Query History
        </h1>
        <p className="text-gray-600 mt-2">
          View and manage your past CDI analyses and generated queries
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
              placeholder="Search by condition or note content..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
            >
              <option value="all">All Types</option>
              <option value="analysis">Note Analysis</option>
              <option value="query_generation">Query Generation</option>
              <option value="gap_detection">Gap Detection</option>
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
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No history found</h3>
          <p className="text-gray-500 mt-1">
            {searchTerm || filterType !== 'all'
              ? 'Try adjusting your filters'
              : 'Start analyzing clinical notes to build your history'}
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
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeBadgeColor(item.query_type)}`}>
                        {getTypeLabel(item.query_type)}
                      </span>
                      {item.condition && (
                        <span className="text-sm font-medium text-gray-900">{item.condition}</span>
                      )}
                      {item.gap_type && (
                        <span className="text-xs text-gray-500">({item.gap_type})</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {item.clinical_note_excerpt}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">{formatDate(item.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    {item.completeness_score !== undefined && (
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">{item.completeness_score}%</div>
                        <div className="text-xs text-gray-500">Completeness</div>
                      </div>
                    )}
                    {item.gaps_found !== undefined && (
                      <div className="text-right">
                        <div className="text-lg font-bold text-orange-600">{item.gaps_found}</div>
                        <div className="text-xs text-gray-500">Gaps</div>
                      </div>
                    )}
                    {expandedId === item.id ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedId === item.id && item.generated_query && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Generated Query</h4>
                    <div className="bg-purple-50 border-l-4 border-purple-500 p-3 rounded-r">
                      <p className="text-sm text-gray-800 italic">&ldquo;{item.generated_query}&rdquo;</p>
                    </div>
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
