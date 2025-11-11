'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export default function InteractiveAPITester() {
  const [codeQuery, setCodeQuery] = useState('29881');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const curlCommand = `curl -X GET "https://api.nuvii.ai/api/v1/procedure/${codeQuery}?code_system=CPT&include_facets=true" \\
  -H "Authorization: Bearer YOUR_API_KEY"`;

  const handleTest = async () => {
    setLoading(true);
    setResponse(null);

    // Simulate API call with demo data showing rich metadata
    setTimeout(() => {
      setResponse({
        code_info: {
          code: '29881',
          code_system: 'CPT',
          description: 'Knee arthroscopy with meniscectomy (removal of torn cartilage)',
          category: 'Surgery',
          version_year: 2025,
          license_status: 'free'
        },
        facets: {
          body_region: 'lower_extremity',
          body_system: 'musculoskeletal',
          procedure_category: 'surgical',
          complexity_level: 'moderate',
          surgical_approach: 'endoscopic',
          service_location: 'hospital_outpatient',
          is_major_surgery: false,
          is_bilateral: false,
          requires_modifier: false
        },
        mappings: []
      });
      setLoading(false);
    }, 1000);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(curlCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 space-y-4">
      {/* Input Section */}
      <div className="flex gap-3">
        <input
          type="text"
          value={codeQuery}
          onChange={(e) => setCodeQuery(e.target.value)}
          placeholder="Enter CPT code (e.g., 29881, 99213)"
          className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleTest}
          disabled={loading || !codeQuery}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Testing...
            </span>
          ) : (
            'Test API'
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
        <div className="bg-gray-800 rounded-md p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Response:</h3>
            <span className="text-xs text-green-400 font-mono">200 OK</span>
          </div>
          <div className="overflow-x-auto">
            <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
              {JSON.stringify(response, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {loading && !response && (
        <div className="bg-gray-800 rounded-md p-8 flex items-center justify-center">
          <div className="text-gray-400 flex items-center gap-3">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Fetching results...</span>
          </div>
        </div>
      )}
    </div>
  );
}
