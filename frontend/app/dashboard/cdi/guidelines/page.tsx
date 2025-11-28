'use client';

import { useState } from 'react';
import {
  BookOpen,
  Search,
  Loader2,
  AlertTriangle,
  ChevronRight,
  FileText,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { cdiAPI } from '@/lib/api';

interface Guideline {
  condition: string;
  icd10_codes: string[];
  documentation_requirements: string[];
  specificity_elements: string[];
  common_gaps: string[];
  query_templates: string[];
  clinical_indicators: string[];
  severity_levels?: string[];
}

const COMMON_CONDITIONS = [
  'Diabetes mellitus',
  'Heart failure',
  'COPD',
  'Pneumonia',
  'Sepsis',
  'Acute kidney injury',
  'Malnutrition',
  'Respiratory failure',
  'Encephalopathy'
];

export default function CDIGuidelinesPage() {
  const [apiKey, setApiKey] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCondition, setSelectedCondition] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<Guideline[]>([]);
  const [selectedGuideline, setSelectedGuideline] = useState<Guideline | null>(null);
  const [error, setError] = useState('');

  const searchGuidelines = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }

    setLoading(true);
    setError('');
    setSelectedGuideline(null);

    try {
      const response = await cdiAPI.searchGuidelines(searchQuery, apiKey, 10);
      setSearchResults(response.data.guidelines || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getGuidelineByCondition = async (condition: string) => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    setLoading(true);
    setError('');
    setSelectedCondition(condition);

    try {
      const response = await cdiAPI.getGuidelinesByCondition(condition, apiKey);
      setSelectedGuideline(response.data);
      setSearchResults([]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load guideline');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <BookOpen className="w-8 h-8 text-orange-600" />
          CDI Guidelines
        </h1>
        <p className="text-gray-600 mt-2">
          Browse condition-specific CDI guidelines and documentation requirements
        </p>
      </div>

      {/* API Key */}
      <div className="bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          API Key
        </label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter your API key (mk_...)"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent"
        />
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Search Guidelines</h2>
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchGuidelines()}
              placeholder="Search by condition, ICD-10 code, or keyword..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500"
            />
          </div>
          <button
            onClick={searchGuidelines}
            disabled={loading || !apiKey}
            className="px-6 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors flex items-center gap-2 disabled:bg-gray-400"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Search
          </button>
        </div>
      </div>

      {/* Common Conditions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Common Conditions</h2>
        <div className="flex flex-wrap gap-2">
          {COMMON_CONDITIONS.map((condition) => (
            <button
              key={condition}
              onClick={() => getGuidelineByCondition(condition)}
              className={`px-4 py-2 rounded-lg border text-sm transition-colors ${
                selectedCondition === condition
                  ? 'bg-orange-100 border-orange-500 text-orange-700'
                  : 'bg-gray-50 border-gray-200 text-gray-700 hover:border-orange-300'
              }`}
            >
              {condition}
            </button>
          ))}
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

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="bg-orange-600 p-4 text-white">
            <h3 className="text-lg font-semibold">Search Results ({searchResults.length})</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {searchResults.map((guideline, index) => (
              <div
                key={index}
                onClick={() => setSelectedGuideline(guideline)}
                className="p-4 hover:bg-orange-50 cursor-pointer transition-colors flex items-center justify-between"
              >
                <div>
                  <h4 className="font-medium text-gray-900">{guideline.condition}</h4>
                  <div className="flex gap-2 mt-1">
                    {guideline.icd10_codes.slice(0, 3).map((code) => (
                      <span key={code} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                        {code}
                      </span>
                    ))}
                    {guideline.icd10_codes.length > 3 && (
                      <span className="text-xs text-gray-500">+{guideline.icd10_codes.length - 3} more</span>
                    )}
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Guideline Details */}
      {selectedGuideline && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="bg-orange-600 p-4 text-white">
            <h3 className="text-xl font-semibold">{selectedGuideline.condition}</h3>
            <div className="flex gap-2 mt-2">
              {selectedGuideline.icd10_codes.map((code) => (
                <span key={code} className="text-sm bg-white/20 px-2 py-0.5 rounded">
                  {code}
                </span>
              ))}
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Documentation Requirements */}
            {selectedGuideline.documentation_requirements.length > 0 && (
              <div>
                <h4 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
                  <FileText className="w-5 h-5 text-orange-600" />
                  Documentation Requirements
                </h4>
                <ul className="space-y-2">
                  {selectedGuideline.documentation_requirements.map((req, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      {req}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Specificity Elements */}
            {selectedGuideline.specificity_elements.length > 0 && (
              <div>
                <h4 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
                  <AlertCircle className="w-5 h-5 text-blue-600" />
                  Specificity Elements
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {selectedGuideline.specificity_elements.map((element, i) => (
                    <div key={i} className="bg-blue-50 border border-blue-200 rounded p-2 text-sm text-blue-800">
                      {element}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Common Gaps */}
            {selectedGuideline.common_gaps.length > 0 && (
              <div>
                <h4 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  Common Documentation Gaps
                </h4>
                <ul className="space-y-2">
                  {selectedGuideline.common_gaps.map((gap, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <span className="w-6 h-6 bg-orange-100 text-orange-700 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                        {i + 1}
                      </span>
                      {gap}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Query Templates */}
            {selectedGuideline.query_templates.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Sample Query Templates</h4>
                <div className="space-y-3">
                  {selectedGuideline.query_templates.map((template, i) => (
                    <div key={i} className="bg-purple-50 border-l-4 border-purple-500 p-3 rounded-r">
                      <p className="text-sm text-gray-800 italic">&ldquo;{template}&rdquo;</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Clinical Indicators */}
            {selectedGuideline.clinical_indicators.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Clinical Indicators</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedGuideline.clinical_indicators.map((indicator, i) => (
                    <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                      {indicator}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
