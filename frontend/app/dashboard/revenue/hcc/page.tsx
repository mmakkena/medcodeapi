'use client';

import { useState } from 'react';
import {
  TrendingUp,
  Loader2,
  AlertTriangle,
  Plus,
  X,
  DollarSign
} from 'lucide-react';
import { revenueAPI } from '@/lib/api';

interface HCCResult {
  model_version: string;
  total_raf_score: number;
  hcc_codes: Array<{
    hcc_code: string;
    hcc_description: string;
    icd10_code: string;
    icd10_description: string;
    raf_value: number;
    hierarchy_notes?: string;
  }>;
  hierarchies_applied: string[];
  estimated_annual_value: number;
  opportunities: Array<{
    condition: string;
    potential_hcc: string;
    raf_value: number;
    clinical_indicators: string[];
  }>;
}

const MODEL_VERSIONS = [
  { value: 'v24', label: 'CMS-HCC V24 (2024)' },
  { value: 'v28', label: 'CMS-HCC V28 (2026)' },
  { value: 'rxhcc', label: 'RxHCC' }
];

const COMMON_DIAGNOSES = [
  'E11.9 - Type 2 diabetes without complications',
  'E11.65 - Type 2 diabetes with hyperglycemia',
  'E11.22 - Type 2 diabetes with CKD',
  'I50.9 - Heart failure, unspecified',
  'I50.22 - Chronic systolic heart failure',
  'J44.1 - COPD with acute exacerbation',
  'N18.3 - CKD stage 3',
  'F32.9 - Major depressive disorder'
];

export default function HCCAnalysisPage() {
  const [apiKey, setApiKey] = useState('');
  const [diagnoses, setDiagnoses] = useState<string[]>([]);
  const [newDiagnosis, setNewDiagnosis] = useState('');
  const [modelVersion, setModelVersion] = useState('v24');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<HCCResult | null>(null);
  const [error, setError] = useState('');

  const addDiagnosis = () => {
    if (newDiagnosis.trim() && !diagnoses.includes(newDiagnosis.trim())) {
      setDiagnoses([...diagnoses, newDiagnosis.trim()]);
      setNewDiagnosis('');
    }
  };

  const removeDiagnosis = (index: number) => {
    setDiagnoses(diagnoses.filter((_, i) => i !== index));
  };

  const addCommonDiagnosis = (diagnosis: string) => {
    const code = diagnosis.split(' - ')[0];
    if (!diagnoses.includes(code)) {
      setDiagnoses([...diagnoses, code]);
    }
  };

  const analyzeHCC = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (diagnoses.length === 0) {
      setError('Please add at least one diagnosis');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await revenueAPI.analyzeHCC(diagnoses, modelVersion, apiKey);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-purple-600" />
          HCC Risk Adjustment Analysis
        </h1>
        <p className="text-gray-600 mt-2">
          Calculate RAF scores and identify HCC opportunities for risk-adjusted payment models
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

      {/* Diagnosis Input */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Diagnoses (ICD-10 Codes)</h2>

        {/* Add Diagnosis */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newDiagnosis}
            onChange={(e) => setNewDiagnosis(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addDiagnosis()}
            placeholder="Enter ICD-10 code (e.g., E11.65)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
          />
          <button
            onClick={addDiagnosis}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
        </div>

        {/* Current Diagnoses */}
        {diagnoses.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {diagnoses.map((diagnosis, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
              >
                {diagnosis}
                <button
                  onClick={() => removeDiagnosis(index)}
                  className="hover:text-purple-900"
                >
                  <X className="w-4 h-4" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Common Diagnoses */}
        <div>
          <p className="text-sm text-gray-500 mb-2">Quick add common diagnoses:</p>
          <div className="flex flex-wrap gap-2">
            {COMMON_DIAGNOSES.map((diagnosis) => (
              <button
                key={diagnosis}
                onClick={() => addCommonDiagnosis(diagnosis)}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-purple-100 hover:text-purple-700 transition-colors"
              >
                {diagnosis}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Model Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">HCC Model Version</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {MODEL_VERSIONS.map((model) => (
            <label
              key={model.value}
              className={`flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors ${
                modelVersion === model.value
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-200 hover:border-purple-300'
              }`}
            >
              <input
                type="radio"
                name="model"
                value={model.value}
                checked={modelVersion === model.value}
                onChange={(e) => setModelVersion(e.target.value)}
                className="text-purple-600"
              />
              <span className="font-medium">{model.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Analyze Button */}
      <div>
        <button
          onClick={analyzeHCC}
          disabled={loading || !apiKey || diagnoses.length === 0}
          className="px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Calculating...
            </>
          ) : (
            <>
              <TrendingUp className="w-5 h-5" />
              Calculate RAF Score
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

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center bg-purple-50 p-6 rounded-lg">
                <div className="text-4xl font-bold text-purple-600">{result.total_raf_score.toFixed(3)}</div>
                <p className="text-sm text-gray-500 mt-1">Total RAF Score</p>
              </div>
              <div className="text-center bg-green-50 p-6 rounded-lg">
                <div className="text-4xl font-bold text-green-600">
                  ${result.estimated_annual_value.toLocaleString()}
                </div>
                <p className="text-sm text-gray-500 mt-1">Est. Annual Value</p>
              </div>
              <div className="text-center bg-blue-50 p-6 rounded-lg">
                <div className="text-4xl font-bold text-blue-600">{result.hcc_codes.length}</div>
                <p className="text-sm text-gray-500 mt-1">HCCs Captured</p>
              </div>
            </div>
          </div>

          {/* HCC Codes */}
          {result.hcc_codes.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-purple-600 p-4 text-white">
                <h3 className="text-lg font-semibold">HCC Codes ({result.hcc_codes.length})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">HCC</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ICD-10</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">RAF Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.hcc_codes.map((hcc, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-purple-700">{hcc.hcc_code}</td>
                        <td className="px-4 py-3 text-sm text-gray-700">{hcc.hcc_description}</td>
                        <td className="px-4 py-3">
                          <span className="text-sm font-medium">{hcc.icd10_code}</span>
                          <span className="text-xs text-gray-500 block">{hcc.icd10_description}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="font-bold text-green-600">+{hcc.raf_value.toFixed(3)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Hierarchies Applied */}
          {result.hierarchies_applied.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-3">Hierarchies Applied</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                {result.hierarchies_applied.map((hierarchy, i) => (
                  <li key={i}>{hierarchy}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Opportunities */}
          {result.opportunities && result.opportunities.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-orange-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Additional HCC Opportunities ({result.opportunities.length})
                </h3>
              </div>
              <div className="p-4 space-y-4">
                {result.opportunities.map((opp, index) => (
                  <div key={index} className="border-l-4 border-orange-400 bg-orange-50 p-4 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold text-gray-900">{opp.condition}</h4>
                        <p className="text-sm text-gray-600">Potential HCC: {opp.potential_hcc}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-orange-600">+{opp.raf_value.toFixed(3)}</div>
                        <p className="text-xs text-gray-500">RAF Value</p>
                      </div>
                    </div>
                    <div className="mt-2">
                      <p className="text-xs text-gray-500">Clinical Indicators:</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {opp.clinical_indicators.map((indicator, i) => (
                          <span key={i} className="px-2 py-0.5 bg-white text-gray-600 rounded text-xs border">
                            {indicator}
                          </span>
                        ))}
                      </div>
                    </div>
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
