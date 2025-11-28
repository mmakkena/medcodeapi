'use client';

import { useState } from 'react';
import {
  ClipboardCheck,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Stethoscope
} from 'lucide-react';
import { qualityAPI, HEDISRequest } from '@/lib/api';

interface MeasureResult {
  measure_id: string;
  measure_name: string;
  status: 'met' | 'not_met' | 'exclusion' | 'pending';
  eligible: boolean;
  documentation_found: string[];
  gaps: string[];
  suggested_actions: string[];
  query?: string;
}

interface HEDISResult {
  patient_summary: string;
  total_measures_evaluated: number;
  measures_met: number;
  measures_not_met: number;
  exclusions: number;
  measure_results: MeasureResult[];
  overall_compliance_rate: number;
  priority_actions: string[];
}

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' }
];

const SAMPLE_SCENARIOS = [
  {
    title: 'Diabetes Management',
    note: `65-year-old female with Type 2 diabetes. A1C 7.2% (last checked 2 months ago). Blood pressure 132/82. LDL 98 (on statin). Last retinal exam 14 months ago. Foot exam documented today - no abnormalities. On metformin and lisinopril.`,
    age: 65,
    gender: 'female',
    codes: ['E11.9', 'I10']
  },
  {
    title: 'Preventive Care Adult',
    note: `52-year-old male for annual wellness visit. Last colonoscopy 3 years ago. Up to date on flu vaccine (this year). Pneumonia vaccine not yet received. BMI 28. Blood pressure 128/78. Discussed colon cancer screening, breast cancer screening not applicable.`,
    age: 52,
    gender: 'male',
    codes: ['Z00.00']
  }
];

