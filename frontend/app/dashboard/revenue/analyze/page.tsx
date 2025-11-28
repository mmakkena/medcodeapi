'use client';

import { useState } from 'react';
import {
  FileBarChart,
  Loader2,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Activity,
  Stethoscope
} from 'lucide-react';
import { revenueAPI, RevenueAnalysisRequest } from '@/lib/api';

interface RevenueResult {
  summary: string;
  estimated_revenue_impact: number;
  em_analysis?: {
    recommended_level: string;
    current_level?: string;
    rationale: string;
    documentation_supports: string[];
    mdm_complexity: string;
  };
  hcc_opportunities?: Array<{
    condition: string;
    hcc_code: string;
    raf_value: number;
    documentation_status: string;
    suggested_query?: string;
  }>;
  drg_analysis?: {
    predicted_drg: string;
    drg_weight: number;
    mcc_present: boolean;
    cc_present: boolean;
    optimization_opportunities: string[];
  };
  coding_recommendations: Array<{
    code: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    rationale: string;
  }>;
}

const SETTINGS = [
  { value: 'outpatient', label: 'Outpatient' },
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'ed', label: 'Emergency Department' },
  { value: 'observation', label: 'Observation' }
];

const PATIENT_TYPES = [
  { value: 'new', label: 'New Patient' },
  { value: 'established', label: 'Established Patient' },
  { value: 'initial', label: 'Initial Hospital Care' },
  { value: 'subsequent', label: 'Subsequent Hospital Care' }
];

const SAMPLE_NOTES = [
  {
    title: 'Complex Outpatient Visit',
    note: `68-year-old male with diabetes mellitus type 2 with chronic kidney disease stage 3, hypertension, and hyperlipidemia presents for comprehensive management. A1C 8.4%, eGFR 42. Patient also reports chest pain on exertion - ordered stress test. Discussed risks of uncontrolled diabetes. Adjusted medications, ordered labs, referred to nephrology. Total time 45 minutes including care coordination.`,
    setting: 'outpatient',
    patientType: 'established'
  },
  {
    title: 'Inpatient Admission',
    note: `72-year-old female admitted with acute hypoxic respiratory failure requiring mechanical ventilation. History of CHF with EF 30%, COPD, and chronic respiratory failure on home oxygen. Developed healthcare-associated pneumonia. Sepsis protocol initiated. Multiple organ systems involved requiring ICU management.`,
    setting: 'inpatient',
    patientType: 'initial'
  }
];

