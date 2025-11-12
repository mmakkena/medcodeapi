'use client';

import { useState } from 'react';
import { Sparkles, Loader2, Code2, Stethoscope, AlertCircle } from 'lucide-react';

interface CodeSuggestion {
  code: string;
  code_system: string;
  description: string;
  confidence_score: number;
  similarity_score: number;
  suggestion_type: string;
  explanation?: string;
  facets?: {
    body_region?: string;
    body_system?: string;
    procedure_category?: string;
    complexity_level?: string;
    service_location?: string;
    em_level?: string;
    em_patient_type?: string;
    imaging_modality?: string;
    surgical_approach?: string;
    is_major_surgery?: boolean;
    uses_contrast?: boolean;
    is_bilateral?: boolean;
    requires_modifier?: boolean;
  };
}

interface ClinicalCodingResponse {
  clinical_note_summary: string;
  primary_diagnoses: CodeSuggestion[];
  secondary_diagnoses: CodeSuggestion[];
  procedures: CodeSuggestion[];
  total_suggestions: number;
  processing_time_ms: number;
}

const SAMPLE_NOTES = [
  {
    title: 'Acute MI with Intervention',
    note: `Patient presents with acute chest pain radiating to left arm for 2 hours. History of hypertension and hyperlipidemia. Blood pressure 165/95. EKG shows ST elevation in leads II, III, aVF. Troponin elevated at 2.5. Diagnosed with acute ST elevation myocardial infarction (STEMI) involving the right coronary artery. Emergency cardiac catheterization performed with placement of drug-eluting stent to right coronary artery. Patient stabilized and transferred to ICU.`
  },
  {
    title: 'Type 2 Diabetes Management',
    note: `Patient with type 2 diabetes mellitus presents for follow-up. A1C today is 8.2%. Patient reports increased thirst and polyuria. Currently taking metformin 1000mg twice daily. Blood pressure 145/92. Foot exam shows no neuropathy. Retinal exam normal. Diagnosed with uncontrolled type 2 diabetes with hyperglycemia. Increased metformin to 1500mg twice daily. Ordered comprehensive metabolic panel and lipid panel.`
  },
  {
    title: 'Knee Surgery',
    note: `Patient with right knee pain and locking for 3 months. MRI shows bucket handle tear of medial meniscus. Patient underwent arthroscopic partial medial meniscectomy under general anesthesia. Procedure performed successfully without complications. Post-op instructions given for physical therapy and gradual return to activities.`
  },
  {
    title: 'Pneumonia',
    note: `Patient presents with cough, fever of 102°F, and difficulty breathing for 3 days. Chest X-ray shows right lower lobe infiltrate consistent with pneumonia. Diagnosed with community-acquired pneumonia. Started on azithromycin 500mg and advised to rest, increase fluids, and follow up in 5 days.`
  },
  {
    title: 'Hypertension Follow-up',
    note: `Patient with history of essential hypertension presents for follow-up. Current blood pressure 165/98. Patient has been non-compliant with lisinopril. Complains of headaches. Labs show normal renal function. Counseled on importance of medication compliance. Increased lisinopril dose to 20mg daily. Ordered lipid panel.`
  },
  {
    title: 'Asthma Exacerbation',
    note: `Patient with history of asthma presents with wheezing and shortness of breath for 2 days. Using albuterol inhaler every 2 hours. Exam reveals decreased breath sounds with expiratory wheezes bilaterally. Peak flow 60% of predicted. Diagnosed with acute asthma exacerbation. Given nebulizer treatment with albuterol and ipratropium. Prescribed prednisone 40mg daily for 5 days. Patient improved after treatment.`
  }
];

