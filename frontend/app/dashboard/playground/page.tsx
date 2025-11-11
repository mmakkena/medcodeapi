'use client';

import { useState } from 'react';
import { Sparkles, Loader2, Code2, Stethoscope, AlertCircle } from 'lucide-react';

interface CodeResult {
  code_info: {
    code: string;
    description: string;
    code_system?: string;
  };
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
  } | null;
  similarity: number;
}

interface SearchResults {
  results: CodeResult[];
  total_results?: number;
  search_time_ms?: number;
}

const SAMPLE_NOTES = [
  {
    title: 'Type 2 Diabetes',
    note: `Patient with type 2 diabetes mellitus. Currently taking metformin. Blood sugar levels have been elevated. Complains of increased thirst and frequent urination.`
  },
  {
    title: 'Chest Pain',
    note: `Patient presents with acute chest pain radiating to left arm. Shortness of breath and sweating. History of hypertension. EKG shows ST elevation.`
  },
  {
    title: 'Knee Pain',
    note: `Right knee pain with swelling for 2 weeks. Pain worse with movement. Possible meniscus tear. X-ray shows mild arthritis.`
  },
  {
    title: 'Hypertension',
    note: `High blood pressure at 160/95. Patient not taking medications. Complains of headaches. Will start antihypertensive therapy.`
  },
  {
    title: 'Pneumonia',
    note: `Cough with fever for 3 days. Difficulty breathing. Chest X-ray shows right lower lobe infiltrate. Diagnosed with community-acquired pneumonia.`
  },
  {
    title: 'Asthma',
    note: `Wheezing and shortness of breath. Using albuterol inhaler frequently. History of asthma. Lung sounds with expiratory wheezes.`
  },
  {
    title: 'Urinary Tract Infection',
    note: `Painful urination with increased frequency. Fever and lower abdominal pain. Urinalysis positive for bacteria. UTI diagnosis.`
  },
  {
    title: 'Migraine Headache',
    note: `Severe throbbing headache with nausea and light sensitivity. History of migraines. Pain on left side of head.`
  }
];

