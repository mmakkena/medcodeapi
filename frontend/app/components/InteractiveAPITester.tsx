'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export default function InteractiveAPITester() {
  const [query, setQuery] = useState('diabetes');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const curlCommand = `curl -X GET "https://api.nuvii.ai/api/v1/icd10/search?query=${encodeURIComponent(query)}" \\
  -H "Authorization: Bearer YOUR_API_KEY"`;

  const handleTest = async () => {
    setLoading(true);
    setResponse(null);

    // Simulate API call with demo data
    setTimeout(() => {
      setResponse({
        results: [
          {
            code: 'E11.9',
            description: 'Type 2 diabetes mellitus without complications',
            category: 'Endocrine, nutritional and metabolic diseases'
          },
          {
            code: 'E11.65',
            description: 'Type 2 diabetes mellitus with hyperglycemia',
            category: 'Endocrine, nutritional and metabolic diseases'
          },
          {
            code: 'E10.9',
            description: 'Type 1 diabetes mellitus without complications',
            category: 'Endocrine, nutritional and metabolic diseases'
          }
        ],
        total: 3,
        query: query
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
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter search term (e.g., diabetes)"
          className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleTest}
          disabled={loading || !query}
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
