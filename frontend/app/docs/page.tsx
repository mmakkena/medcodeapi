'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';

export default function DocsPage() {
  const [copiedEndpoint, setCopiedEndpoint] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedEndpoint(id);
    setTimeout(() => setCopiedEndpoint(null), 2000);
  };

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b sticky top-0 bg-white z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link href="/">
            <Image
              src="/nuvii_logo.png"
              alt="Nuvii AI"
              width={720}
              height={192}
              className="h-48 w-auto"
            />
          </Link>
          <Link
            href="/"
            className="text-gray-700 hover:text-gray-900"
          >
            Back to Home
          </Link>
        </div>
      </header>

      {/* API Documentation Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="space-y-6">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">API Documentation</h1>
            <p className="text-gray-600">
              Complete reference for the Nuvii API endpoints and authentication.
            </p>
          </div>

      {/* Interactive API Testing */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-3">
          Interactive API Testing
        </h2>
        <p className="text-gray-700 mb-4">
          Try out the API endpoints interactively with our Swagger UI interface. Test requests, view responses, and explore all available endpoints.
        </p>
        <a
          href={`${apiUrl}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Open Interactive Swagger UI
        </a>
      </div>

      {/* Authentication */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold mb-4">Authentication</h2>
        <p className="text-gray-600 mb-4">
          All API requests must include your API key in the Authorization header:
        </p>
        <div className="bg-gray-900 text-gray-100 p-4 rounded-md font-mono text-sm relative">
          <code>Authorization: Bearer YOUR_API_KEY</code>
          <button
            onClick={() => copyToClipboard('Authorization: Bearer YOUR_API_KEY', 'auth')}
            className="absolute top-2 right-2 p-2 hover:bg-gray-800 rounded"
          >
            {copiedEndpoint === 'auth' ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Base URL */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold mb-4">Base URL</h2>
        <div className="bg-gray-900 text-gray-100 p-4 rounded-md font-mono text-sm relative">
          <code>{apiUrl}</code>
          <button
            onClick={() => copyToClipboard(apiUrl, 'base-url')}
            className="absolute top-2 right-2 p-2 hover:bg-gray-800 rounded"
          >
            {copiedEndpoint === 'base-url' ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Endpoints */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold mb-6">Endpoints</h2>

        {/* ICD-10 Endpoints */}
        <div className="mb-10">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">ICD-10 Diagnosis Codes</h3>

          {/* ICD-10 Keyword Search */}
          <div className="mb-6 p-4 border-l-4 border-blue-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Keyword Search</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Search by code or description using exact keyword matching</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded">GET /api/v1/icd10/search?query=diabetes&limit=10</code>
          </div>

          {/* ICD-10 Semantic Search */}
          <div className="mb-6 p-4 border-l-4 border-purple-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Semantic Search (AI-Powered)</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Search using natural language - finds codes based on clinical meaning, not just keywords</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block mb-2">GET /api/v1/icd10/semantic-search?query=patient%20with%20chest%20pain&min_similarity=0.7&year=2026</code>
            <div className="text-xs text-gray-600 mt-2">
              <strong>Parameters:</strong> query, code_system, version_year, limit, min_similarity
            </div>
          </div>

          {/* ICD-10 Hybrid Search */}
          <div className="mb-6 p-4 border-l-4 border-indigo-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Hybrid Search (Recommended)</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Combines semantic AI and keyword matching - best of both worlds</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block mb-2">GET /api/v1/icd10/hybrid-search?query=diabetes%20kidney%20complications&semantic_weight=0.7&year=2026</code>
            <div className="text-xs text-gray-600 mt-2">
              <strong>Parameters:</strong> query, code_system, version_year, semantic_weight (0-1), limit
              <br/>
              <strong>Tip:</strong> semantic_weight=0.7 (default) balances AI understanding with keyword precision
            </div>
          </div>

          {/* ICD-10 Faceted Search */}
          <div className="mb-6 p-4 border-l-4 border-teal-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Faceted Search (Filter by Clinical Attributes)</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Filter codes by body system, severity, chronicity, and other clinical facets</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block mb-2">GET /api/v1/icd10/faceted-search?body_system=Cardiovascular&severity=Severe</code>
            <div className="text-xs text-gray-600 mt-2">
              <strong>Facets:</strong> body_system, concept_type, chronicity, severity, acuity, risk_flag
            </div>
          </div>
        </div>

        {/* Procedure Code Endpoints */}
        <div className="mb-10">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Procedure Codes (CPT/HCPCS)</h3>

          {/* Procedure Keyword Search */}
          <div className="mb-6 p-4 border-l-4 border-green-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Keyword Search</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Search procedure codes by code or description</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block">GET /api/v1/procedure/search?query=office%20visit&code_system=CPT&year=2025</code>
            <div className="text-xs text-gray-600 mt-2">
              <strong>Parameters:</strong> query, code_system (CPT/HCPCS), version_year, limit
            </div>
          </div>

          {/* Procedure Semantic Search */}
          <div className="mb-6 p-4 border-l-4 border-purple-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Semantic Search (AI-Powered)</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Natural language search - &ldquo;blood sugar test&rdquo; finds glucose testing codes</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block">GET /api/v1/procedure/semantic-search?query=knee%20surgery&min_similarity=0.6</code>
          </div>

          {/* Procedure Hybrid Search */}
          <div className="mb-6 p-4 border-l-4 border-indigo-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Hybrid Search (Recommended)</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Combines AI and keyword matching for best results</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block">GET /api/v1/procedure/hybrid-search?query=knee%20arthroscopy&semantic_weight=0.7</code>
          </div>

          {/* Procedure Faceted Search */}
          <div className="mb-6 p-4 border-l-4 border-teal-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Faceted Search</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Filter by body region, complexity, service location, E/M level, imaging type, etc.</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block">GET /api/v1/procedure/faceted-search?procedure_category=evaluation&em_level=level_3</code>
            <div className="text-xs text-gray-600 mt-2">
              <strong>Facets:</strong> body_region, body_system, procedure_category, complexity_level, service_location, em_level, imaging_modality
            </div>
          </div>

          {/* Get Code Details */}
          <div className="mb-6 p-4 border-l-4 border-orange-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">GET</span>
              <h4 className="font-semibold">Get Code Details</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Get detailed information, facets, and mappings for a specific code</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block">GET /api/v1/procedure/99213?code_system=CPT&version_year=2025</code>
          </div>

          {/* Procedure Code Suggestions */}
          <div className="mb-6 p-4 border-l-4 border-pink-500 bg-gray-50">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">POST</span>
              <h4 className="font-semibold">Suggest Codes from Clinical Text</h4>
            </div>
            <p className="text-sm text-gray-600 mb-2">Analyze clinical documentation and suggest appropriate procedure codes</p>
            <code className="text-xs bg-gray-800 text-gray-100 px-2 py-1 rounded block">POST /api/v1/procedure/suggest?clinical_text=Patient%20for%20wellness%20exam&min_similarity=0.7</code>
            <div className="text-xs text-gray-600 mt-2">
              <strong>Use Case:</strong> Automated coding assistance, EHR integration, compliance checking
            </div>
          </div>
        </div>
      </div>

      {/* Rate Limits */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold mb-4">Rate Limits</h2>
        <div className="space-y-3 text-gray-600">
          <p>
            <strong>Per Minute:</strong> 60 requests (Free), 300 requests (Developer), 1000 requests (Growth)
          </p>
          <p>
            <strong>Per Day:</strong> 10,000 requests (adjusts based on your plan)
          </p>
          <p className="text-sm text-gray-500">
            Rate limit headers are included in all responses: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
          </p>
        </div>
      </div>

      {/* Error Codes */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-semibold mb-4">Error Codes</h2>
        <div className="space-y-2">
          <div className="flex items-start gap-3">
            <code className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-mono rounded">400</code>
            <span className="text-gray-600">Bad Request - Invalid parameters</span>
          </div>
          <div className="flex items-start gap-3">
            <code className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-mono rounded">401</code>
            <span className="text-gray-600">Unauthorized - Invalid or missing API key</span>
          </div>
          <div className="flex items-start gap-3">
            <code className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-mono rounded">429</code>
            <span className="text-gray-600">Too Many Requests - Rate limit exceeded</span>
          </div>
          <div className="flex items-start gap-3">
            <code className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-mono rounded">500</code>
            <span className="text-gray-600">Internal Server Error - Something went wrong</span>
          </div>
        </div>
      </div>

        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 bg-gray-50 px-4 sm:px-6 lg:px-8 border-t mt-12">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-600">&copy; 2025 Nuvii API. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
