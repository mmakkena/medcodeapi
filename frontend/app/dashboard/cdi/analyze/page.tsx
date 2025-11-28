'use client';

import { useState } from 'react';
import {
  FileSearch,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Stethoscope,
  ClipboardList,
  Lightbulb
} from 'lucide-react';
import { cdiAPI } from '@/lib/api';

interface DocumentationGap {
  gap_type: string;
  condition: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  suggested_query?: string;
  clinical_indicators?: string[];
}

interface ClinicalEntity {
  text: string;
  type: string;
  confidence: number;
  icd10_codes?: Array<{ code: string; description: string }>;
}

interface AnalysisResult {
  summary: string;
  documentation_gaps: DocumentationGap[];
  clinical_entities: ClinicalEntity[];
  coding_suggestions: Array<{
    code: string;
    description: string;
    confidence: number;
    rationale: string;
  }>;
  overall_completeness_score: number;
}

const SAMPLE_NOTES = [
  {
    title: 'Diabetes with Complications',
    note: `Patient is a 65-year-old male with diabetes presenting for follow-up. A1C is 8.9%. Patient reports numbness and tingling in both feet. Blood pressure 145/95. Creatinine elevated at 1.8. Patient also complains of blurry vision. Currently on metformin 1000mg BID and lisinopril.`
  },
  {
    title: 'Heart Failure Management',
    note: `72-year-old female with history of heart failure presents with increased shortness of breath and lower extremity edema. Patient gained 8 pounds over the past week. BNP elevated at 850. Chest X-ray shows cardiomegaly with bilateral pleural effusions. Currently on furosemide 40mg daily. EF was 35% on last echo.`
  },
  {
    title: 'COPD Exacerbation',
    note: `68-year-old male with history of COPD presents with worsening dyspnea and productive cough with yellow sputum for 3 days. O2 sat 89% on room air. Wheezing noted bilaterally. History of 40 pack-year smoking, quit 5 years ago. Currently using albuterol PRN and tiotropium daily.`
  }
];

export default function CDIAnalyzePage() {
  const [apiKey, setApiKey] = useState('');
  const [clinicalNote, setClinicalNote] = useState('');
  const [noteTitle, setNoteTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const [includeGaps, setIncludeGaps] = useState(true);
  const [includeEntities, setIncludeEntities] = useState(true);
  const [includeSuggestions, setIncludeSuggestions] = useState(true);

  const loadSampleNote = () => {
    const sample = SAMPLE_NOTES[Math.floor(Math.random() * SAMPLE_NOTES.length)];
    setClinicalNote(sample.note);
    setNoteTitle(sample.title);
    setResults(null);
    setError('');
  };

  const analyzeNote = async () => {
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
      const response = await cdiAPI.analyzeNote(
        {
          clinical_note: clinicalNote,
          include_gaps: includeGaps,
          include_entities: includeEntities,
          include_suggestions: includeSuggestions
        },
        apiKey
      );
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200';
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
          <FileSearch className="w-8 h-8 text-blue-600" />
          Clinical Note Analysis
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze clinical notes to identify documentation gaps, extract entities, and get coding suggestions
        </p>
      </div>

      {/* API Key Input */}
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

      {/* Clinical Note Input */}
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-blue-600" />
            {noteTitle || 'Clinical Note'}
          </h2>
          <button
            onClick={loadSampleNote}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
          >
            Load Sample Note
          </button>
        </div>
        <textarea
          value={clinicalNote}
          onChange={(e) => setClinicalNote(e.target.value)}
          className="w-full bg-white border border-gray-300 p-4 rounded text-sm min-h-[200px] focus:ring-2 focus:ring-blue-500"
          placeholder="Enter or paste clinical note text here..."
        />

        {/* Options */}
        <div className="mt-4 flex flex-wrap gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeGaps}
              onChange={(e) => setIncludeGaps(e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-gray-700">Documentation Gaps</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeEntities}
              onChange={(e) => setIncludeEntities(e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-gray-700">Clinical Entities</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={includeSuggestions}
              onChange={(e) => setIncludeSuggestions(e.target.checked)}
              className="rounded text-blue-600"
            />
            <span className="text-sm text-gray-700">Coding Suggestions</span>
          </label>
        </div>

        {/* Privacy Notice */}
        <div className="mt-4 flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <AlertCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-blue-800">
            <strong>Privacy Notice:</strong> Do not enter Protected Health Information (PHI). Remove all patient identifiers before analysis.
          </p>
        </div>

        {/* Analyze Button */}
        <div className="mt-4">
          <button
            onClick={analyzeNote}
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
                <FileSearch className="w-5 h-5" />
                Analyze Note
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
      {results && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Analysis Summary</h3>
                <p className="text-gray-600 mt-2">{results.summary}</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">
                  {results.overall_completeness_score}%
                </div>
                <p className="text-sm text-gray-500">Completeness Score</p>
              </div>
            </div>
          </div>

          {/* Documentation Gaps */}
          {results.documentation_gaps && results.documentation_gaps.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-orange-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Documentation Gaps ({results.documentation_gaps.length})
                </h3>
              </div>
              <div className="p-4 space-y-4">
                {results.documentation_gaps.map((gap, index) => (
                  <div key={index} className="border-l-4 border-orange-400 bg-orange-50 p-4 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(gap.severity)}`}>
                          {gap.severity.toUpperCase()}
                        </span>
                        <span className="ml-2 text-xs text-gray-500">{gap.gap_type}</span>
                      </div>
                    </div>
                    <h4 className="font-semibold text-gray-900 mt-2">{gap.condition}</h4>
                    <p className="text-sm text-gray-700 mt-1">{gap.description}</p>
                    {gap.suggested_query && (
                      <div className="mt-3 bg-white p-3 rounded border border-orange-200">
                        <p className="text-xs text-gray-500 mb-1">Suggested Query:</p>
                        <p className="text-sm text-gray-800 italic">&ldquo;{gap.suggested_query}&rdquo;</p>
                      </div>
                    )}
                    {gap.clinical_indicators && gap.clinical_indicators.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {gap.clinical_indicators.map((indicator, i) => (
                          <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            {indicator}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clinical Entities */}
          {results.clinical_entities && results.clinical_entities.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-blue-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <ClipboardList className="w-5 h-5" />
                  Clinical Entities ({results.clinical_entities.length})
                </h3>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {results.clinical_entities.map((entity, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900">{entity.text}</span>
                        <span className="text-xs text-gray-500">{(entity.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded mt-1 inline-block">
                        {entity.type}
                      </span>
                      {entity.icd10_codes && entity.icd10_codes.length > 0 && (
                        <div className="mt-2 text-xs text-gray-600">
                          {entity.icd10_codes.map((code, i) => (
                            <div key={i}>{code.code}: {code.description}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Coding Suggestions */}
          {results.coding_suggestions && results.coding_suggestions.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-green-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Coding Suggestions ({results.coding_suggestions.length})
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {results.coding_suggestions.map((suggestion, index) => (
                  <div key={index} className="border-l-4 border-green-400 bg-green-50 p-4 rounded-r">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="font-bold text-lg text-gray-900">{suggestion.code}</span>
                        <p className="text-gray-700 text-sm">{suggestion.description}</p>
                      </div>
                      <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-sm font-medium">
                        {(suggestion.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2 flex items-start gap-1">
                      <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-green-600" />
                      {suggestion.rationale}
                    </p>
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
