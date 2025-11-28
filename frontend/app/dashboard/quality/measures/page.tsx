'use client';

import { useState, useEffect } from 'react';
import {
  Target,
  Search,
  Loader2,
  AlertTriangle,
  ChevronRight,
  Users,
  Calendar,
  FileText
} from 'lucide-react';
import { qualityAPI } from '@/lib/api';

interface HEDISMeasure {
  measure_id: string;
  measure_name: string;
  domain: string;
  description: string;
  eligible_population: string;
  numerator: string;
  denominator: string;
  exclusions: string[];
  data_sources: string[];
  reporting_year: number;
}

const DOMAINS = [
  'All Domains',
  'Effectiveness of Care',
  'Access/Availability of Care',
  'Experience of Care',
  'Utilization and Risk Adjusted Utilization',
  'Health Plan Descriptive Information'
];

export default function HEDISMeasuresPage() {
  const [apiKey, setApiKey] = useState('');
  const [measures, setMeasures] = useState<HEDISMeasure[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All Domains');
  const [selectedMeasure, setSelectedMeasure] = useState<HEDISMeasure | null>(null);

  const fetchMeasures = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await qualityAPI.getHEDISMeasures(apiKey);
      setMeasures(response.data.measures || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load measures');
    } finally {
      setLoading(false);
    }
  };

  const filteredMeasures = measures.filter(measure => {
    const matchesSearch = searchTerm === '' ||
      measure.measure_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      measure.measure_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      measure.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDomain = selectedDomain === 'All Domains' || measure.domain === selectedDomain;
    return matchesSearch && matchesDomain;
  });

  const getDomainColor = (domain: string) => {
    const colors: Record<string, string> = {
      'Effectiveness of Care': 'bg-blue-100 text-blue-700',
      'Access/Availability of Care': 'bg-green-100 text-green-700',
      'Experience of Care': 'bg-purple-100 text-purple-700',
      'Utilization and Risk Adjusted Utilization': 'bg-orange-100 text-orange-700',
      'Health Plan Descriptive Information': 'bg-gray-100 text-gray-700'
    };
    return colors[domain] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Target className="w-8 h-8 text-purple-600" />
          HEDIS Measure Reference
        </h1>
        <p className="text-gray-600 mt-2">
          Browse available HEDIS quality measures and their requirements
        </p>
      </div>

      {/* API Key */}
      <div className="bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          API Key
        </label>
        <div className="flex gap-4">
          <input
            type="text"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter your API key (mk_...)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <button
            onClick={fetchMeasures}
            disabled={loading || !apiKey}
            className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors flex items-center gap-2 disabled:bg-gray-400"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
            Load Measures
          </button>
        </div>
      </div>

      {/* Filters */}
      {measures.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by measure name, ID, or description..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* Domain Filter */}
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
            >
              {DOMAINS.map((domain) => (
                <option key={domain} value={domain}>{domain}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Two-column layout */}
      {measures.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Measure List */}
          <div className="lg:col-span-1 bg-white rounded-lg shadow overflow-hidden">
            <div className="bg-purple-600 p-4 text-white">
              <h3 className="font-semibold">
                Measures ({filteredMeasures.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {filteredMeasures.map((measure) => (
                <div
                  key={measure.measure_id}
                  onClick={() => setSelectedMeasure(measure)}
                  className={`p-4 cursor-pointer transition-colors flex items-center justify-between ${
                    selectedMeasure?.measure_id === measure.measure_id
                      ? 'bg-purple-50'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div>
                    <div className="font-medium text-gray-900 text-sm">{measure.measure_name}</div>
                    <div className="text-xs text-gray-500">{measure.measure_id}</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              ))}
            </div>
          </div>

          {/* Measure Details */}
          <div className="lg:col-span-2">
            {selectedMeasure ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="bg-purple-600 p-6 text-white">
                  <h3 className="text-xl font-semibold">{selectedMeasure.measure_name}</h3>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-purple-200">{selectedMeasure.measure_id}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${getDomainColor(selectedMeasure.domain)}`}>
                      {selectedMeasure.domain}
                    </span>
                  </div>
                </div>
                <div className="p-6 space-y-6">
                  {/* Description */}
                  <div>
                    <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                      <FileText className="w-5 h-5 text-purple-600" />
                      Description
                    </h4>
                    <p className="text-gray-700">{selectedMeasure.description}</p>
                  </div>

                  {/* Eligible Population */}
                  <div>
                    <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                      <Users className="w-5 h-5 text-purple-600" />
                      Eligible Population
                    </h4>
                    <p className="text-gray-700">{selectedMeasure.eligible_population}</p>
                  </div>

                  {/* Numerator & Denominator */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-green-50 p-4 rounded-lg">
                      <h5 className="font-medium text-green-800 mb-1">Numerator</h5>
                      <p className="text-sm text-green-700">{selectedMeasure.numerator}</p>
                    </div>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h5 className="font-medium text-blue-800 mb-1">Denominator</h5>
                      <p className="text-sm text-blue-700">{selectedMeasure.denominator}</p>
                    </div>
                  </div>

                  {/* Exclusions */}
                  {selectedMeasure.exclusions.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Exclusions</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {selectedMeasure.exclusions.map((exclusion, i) => (
                          <li key={i}>{exclusion}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Data Sources */}
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Data Sources</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedMeasure.data_sources.map((source, i) => (
                        <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Reporting Year */}
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Calendar className="w-4 h-4" />
                    Reporting Year: {selectedMeasure.reporting_year}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Target className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900">Select a Measure</h3>
                <p className="text-gray-500 mt-1">
                  Click on a measure from the list to view its details
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && measures.length === 0 && !error && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <Target className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No Measures Loaded</h3>
          <p className="text-gray-500 mt-1">
            Enter your API key and click &ldquo;Load Measures&rdquo; to browse HEDIS measures
          </p>
        </div>
      )}
    </div>
  );
}