export default function RevenueAnalyzePage() {
  const [apiKey, setApiKey] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [setting, setSetting] = useState('outpatient');
  const [patientType, setPatientType] = useState('established');
  const [includeEM, setIncludeEM] = useState(true);
  const [includeHCC, setIncludeHCC] = useState(true);
  const [includeDRG, setIncludeDRG] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RevenueResult | null>(null);
  const [error, setError] = useState('');

  const loadSample = () => {
    const sample = SAMPLE_NOTES[Math.floor(Math.random() * SAMPLE_NOTES.length)];
    setClinicalNote(sample.note);
    setSetting(sample.setting);
    setPatientType(sample.patientType);
    setResult(null);
    setError('');
  };

  const analyzeRevenue = async () => {
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
      const request: RevenueAnalysisRequest = {
        clinical_note: clinicalNote,
        setting: setting as any,
        patient_type: patientType as any,
        include_em_coding: includeEM,
        include_hcc: includeHCC,
        include_drg: includeDRG
      };
      const response = await revenueAPI.analyze(request, apiKey);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'bg-green-100 text-green-700 border-green-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <FileBarChart className="w-8 h-8 text-green-600" />
          Revenue Analysis
        </h1>
        <p className="text-gray-600 mt-2">
          Comprehensive revenue optimization including E/M coding, HCC capture, and DRG analysis
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* Clinical Note Input */}
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-green-600" />
            Clinical Note
          </h2>
          <button
            onClick={loadSample}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
          >
            Load Sample
          </button>
        </div>
        <textarea
          value={clinicalNote}
          onChange={(e) => setClinicalNote(e.target.value)}
          className="w-full bg-white border border-gray-300 p-4 rounded text-sm min-h-[200px] focus:ring-2 focus:ring-green-500"
          placeholder="Enter clinical note..."
        />

        {/* Settings */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Setting</label>
            <select
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
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
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
            >
              {PATIENT_TYPES.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Analysis Options */}
        <div className="mt-4 flex flex-wrap gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeEM}
              onChange={(e) => setIncludeEM(e.target.checked)}
              className="rounded text-green-600"
            />
            <span className="text-sm text-gray-700">E/M Coding Analysis</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeHCC}
              onChange={(e) => setIncludeHCC(e.target.checked)}
              className="rounded text-green-600"
            />
            <span className="text-sm text-gray-700">HCC Opportunities</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeDRG}
              onChange={(e) => setIncludeDRG(e.target.checked)}
              className="rounded text-green-600"
            />
            <span className="text-sm text-gray-700">DRG Analysis (Inpatient)</span>
          </label>
        </div>

        {/* Analyze Button */}
        <div className="mt-4">
          <button
            onClick={analyzeRevenue}
            disabled={loading || !apiKey || !clinicalNote.trim()}
            className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <FileBarChart className="w-5 h-5" />
                Analyze Revenue Impact
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
          {/* Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Revenue Impact Summary</h3>
                <p className="text-gray-600 mt-2">{result.summary}</p>
              </div>
              <div className="text-right bg-green-50 p-4 rounded-lg">
                <div className="text-3xl font-bold text-green-600">
                  ${result.estimated_revenue_impact.toLocaleString()}
                </div>
                <p className="text-sm text-gray-500">Estimated Impact</p>
              </div>
            </div>
          </div>

          {/* E/M Analysis */}
          {result.em_analysis && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-blue-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  E/M Coding Analysis
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">Recommended Level</p>
                    <p className="text-2xl font-bold text-blue-700">{result.em_analysis.recommended_level}</p>
                  </div>
                  {result.em_analysis.current_level && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-xs text-gray-500 uppercase">Current Level</p>
                      <p className="text-2xl font-bold text-gray-700">{result.em_analysis.current_level}</p>
                    </div>
                  )}
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">MDM Complexity</p>
                    <p className="text-2xl font-bold text-purple-700">{result.em_analysis.mdm_complexity}</p>
                  </div>
                </div>
                <p className="text-gray-700 mb-4">{result.em_analysis.rationale}</p>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Documentation Supports:</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {result.em_analysis.documentation_supports.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* HCC Opportunities */}
          {result.hcc_opportunities && result.hcc_opportunities.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-purple-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  HCC Opportunities ({result.hcc_opportunities.length})
                </h3>
              </div>
              <div className="p-4 space-y-4">
                {result.hcc_opportunities.map((opp, index) => (
                  <div key={index} className="border-l-4 border-purple-400 bg-purple-50 p-4 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold text-gray-900">{opp.condition}</h4>
                        <p className="text-sm text-gray-600">HCC: {opp.hcc_code}</p>
                        <span className="text-xs text-purple-600">{opp.documentation_status}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-purple-700">+{opp.raf_value.toFixed(3)}</div>
                        <p className="text-xs text-gray-500">RAF Value</p>
                      </div>
                    </div>
                    {opp.suggested_query && (
                      <div className="mt-3 bg-white p-3 rounded border border-purple-200">
                        <p className="text-xs text-gray-500">Suggested Query:</p>
                        <p className="text-sm text-gray-800 italic">&ldquo;{opp.suggested_query}&rdquo;</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* DRG Analysis */}
          {result.drg_analysis && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-teal-600 p-4 text-white">
                <h3 className="text-lg font-semibold">DRG Analysis</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-teal-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">Predicted DRG</p>
                    <p className="text-xl font-bold text-teal-700">{result.drg_analysis.predicted_drg}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">DRG Weight</p>
                    <p className="text-xl font-bold text-gray-700">{result.drg_analysis.drg_weight.toFixed(4)}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">MCC Present</p>
                    <p className="text-xl font-bold text-gray-700">{result.drg_analysis.mcc_present ? 'Yes' : 'No'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-xs text-gray-500 uppercase">CC Present</p>
                    <p className="text-xl font-bold text-gray-700">{result.drg_analysis.cc_present ? 'Yes' : 'No'}</p>
                  </div>
                </div>
                {result.drg_analysis.optimization_opportunities.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Optimization Opportunities:</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {result.drg_analysis.optimization_opportunities.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Coding Recommendations */}
          {result.coding_recommendations && result.coding_recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-green-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Coding Recommendations ({result.coding_recommendations.length})
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {result.coding_recommendations.map((rec, index) => (
                  <div key={index} className="border-l-4 border-green-400 bg-green-50 p-4 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="font-bold text-lg text-gray-900">{rec.code}</span>
                        <p className="text-gray-700 text-sm">{rec.description}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactColor(rec.impact)}`}>
                        {rec.impact.toUpperCase()} IMPACT
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">{rec.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
