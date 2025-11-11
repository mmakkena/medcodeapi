'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export default function InteractiveAPITester() {
  const [clinicalNote, setClinicalNote] = useState(
    'Patient with right knee pain for 3 months. MRI shows meniscus tear. Underwent arthroscopic meniscectomy.'
  );
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const curlCommand = `curl -X POST "https://api.nuvii.ai/api/v1/clinical-coding" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "clinical_note": "${clinicalNote.substring(0, 80).replace(/"/g, '\\"')}...",
    "max_codes_per_type": 3,
    "use_llm": false
  }'`;

  const handleTest = async () => {
    setLoading(true);
    setResponse(null);

    // Simulate API call with clinical coding demo data
    setTimeout(() => {
      setResponse({
        clinical_note_summary: 'Patient with meniscus tear underwent arthroscopic meniscectomy',
        primary_diagnoses: [
          {
            code: 'M23.204',
            code_system: 'ICD10-CM',
            description: 'Derangement of medial meniscus, right knee',
            confidence_score: 0.92,
            explanation: 'Matched from: meniscus tear'
          },
          {
            code: 'M25.561',
            code_system: 'ICD10-CM',
            description: 'Pain in right knee',
            confidence_score: 0.88,
            explanation: 'Matched from: right knee pain'
          }
        ],
        procedures: [
          {
            code: '29881',
            code_system: 'CPT',
            description: 'Arthroscopy, knee, surgical; with meniscectomy',
            confidence_score: 0.95,
            explanation: 'Matched from: arthroscopic meniscectomy',
            facets: {
              body_region: 'lower_extremity',
              body_system: 'musculoskeletal',
              procedure_category: 'surgical',
              complexity_level: 'moderate',
              surgical_approach: 'endoscopic'
            }
          }
        ],
        total_suggestions: 3,
        processing_time_ms: 1650
      });
      setLoading(false);
    }, 1500);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(curlCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 space-y-4">
      {/* Input Section */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">
          Clinical Note
        </label>
        <textarea
          value={clinicalNote}
          onChange={(e) => setClinicalNote(e.target.value)}
          placeholder="Enter clinical note (e.g., patient presents with...)"
          rows={3}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-sm"
        />
        <button
          onClick={handleTest}
          disabled={loading || !clinicalNote || clinicalNote.length < 30}
          className="w-full px-6 py-2.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing...
            </span>
          ) : (
            'Get Code Suggestions'
          )}
        </button>
      </div>

      {/* cURL Command Display */}
      <div className="bg-gray-800 rounded-md p-4 relative">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 overflow-x-auto">
            <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap break-all">
              {curlCommand}
            </pre>
          </div>
          <button
            onClick={handleCopy}
            className="flex-shrink-0 p-2 hover:bg-gray-700 rounded-md transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <Check className="w-5 h-5 text-green-400" />
            ) : (
              <Copy className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Response Display */}
      {response && (
        <div className="bg-gray-800 rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300">AI Code Suggestions</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">{response.processing_time_ms}ms</span>
              <span className="text-xs text-green-400 font-mono">200 OK</span>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-gray-700/50 rounded p-2">
            <p className="text-xs text-gray-300 italic">{response.clinical_note_summary}</p>
          </div>

          {/* Primary Diagnoses */}
          {response.primary_diagnoses && response.primary_diagnoses.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">
                Diagnoses ({response.primary_diagnoses.length})
              </div>
              {response.primary_diagnoses.map((code: any, idx: number) => (
                <div key={idx} className="bg-blue-900/20 border-l-2 border-blue-500 rounded-r p-2 mb-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-sm font-bold text-white">{code.code}</span>
                    <span className="text-xs text-green-400">{Math.round(code.confidence_score * 100)}%</span>
                  </div>
                  <p className="text-xs text-gray-300">{code.description}</p>
                  {code.explanation && (
                    <p className="text-xs text-gray-400 italic mt-1">💡 {code.explanation}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Procedures */}
          {response.procedures && response.procedures.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-teal-400 uppercase tracking-wider mb-2">
                Procedures ({response.procedures.length})
              </div>
              {response.procedures.map((code: any, idx: number) => (
                <div key={idx} className="bg-teal-900/20 border-l-2 border-teal-500 rounded-r p-2 mb-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-sm font-bold text-white">{code.code}</span>
                    <span className="text-xs text-green-400">{Math.round(code.confidence_score * 100)}%</span>
                  </div>
                  <p className="text-xs text-gray-300 mb-2">{code.description}</p>

                  {/* Facets */}
                  {code.facets && (
                    <div className="flex flex-wrap gap-1 mb-1">
                      {code.facets.procedure_category && (
                        <span className="px-1.5 py-0.5 bg-purple-900/40 text-purple-300 rounded text-xs">
                          {code.facets.procedure_category}
                        </span>
                      )}
                      {code.facets.complexity_level && (
                        <span className="px-1.5 py-0.5 bg-orange-900/40 text-orange-300 rounded text-xs">
                          {code.facets.complexity_level}
                        </span>
                      )}
                      {code.facets.surgical_approach && (
                        <span className="px-1.5 py-0.5 bg-red-900/40 text-red-300 rounded text-xs">
                          {code.facets.surgical_approach}
                        </span>
                      )}
                    </div>
                  )}

                  {code.explanation && (
                    <p className="text-xs text-gray-400 italic mt-1">💡 {code.explanation}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {loading && !response && (
        <div className="bg-gray-800 rounded-md p-8 flex items-center justify-center">
          <div className="text-gray-400 flex items-center gap-3">
            <svg className="animate-spin h-5 h-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Analyzing clinical note...</span>
          </div>
        </div>
      )}
    </div>
  );
}