export default function HEDISEvaluationPage() {
  const [apiKey, setApiKey] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [patientAge, setPatientAge] = useState<number>(50);
  const [patientGender, setPatientGender] = useState<'male' | 'female'>('male');
  const [icd10Codes, setIcd10Codes] = useState<string[]>([]);
  const [newCode, setNewCode] = useState('');
  const [generateQueries, setGenerateQueries] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<HEDISResult | null>(null);
  const [error, setError] = useState('');

  const loadSample = () => {
    const sample = SAMPLE_SCENARIOS[Math.floor(Math.random() * SAMPLE_SCENARIOS.length)];
    setClinicalNote(sample.note);
    setPatientAge(sample.age);
    setPatientGender(sample.gender as 'male' | 'female');
    setIcd10Codes(sample.codes);
    setResult(null);
    setError('');
  };

  const addCode = () => {
    if (newCode.trim() && !icd10Codes.includes(newCode.trim().toUpperCase())) {
      setIcd10Codes([...icd10Codes, newCode.trim().toUpperCase()]);
      setNewCode('');
    }
  };

  const removeCode = (code: string) => {
    setIcd10Codes(icd10Codes.filter((c) => c !== code));
  };

  const evaluateHEDIS = async () => {
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
      const request: HEDISRequest = {
        clinical_note: clinicalNote,
        patient_age: patientAge,
        patient_gender: patientGender,
        icd10_codes: icd10Codes.length > 0 ? icd10Codes : undefined,
        generate_queries: generateQueries
      };
      const response = await qualityAPI.evaluateHEDIS(request, apiKey);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'met':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'not_met':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'exclusion':
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
      case 'pending':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'met': return 'bg-green-50 border-green-200';
      case 'not_met': return 'bg-red-50 border-red-200';
      case 'exclusion': return 'bg-gray-50 border-gray-200';
      case 'pending': return 'bg-yellow-50 border-yellow-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <ClipboardCheck className="w-8 h-8 text-teal-600" />
          HEDIS Evaluation
        </h1>
        <p className="text-gray-600 mt-2">
          Evaluate clinical documentation against HEDIS quality measures
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        />
      </div>

      {/* Patient Info & Clinical Note */}
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-teal-600" />
            Patient Information
          </h2>
          <button
            onClick={loadSample}
            className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 transition-colors text-sm"
          >
            Load Sample
          </button>
        </div>

        {/* Patient Demographics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Patient Age</label>
            <input
              type="number"
              value={patientAge}
              onChange={(e) => setPatientAge(parseInt(e.target.value) || 0)}
              min={0}
              max={120}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Patient Gender</label>
            <div className="flex gap-4">
              {GENDER_OPTIONS.map((option) => (
                <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="gender"
                    value={option.value}
                    checked={patientGender === option.value}
                    onChange={(e) => setPatientGender(e.target.value as 'male' | 'female')}
                    className="text-teal-600"
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* ICD-10 Codes */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">ICD-10 Codes (Optional)</label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addCode()}
              placeholder="Add ICD-10 code (e.g., E11.9)"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-teal-500"
            />
            <button
              onClick={addCode}
              className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 transition-colors"
            >
              Add
            </button>
          </div>
          {icd10Codes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {icd10Codes.map((code) => (
                <span
                  key={code}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-teal-100 text-teal-700 rounded-full text-sm"
                >
                  {code}
                  <button
                    onClick={() => removeCode(code)}
                    className="hover:text-teal-900"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Clinical Note */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Clinical Note</label>
          <textarea
            value={clinicalNote}
            onChange={(e) => setClinicalNote(e.target.value)}
            className="w-full bg-white border border-gray-300 p-4 rounded text-sm min-h-[200px] focus:ring-2 focus:ring-teal-500"
            placeholder="Enter clinical note for HEDIS evaluation..."
          />
        </div>

        {/* Options */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={generateQueries}
              onChange={(e) => setGenerateQueries(e.target.checked)}
              className="rounded text-teal-600"
            />
            <span className="text-sm text-gray-700">Generate care gap queries</span>
          </label>
        </div>

        {/* Evaluate Button */}
        <div>
          <button
            onClick={evaluateHEDIS}
            disabled={loading || !apiKey || !clinicalNote.trim()}
            className="px-6 py-3 bg-teal-600 text-white rounded-md hover:bg-teal-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Evaluating...
              </>
            ) : (
              <>
                <ClipboardCheck className="w-5 h-5" />
                Evaluate HEDIS Measures
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
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Evaluation Summary</h3>
            <p className="text-gray-600 mb-4">{result.patient_summary}</p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-700">{result.total_measures_evaluated}</div>
                <p className="text-xs text-gray-500">Measures Evaluated</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{result.measures_met}</div>
                <p className="text-xs text-gray-500">Met</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{result.measures_not_met}</div>
                <p className="text-xs text-gray-500">Not Met</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-500">{result.exclusions}</div>
                <p className="text-xs text-gray-500">Exclusions</p>
              </div>
              <div className="text-center p-4 bg-teal-50 rounded-lg">
                <div className="text-2xl font-bold text-teal-600">{result.overall_compliance_rate}%</div>
                <p className="text-xs text-gray-500">Compliance</p>
              </div>
            </div>
          </div>

          {/* Priority Actions */}
          {result.priority_actions && result.priority_actions.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Priority Actions</h3>
              <ul className="space-y-2">
                {result.priority_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-700">
                    <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Measure Results */}
          {result.measure_results && result.measure_results.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-teal-600 p-4 text-white">
                <h3 className="text-lg font-semibold">
                  Measure Results ({result.measure_results.length})
                </h3>
              </div>
              <div className="p-4 space-y-4">
                {result.measure_results.map((measure, index) => (
                  <div key={index} className={`border rounded-lg p-4 ${getStatusBg(measure.status)}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(measure.status)}
                        <div>
                          <h4 className="font-semibold text-gray-900">{measure.measure_name}</h4>
                          <span className="text-xs text-gray-500">{measure.measure_id}</span>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        measure.status === 'met' ? 'bg-green-100 text-green-700' :
                        measure.status === 'not_met' ? 'bg-red-100 text-red-700' :
                        measure.status === 'exclusion' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {measure.status.toUpperCase().replace('_', ' ')}
                      </span>
                    </div>

                    {measure.documentation_found.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-500 uppercase mb-1">Documentation Found</p>
                        <ul className="list-disc list-inside text-sm text-gray-600">
                          {measure.documentation_found.map((doc, i) => (
                            <li key={i}>{doc}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {measure.gaps.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-500 uppercase mb-1">Gaps Identified</p>
                        <ul className="list-disc list-inside text-sm text-red-600">
                          {measure.gaps.map((gap, i) => (
                            <li key={i}>{gap}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {measure.suggested_actions.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-500 uppercase mb-1">Suggested Actions</p>
                        <ul className="list-disc list-inside text-sm text-gray-600">
                          {measure.suggested_actions.map((action, i) => (
                            <li key={i}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {measure.query && (
                      <div className="bg-white p-3 rounded border border-gray-200">
                        <p className="text-xs text-gray-500 mb-1">Care Gap Query:</p>
                        <p className="text-sm text-gray-800 italic">&ldquo;{measure.query}&rdquo;</p>
                      </div>
                    )}
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
