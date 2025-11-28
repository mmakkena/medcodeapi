'use client';

import { useState } from 'react';
import {
  Activity,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Info
} from 'lucide-react';
import { revenueAPI } from '@/lib/api';

interface EMResult {
  recommended_level: string;
  em_code: string;
  rationale: string;
  mdm_analysis: {
    problems_addressed: string;
    data_reviewed: string;
    risk_level: string;
    overall_complexity: string;
  };
  documentation_elements: Array<{
    element: string;
    status: 'present' | 'missing' | 'partial';
    notes?: string;
  }>;
  time_based_option?: {
    total_time: number;
    supports_level: string;
    activities: string[];
  };
}

const SETTINGS = [
  { value: 'office', label: 'Office/Outpatient' },
  { value: 'hospital', label: 'Hospital Inpatient' },
  { value: 'ed', label: 'Emergency Department' },
  { value: 'observation', label: 'Observation' },
  { value: 'telehealth', label: 'Telehealth' }
];

const PATIENT_TYPES = [
  { value: 'new', label: 'New Patient' },
  { value: 'established', label: 'Established Patient' },
  { value: 'initial', label: 'Initial Visit' },
  { value: 'subsequent', label: 'Subsequent Visit' }
];

export default function EMCodingPage() {
  const [apiKey, setApiKey] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [setting, setSetting] = useState('office');
  const [patientType, setPatientType] = useState('established');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EMResult | null>(null);
  const [error, setError] = useState('');

  const analyzeEM = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!clinicalNote.trim() || clinicalNote.trim().length < 50) {
      setError('Please enter a clinical note (minimum 50 characters)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await revenueAPI.analyzeEMCoding(clinicalNote, setting, patientType, apiKey);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'present':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'missing':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'partial':
        return <Info className="w-5 h-5 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'present': return 'bg-green-50 border-green-200';
      case 'missing': return 'bg-red-50 border-red-200';
      case 'partial': return 'bg-yellow-50 border-yellow-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="w-8 h-8 text-blue-600" />
          E/M Level Analysis
        </h1>
        <p className="text-gray-600 mt-2">
          Evaluate documentation to determine appropriate E/M coding level based on 2021 guidelines
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Input */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Clinical Documentation</h2>
        <textarea
          value={clinicalNote}
          onChange={(e) => setClinicalNote(e.target.value)}
          className="w-full bg-white border border-gray-300 p-4 rounded text-sm min-h-[200px] focus:ring-2 focus:ring-blue-500"
          placeholder="Enter clinical note for E/M analysis..."
        />

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Setting</label>
            <select
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              {SETTINGS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Patient Type</label>
            <select
              value={patientType}
              onChange={(e) => setPatientType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              {PATIENT_TYPES.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={analyzeEM}
            disabled={loading || !apiKey || !clinicalNote.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Activity className="w-5 h-5" />
                Analyze E/M Level
              </>
            )}
          </button>
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

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Recommended Level */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Recommended E/M Level</h3>
                <p className="text-gray-600 mt-1">{result.rationale}</p>
              </div>
              <div className="text-center bg-blue-50 p-6 rounded-lg">
                <div className="text-4xl font-bold text-blue-600">{result.recommended_level}</div>
                <div className="text-sm text-gray-500 mt-1">{result.em_code}</div>
              </div>
            </div>
          </div>

          {/* MDM Analysis */}
          {result.mdm_analysis && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-blue-600 p-4 text-white">
                <h3 className="text-lg font-semibold">Medical Decision Making Analysis</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase mb-1">Problems Addressed</p>
                    <p className="font-semibold text-gray-900">{result.mdm_analysis.problems_addressed}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase mb-1">Data Reviewed</p>
                    <p className="font-semibold text-gray-900">{result.mdm_analysis.data_reviewed}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase mb-1">Risk Level</p>
                    <p className="font-semibold text-gray-900">{result.mdm_analysis.risk_level}</p>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase mb-1">Overall Complexity</p>
                    <p className="font-bold text-blue-700">{result.mdm_analysis.overall_complexity}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Documentation Elements */}
          {result.documentation_elements && result.documentation_elements.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-gray-700 p-4 text-white">
                <h3 className="text-lg font-semibold">Documentation Elements</h3>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.documentation_elements.map((elem, index) => (
                    <div key={index} className={`border rounded-lg p-4 ${getStatusBg(elem.status)}`}>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(elem.status)}
                        <span className="font-medium text-gray-900">{elem.element}</span>
                      </div>
                      {elem.notes && (
                        <p className="text-sm text-gray-600 mt-2">{elem.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Time-Based Option */}
          {result.time_based_option && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-purple-600 p-4 text-white">
                <h3 className="text-lg font-semibold">Time-Based Coding Option</h3>
              </div>
              <div className="p-6">
                <div className="flex items-center gap-6 mb-4">
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">Total Time</p>
                    <p className="text-2xl font-bold text-purple-700">{result.time_based_option.total_time} min</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">Supports Level</p>
                    <p className="text-2xl font-bold text-purple-700">{result.time_based_option.supports_level}</p>
                  </div>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Time Activities:</h4>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {result.time_based_option.activities.map((activity, i) => (
                    <li key={i}>{activity}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
