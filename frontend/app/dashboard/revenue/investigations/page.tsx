'use client';

import { useState } from 'react';
import {
  Stethoscope,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Clock,
  AlertCircle
} from 'lucide-react';
import { revenueAPI } from '@/lib/api';

interface Investigation {
  name: string;
  type: 'laboratory' | 'imaging' | 'procedure' | 'consultation';
  priority: 'stat' | 'urgent' | 'routine';
  rationale: string;
  expected_findings: string[];
  cpt_codes?: string[];
}

interface InvestigationResult {
  condition: string;
  severity_assessment: string;
  recommended_investigations: Investigation[];
  clinical_pathway: string;
  documentation_tips: string[];
}

const SEVERITY_LEVELS = [
  { value: 'mild', label: 'Mild' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'severe', label: 'Severe' },
  { value: 'critical', label: 'Critical' }
];

const SAMPLE_CONDITIONS = [
  'Acute kidney injury',
  'Heart failure exacerbation',
  'Pneumonia',
  'Diabetic ketoacidosis',
  'Sepsis',
  'COPD exacerbation',
  'Acute coronary syndrome',
  'Stroke'
];

export default function InvestigationsPage() {
  const [apiKey, setApiKey] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [condition, setCondition] = useState('');
  const [severityLevel, setSeverityLevel] = useState('moderate');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [error, setError] = useState('');

  const getInvestigations = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!clinicalNote.trim() && !condition.trim()) {
      setError('Please enter a clinical note or specify a condition');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await revenueAPI.recommendInvestigations(
        {
          clinical_note: clinicalNote,
          condition: condition || undefined,
          severity_level: severityLevel
        },
        apiKey
      );
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'stat': return 'bg-red-100 text-red-700 border-red-200';
      case 'urgent': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'routine': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'laboratory': return '🧪';
      case 'imaging': return '📷';
      case 'procedure': return '🔬';
      case 'consultation': return '👨‍⚕️';
      default: return '📋';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'stat': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'urgent': return <Clock className="w-4 h-4 text-orange-500" />;
      case 'routine': return <CheckCircle2 className="w-4 h-4 text-blue-500" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Stethoscope className="w-8 h-8 text-orange-600" />
          Investigation Recommendations
        </h1>
        <p className="text-gray-600 mt-2">
          Get evidence-based investigation recommendations to support clinical diagnoses
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

      {/* Input */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Clinical Information</h2>

        {/* Clinical Note */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Clinical Note (Optional)
          </label>
          <textarea
            value={clinicalNote}
            onChange={(e) => setClinicalNote(e.target.value)}
            className="w-full bg-white border border-gray-300 p-4 rounded text-sm min-h-[150px] focus:ring-2 focus:ring-orange-500"
            placeholder="Enter clinical note for context-aware recommendations..."
          />
        </div>

        {/* Condition */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Condition (Optional)
          </label>
          <input
            type="text"
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            placeholder="e.g., Acute kidney injury, Heart failure"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500"
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {SAMPLE_CONDITIONS.map((cond) => (
              <button
                key={cond}
                onClick={() => setCondition(cond)}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-orange-100 hover:text-orange-700 transition-colors"
              >
                {cond}
              </button>
            ))}
          </div>
        </div>

        {/* Severity Level */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity Level
          </label>
          <div className="flex gap-2">
            {SEVERITY_LEVELS.map((level) => (
              <button
                key={level.value}
                onClick={() => setSeverityLevel(level.value)}
                className={`px-4 py-2 rounded-md border transition-colors ${
                  severityLevel === level.value
                    ? 'bg-orange-100 border-orange-500 text-orange-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:border-orange-300'
                }`}
              >
                {level.label}
              </button>
            ))}
          </div>
        </div>

        {/* Get Recommendations Button */}
        <div className="mt-4">
          <button
            onClick={getInvestigations}
            disabled={loading || !apiKey || (!clinicalNote.trim() && !condition.trim())}
            className="px-6 py-3 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Getting Recommendations...
              </>
            ) : (
              <>
                <Stethoscope className="w-5 h-5" />
                Get Investigation Recommendations
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
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{result.condition}</h3>
            <p className="text-gray-600">{result.severity_assessment}</p>
            {result.clinical_pathway && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-1">Clinical Pathway</h4>
                <p className="text-sm text-blue-800">{result.clinical_pathway}</p>
              </div>
            )}
          </div>

          {/* Recommended Investigations */}
          {result.recommended_investigations && result.recommended_investigations.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-orange-600 p-4 text-white">
                <h3 className="text-lg font-semibold">
                  Recommended Investigations ({result.recommended_investigations.length})
                </h3>
              </div>
              <div className="p-4 space-y-4">
                {result.recommended_investigations.map((inv, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{getTypeIcon(inv.type)}</span>
                        <div>
                          <h4 className="font-semibold text-gray-900">{inv.name}</h4>
                          <span className="text-xs text-gray-500 capitalize">{inv.type}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {getPriorityIcon(inv.priority)}
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(inv.priority)}`}>
                          {inv.priority.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 mb-3">{inv.rationale}</p>

                    {inv.expected_findings && inv.expected_findings.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-500 uppercase mb-1">Expected Findings</p>
                        <ul className="list-disc list-inside text-sm text-gray-600">
                          {inv.expected_findings.map((finding, i) => (
                            <li key={i}>{finding}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {inv.cpt_codes && inv.cpt_codes.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">CPT:</span>
                        {inv.cpt_codes.map((code) => (
                          <span key={code} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                            {code}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Documentation Tips */}
          {result.documentation_tips && result.documentation_tips.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Documentation Tips</h3>
              <ul className="space-y-2">
                {result.documentation_tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
