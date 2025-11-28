'use client';

import { useState } from 'react';
import {
  MessageSquare,
  Loader2,
  AlertTriangle,
  Copy,
  CheckCircle,
  Stethoscope
} from 'lucide-react';
import { cdiAPI, CDIQueryRequest } from '@/lib/api';

interface QueryResult {
  query: string;
  gap_type: string;
  condition: string;
  query_style: string;
  compliance_notes: string[];
  documentation_requirements: string[];
}

const GAP_TYPES = [
  { value: 'specificity', label: 'Specificity Gap', description: 'Missing details about type, location, or characteristics' },
  { value: 'acuity', label: 'Acuity Gap', description: 'Missing severity or acute/chronic status' },
  { value: 'comorbidity', label: 'Comorbidity Gap', description: 'Missing related conditions or complications' },
  { value: 'medical_necessity', label: 'Medical Necessity Gap', description: 'Missing clinical rationale for services' }
];

const QUERY_STYLES = [
  { value: 'open_ended', label: 'Open-Ended', description: 'Allows physician to provide detailed response' },
  { value: 'yes_no', label: 'Yes/No', description: 'Simple confirmation questions' },
  { value: 'documentation_based', label: 'Documentation-Based', description: 'Requests specific documentation' }
];

const SAMPLE_SCENARIOS = [
  {
    title: 'Unspecified Diabetes',
    note: `Patient with diabetes mellitus on metformin. Blood glucose elevated at 245. A1C 9.2%. Reports increased thirst and frequent urination.`
  },
  {
    title: 'Unspecified Heart Failure',
    note: `Patient with heart failure, presenting with dyspnea on exertion. Lower extremity edema noted. BNP 650. On furosemide and lisinopril.`
  },
  {
    title: 'Sepsis Without Organism',
    note: `Patient admitted with sepsis. Temperature 102.5F, WBC 18,000, lactate 2.8. Blood cultures pending. Started on broad-spectrum antibiotics.`
  }
];

export default function CDIQueryGeneratorPage() {
  const [apiKey, setApiKey] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [gapType, setGapType] = useState<string>('specificity');
  const [queryStyle, setQueryStyle] = useState<string>('open_ended');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const loadSample = () => {
    const sample = SAMPLE_SCENARIOS[Math.floor(Math.random() * SAMPLE_SCENARIOS.length)];
    setClinicalNote(sample.note);
    setResult(null);
    setError('');
  };

  const generateQuery = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!clinicalNote.trim() || clinicalNote.trim().length < 30) {
      setError('Please enter a clinical note (minimum 30 characters)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const request: CDIQueryRequest = {
        clinical_note: clinicalNote,
        gap_type: gapType as any,
        query_style: queryStyle as any
      };
      const response = await cdiAPI.generateQuery(request, apiKey);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Query generation failed');
    } finally {
      setLoading(false);
    }
  };

  const copyQuery = () => {
    if (result?.query) {
      navigator.clipboard.writeText(result.query);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <MessageSquare className="w-8 h-8 text-purple-600" />
          CDI Query Generator
        </h1>
        <p className="text-gray-600 mt-2">
          Generate compliant, physician-friendly CDI queries to clarify clinical documentation
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Clinical Note Input */}
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-purple-600" />
            Clinical Note
          </h2>
          <button
            onClick={loadSample}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
          >
            Load Sample
          </button>
        </div>
        <textarea
          value={clinicalNote}
          onChange={(e) => setClinicalNote(e.target.value)}
          className="w-full bg-white border border-gray-300 p-4 rounded text-sm min-h-[150px] focus:ring-2 focus:ring-purple-500"
          placeholder="Enter the clinical note or documentation excerpt..."
        />
      </div>

      {/* Query Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gap Type */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Gap Type</h3>
          <div className="space-y-3">
            {GAP_TYPES.map((type) => (
              <label
                key={type.value}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  gapType === type.value
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-purple-300'
                }`}
              >
                <input
                  type="radio"
                  name="gapType"
                  value={type.value}
                  checked={gapType === type.value}
                  onChange={(e) => setGapType(e.target.value)}
                  className="mt-1 text-purple-600"
                />
                <div>
                  <div className="font-medium text-gray-900">{type.label}</div>
                  <div className="text-sm text-gray-500">{type.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Query Style */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Query Style</h3>
          <div className="space-y-3">
            {QUERY_STYLES.map((style) => (
              <label
                key={style.value}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  queryStyle === style.value
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-purple-300'
                }`}
              >
                <input
                  type="radio"
                  name="queryStyle"
                  value={style.value}
                  checked={queryStyle === style.value}
                  onChange={(e) => setQueryStyle(e.target.value)}
                  className="mt-1 text-purple-600"
                />
                <div>
                  <div className="font-medium text-gray-900">{style.label}</div>
                  <div className="text-sm text-gray-500">{style.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Generate Button */}
      <div>
        <button
          onClick={generateQuery}
          disabled={loading || !apiKey || !clinicalNote.trim()}
          className="px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating Query...
            </>
          ) : (
            <>
              <MessageSquare className="w-5 h-5" />
              Generate CDI Query
            </>
          )}
        </button>
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

      {/* Result */}
      {result && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="bg-purple-600 p-4 text-white flex items-center justify-between">
            <h3 className="text-lg font-semibold">Generated CDI Query</h3>
            <button
              onClick={copyQuery}
              className="flex items-center gap-2 px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-sm transition-colors"
            >
              {copied ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copy Query
                </>
              )}
            </button>
          </div>
          <div className="p-6">
            {/* Query Text */}
            <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded-r mb-6">
              <p className="text-lg text-gray-800 italic">&ldquo;{result.query}&rdquo;</p>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-xs text-gray-500 uppercase">Gap Type</p>
                <p className="font-medium text-gray-900">{result.gap_type}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-xs text-gray-500 uppercase">Condition</p>
                <p className="font-medium text-gray-900">{result.condition}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <p className="text-xs text-gray-500 uppercase">Query Style</p>
                <p className="font-medium text-gray-900">{result.query_style}</p>
              </div>
            </div>

            {/* Compliance Notes */}
            {result.compliance_notes && result.compliance_notes.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold text-gray-900 mb-2">Compliance Notes</h4>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {result.compliance_notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Documentation Requirements */}
            {result.documentation_requirements && result.documentation_requirements.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Documentation Requirements</h4>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  {result.documentation_requirements.map((req, i) => (
                    <li key={i}>{req}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