// Format facet values for display
const formatFacetValue = (value: string | boolean | undefined | null): string => {
  if (value === null || value === undefined) return '';
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

export default function PlaygroundPage() {
  const [apiKey, setApiKey] = useState('');
  const [currentNote, setCurrentNote] = useState('');
  const [noteTitle, setNoteTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [icd10Results, setIcd10Results] = useState<SearchResults | null>(null);
  const [procedureResults, setProcedureResults] = useState<SearchResults | null>(null);
  const [error, setError] = useState('');

  const generateRandomNote = () => {
    const randomNote = SAMPLE_NOTES[Math.floor(Math.random() * SAMPLE_NOTES.length)];
    setCurrentNote(randomNote.note);
    setNoteTitle(randomNote.title);
    setIcd10Results(null);
    setProcedureResults(null);
    setError('');
  };

  const searchCodes = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    if (!currentNote.trim()) {
      setError('Please generate a clinical note first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Ensure API URL has /api/v1 path
      let baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';
      if (!baseUrl.endsWith('/api/v1')) {
        baseUrl = `${baseUrl}/api/v1`;
      }

      // Use first 200 chars for faster search
      const searchQuery = currentNote.substring(0, 200);

      const icd10Url = `${baseUrl}/icd10/semantic-search?query=${encodeURIComponent(searchQuery)}&limit=3&year=2026`;
      const procedureUrl = `${baseUrl}/procedure/hybrid-search?query=${encodeURIComponent(searchQuery)}&limit=3&year=2025&semantic_weight=0.7`;

      const trimmedKey = apiKey.trim();
      console.log('Calling APIs:', {
        icd10Url,
        procedureUrl,
        apiKeyLength: trimmedKey.length,
        apiKeyPrefix: trimmedKey.substring(0, 5),
        apiKeySuffix: trimmedKey.substring(trimmedKey.length - 5)
      });

      const [icd10Response, procedureResponse] = await Promise.all([
        fetch(icd10Url, {
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`
          }
        }),
        fetch(procedureUrl, {
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`
          }
        })
      ]);

      if (!icd10Response.ok || !procedureResponse.ok) {
        const failedEndpoint = !icd10Response.ok ? 'ICD-10' : 'Procedure';
        const failedUrl = !icd10Response.ok ? icd10Url : procedureUrl;
        const statusCode = !icd10Response.ok ? icd10Response.status : procedureResponse.status;
        const errorBody = !icd10Response.ok
          ? await icd10Response.text()
          : await procedureResponse.text();

        console.error(`${failedEndpoint} API failed:`, { statusCode, errorBody, url: failedUrl });
        throw new Error(`${failedEndpoint} API request failed (${statusCode}): ${errorBody}. URL: ${failedUrl}`);
      }

      const icd10Data = await icd10Response.json();
      const procedureData = await procedureResponse.json();

      console.log('API Responses:', {
        icd10: {
          total_results: icd10Data.total_results,
          results_count: icd10Data.results?.length || 0,
          first_result: icd10Data.results?.[0]
        },
        procedure: {
          total_results: procedureData.total_results,
          results_count: procedureData.results?.length || 0,
          first_result: procedureData.results?.[0]
        }
      });

      setIcd10Results(icd10Data);
      setProcedureResults(procedureData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch codes. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setCurrentNote('');
    setNoteTitle('');
    setIcd10Results(null);
    setProcedureResults(null);
    setError('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-nuvii-blue" />
          MedCode Playground
        </h1>
        <p className="text-gray-600 mt-2">
          Generate sample clinical notes and automatically suggest ICD-10 and CPT/HCPCS codes using semantic search
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

        {/* Action Buttons */}
        <div className="mt-4 flex gap-3">
          <button
            onClick={searchCodes}
            disabled={loading || !apiKey || !currentNote.trim()}
            className="px-6 py-3 bg-nuvii-blue text-white rounded-md hover:bg-blue-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Code2 className="w-5 h-5" />
                Get Suggested Codes
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
      {(icd10Results || procedureResults) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ICD-10 Results */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="bg-nuvii-blue p-4 text-white">
              <h3 className="text-lg font-semibold flex items-center justify-between">
                <span>ICD-10 Diagnosis Codes</span>
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                  {icd10Results?.results?.length || 0}
                </span>
              </h3>
            </div>
            <div className="p-4 space-y-3">
              {icd10Results?.results?.map((code, index) => (
                <div
                  key={index}
                  className="border-l-4 border-nuvii-blue bg-gray-50 p-3 rounded hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-nuvii-blue text-lg">{code.code_info.code}</span>
                    <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold">
                      {(code.similarity * 100).toFixed(1)}% match
                    </span>
                  </div>
                  <p className="text-gray-700 text-sm">{code.code_info.description}</p>
                </div>
              ))}
              {(icd10Results?.search_time_ms || icd10Results?.total_results) && (
                <div className="flex gap-4 pt-3 border-t text-xs text-gray-600">
                  {icd10Results.search_time_ms && (
                    <span>Search time: <strong>{icd10Results.search_time_ms.toFixed(0)}ms</strong></span>
                  )}
                  {icd10Results.total_results && (
                    <span>Total results: <strong>{icd10Results.total_results}</strong></span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Procedure Results */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="bg-nuvii-teal p-4 text-white">
              <h3 className="text-lg font-semibold flex items-center justify-between">
                <span>CPT/HCPCS Procedure Codes</span>
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                  {procedureResults?.results?.length || 0}
                </span>
              </h3>
            </div>
            <div className="p-4 space-y-3">
              {procedureResults?.results?.map((code, index) => (
                <div
                  key={index}
                  className="border-l-4 border-nuvii-teal bg-gray-50 p-3 rounded hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="font-bold text-nuvii-teal text-lg">{code.code_info.code}</span>
                      {code.code_info.code_system && (
                        <span className="ml-2 text-xs text-gray-500">({code.code_info.code_system})</span>
                      )}
                    </div>
                    <span className="bg-teal-100 text-teal-700 px-3 py-1 rounded-full text-xs font-semibold">
                      {(code.similarity * 100).toFixed(1)}% match
                    </span>
                  </div>
                  <p className="text-gray-700 text-sm mb-3">{code.code_info.description}</p>

                  {/* Facets Display */}
                  {code.facets && (
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
                </div>
              ))}
              {(procedureResults?.search_time_ms || procedureResults?.total_results) && (
                <div className="flex gap-4 pt-3 border-t text-xs text-gray-600">
                  {procedureResults.search_time_ms && (
                    <span>Search time: <strong>{procedureResults.search_time_ms.toFixed(0)}ms</strong></span>
                  )}
                  {procedureResults.total_results && (
                    <span>Total results: <strong>{procedureResults.total_results}</strong></span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