export default function PlaygroundPage() {
  const [apiKey, setApiKey] = useState('');
  const [currentNote, setCurrentNote] = useState('');
  const [noteTitle, setNoteTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ClinicalCodingResponse | null>(null);
  const [error, setError] = useState('');
  const [useLLM, setUseLLM] = useState(false); // Default to semantic-only (fast & free)

  const generateRandomNote = () => {
    const randomNote = SAMPLE_NOTES[Math.floor(Math.random() * SAMPLE_NOTES.length)];
    setCurrentNote(randomNote.note);
    setNoteTitle(randomNote.title);
    setResults(null);
    setError('');
  };

  const analyzeClinicalNote = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    if (!currentNote.trim() || currentNote.trim().length < 50) {
      setError('Please enter a clinical note (minimum 50 characters)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      let baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';
      if (!baseUrl.endsWith('/api/v1')) {
        baseUrl = `${baseUrl}/api/v1`;
      }

      const url = `${baseUrl}/clinical-coding`;

      console.log('Calling Clinical Coding API:', {
        url,
        noteLength: currentNote.length,
        useLLM
      });

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey.trim()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          clinical_note: currentNote,
          max_codes_per_type: 3,
          include_explanations: true,
          use_llm: useLLM
        })
      });

      if (!response.ok) {
        const errorBody = await response.text();
        console.error('Clinical Coding API failed:', { status: response.status, errorBody });
        throw new Error(`API request failed (${response.status}): ${errorBody}`);
      }

      const data = await response.json();
      console.log('API Response:', {
        total_suggestions: data.total_suggestions,
        processing_time: data.processing_time_ms,
        primary_dx: data.primary_diagnoses?.length || 0,
        secondary_dx: data.secondary_diagnoses?.length || 0,
        procedures: data.procedures?.length || 0
      });

      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze clinical note. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setCurrentNote('');
    setNoteTitle('');
    setResults(null);
    setError('');
  };

  // Format facet values for display
  const formatFacetValue = (value: string | boolean | undefined): string => {
    if (value === undefined) return '';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';

    // Convert snake_case to Title Case
    return value
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get facet badge color based on type
  const getFacetColor = (facetType: string): string => {
    const colorMap: Record<string, string> = {
      procedure_category: 'bg-purple-100 text-purple-700 border-purple-200',
      complexity_level: 'bg-orange-100 text-orange-700 border-orange-200',
      service_location: 'bg-blue-100 text-blue-700 border-blue-200',
      body_region: 'bg-green-100 text-green-700 border-green-200',
      body_system: 'bg-cyan-100 text-cyan-700 border-cyan-200',
      em_level: 'bg-indigo-100 text-indigo-700 border-indigo-200',
      imaging_modality: 'bg-pink-100 text-pink-700 border-pink-200',
      surgical_approach: 'bg-red-100 text-red-700 border-red-200'
    };
    return colorMap[facetType] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const CodeCard = ({ code, type }: { code: CodeSuggestion; type: 'primary' | 'secondary' | 'procedure' }) => {
    const colorClasses = {
      primary: 'border-blue-500 bg-blue-50',
      secondary: 'border-yellow-500 bg-yellow-50',
      procedure: 'border-teal-500 bg-teal-50'
    };

    const badgeClasses = {
      primary: 'bg-blue-100 text-blue-700',
      secondary: 'bg-yellow-100 text-yellow-700',
      procedure: 'bg-teal-100 text-teal-700'
    };

    return (
      <div className={`border-l-4 ${colorClasses[type]} p-4 rounded-r hover:shadow-md transition-shadow`}>
        <div className="flex items-start justify-between mb-2">
          <div>
            <span className="font-bold text-lg text-gray-900">{code.code}</span>
            <span className="ml-2 text-xs text-gray-500 px-2 py-1 bg-white rounded-full border border-gray-200">
              {code.code_system}
            </span>
          </div>
          <span className={`${badgeClasses[type]} px-3 py-1 rounded-full text-xs font-semibold`}>
            {(code.confidence_score * 100).toFixed(0)}% confidence
          </span>
        </div>
        <p className="text-gray-700 text-sm mb-2">{code.description}</p>

        {/* Facets Display for Procedures */}
        {type === 'procedure' && code.facets && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex flex-wrap gap-1.5">
              {code.facets.procedure_category && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('procedure_category')}`}>
                  {formatFacetValue(code.facets.procedure_category)}
                </span>
              )}
              {code.facets.complexity_level && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('complexity_level')}`}>
                  {formatFacetValue(code.facets.complexity_level)}
                </span>
              )}
              {code.facets.service_location && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('service_location')}`}>
                  {formatFacetValue(code.facets.service_location)}
                </span>
              )}
              {code.facets.body_region && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('body_region')}`}>
                  {formatFacetValue(code.facets.body_region)}
                </span>
              )}
              {code.facets.body_system && code.facets.body_system !== 'not_applicable' && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('body_system')}`}>
                  {formatFacetValue(code.facets.body_system)}
                </span>
              )}
              {code.facets.em_level && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('em_level')}`}>
                  E/M: {formatFacetValue(code.facets.em_level)}
                </span>
              )}
              {code.facets.em_patient_type && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('em_level')}`}>
                  {formatFacetValue(code.facets.em_patient_type)}
                </span>
              )}
              {code.facets.imaging_modality && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('imaging_modality')}`}>
                  {formatFacetValue(code.facets.imaging_modality).toUpperCase()}
                </span>
              )}
              {code.facets.surgical_approach && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getFacetColor('surgical_approach')}`}>
                  {formatFacetValue(code.facets.surgical_approach)}
                </span>
              )}
              {code.facets.is_major_surgery && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium border bg-red-100 text-red-700 border-red-200">
                  Major Surgery
                </span>
              )}
              {code.facets.uses_contrast && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-700 border-yellow-200">
                  With Contrast
                </span>
              )}
            </div>
          </div>
        )}

        {code.explanation && (
          <p className="text-xs text-gray-600 italic flex items-start gap-1 mt-2 pt-2 border-t border-gray-200">
            <span className="flex-shrink-0">💡</span>
            <span>{code.explanation}</span>
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-nuvii-blue" />
          AI Clinical Coding Playground
        </h1>
        <p className="text-gray-600 mt-2">
          Analyze clinical notes with AI to automatically extract and suggest ICD-10 diagnosis codes and CPT/HCPCS procedure codes
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nuvii-blue focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-2">
          Get your API key from the <a href="/dashboard/api-keys" className="text-nuvii-blue hover:underline">API Keys</a> page
        </p>
      </div>

      {/* Clinical Note Input */}
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-nuvii-blue" />
            {noteTitle || 'Clinical Note'}
          </h2>
          <button
            onClick={generateRandomNote}
            className="px-4 py-2 bg-nuvii-blue text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            Random Example
          </button>
        </div>
        <textarea
          value={currentNote}
          onChange={(e) => setCurrentNote(e.target.value)}
          className="w-full bg-white border-l-4 border-nuvii-blue p-4 rounded text-sm text-gray-700 min-h-[200px] max-h-96 resize-y focus:outline-none focus:ring-2 focus:ring-nuvii-blue"
          placeholder="Enter or paste clinical note text here... or click 'Random Example' to try a sample."
        />

        {/* Privacy Notice */}
        <div className="mt-3 flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <AlertCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-blue-800">
            <strong>Privacy Notice:</strong> Do not enter Protected Health Information (PHI). Remove all patient identifiers including names, dates, addresses, and other identifying information before testing.
          </p>
        </div>

        {/* Mode Selection - Hidden for now */}
        <div className="hidden mt-4 p-4 bg-white border border-gray-200 rounded-md">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={useLLM}
              onChange={(e) => setUseLLM(e.target.checked)}
              className="mt-1 w-4 h-4 text-nuvii-blue rounded focus:ring-2 focus:ring-nuvii-blue"
            />
            <div className="flex-1">
              <div className="font-medium text-gray-900">Use LLM Mode (Claude 3.5 Sonnet)</div>
              <div className="text-xs text-gray-600 mt-1">
                <strong>Checked:</strong> 90-95% accuracy, ~2-4 seconds, ~$0.005/request (uses AI for entity extraction)<br/>
                <strong>Unchecked (default):</strong> 80-85% accuracy, ~1-2 seconds, $0/request (pure semantic search)
              </div>
            </div>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="mt-4 flex gap-3">
          <button
            onClick={analyzeClinicalNote}
            disabled={loading || !apiKey || !currentNote.trim() || currentNote.trim().length < 50}
            className="px-6 py-3 bg-nuvii-blue text-white rounded-md hover:bg-blue-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing{useLLM ? ' with AI' : ''}...
              </>
            ) : (
              <>
                <Code2 className="w-5 h-5" />
                Analyze & Suggest Codes
              </>
            )}
          </button>
          <button
            onClick={clearAll}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors font-medium"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-yellow-800 font-medium">Error</p>
            <p className="text-yellow-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary Header */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Clinical Note Summary</h3>
                <p className="text-gray-700 italic">{results.clinical_note_summary}</p>
              </div>
              <div className="text-right ml-4">
                <div className="text-2xl font-bold text-nuvii-blue">{results.total_suggestions}</div>
                <div className="text-xs text-gray-500">code suggestions</div>
                <div className="text-xs text-gray-400 mt-1">{results.processing_time_ms}ms</div>
              </div>
            </div>
          </div>

          {/* Primary Diagnoses */}
          {results.primary_diagnoses && results.primary_diagnoses.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-blue-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center justify-between">
                  <span>Primary Diagnoses (ICD-10-CM)</span>
                  <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                    {results.primary_diagnoses.length}
                  </span>
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {results.primary_diagnoses.map((code, index) => (
                  <CodeCard key={index} code={code} type="primary" />
                ))}
              </div>
            </div>
          )}

          {/* Procedures */}
          {results.procedures && results.procedures.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-teal-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center justify-between">
                  <span>Procedures (CPT/HCPCS)</span>
                  <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                    {results.procedures.length}
                  </span>
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {results.procedures.map((code, index) => (
                  <CodeCard key={index} code={code} type="procedure" />
                ))}
              </div>
            </div>
          )}

          {/* Secondary Diagnoses */}
          {results.secondary_diagnoses && results.secondary_diagnoses.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-yellow-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center justify-between">
                  <span>Secondary Diagnoses / Comorbidities (ICD-10-CM)</span>
                  <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                    {results.secondary_diagnoses.length}
                  </span>
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {results.secondary_diagnoses.map((code, index) => (
                  <CodeCard key={index} code={code} type="secondary" />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
