'use client';

import { useState } from 'react';
import { Search, MapPin, DollarSign, Loader2, AlertCircle, Building2, Home, Info, ChevronDown, ChevronUp } from 'lucide-react';
import Link from 'next/link';

interface LocalityInfo {
  zip_code: string;
  locality_code: string;
  locality_name: string;
  mac_code?: string;
  state?: string;
  work_gpci: number;
  pe_gpci: number;
  mp_gpci: number;
  year: number;
}

interface PriceResult {
  hcpcs_code: string;
  modifier?: string;
  description?: string;
  setting: string;
  price: number;
  national_price: number;
  work_rvu?: number;
  pe_rvu?: number;
  mp_rvu?: number;
  total_rvu?: number;
  conversion_factor: number;
  locality: LocalityInfo;
  global_days?: string;
  status_code?: string;
  year: number;
}

interface SearchResult {
  hcpcs_code: string;
  modifier?: string;
  description?: string;
  work_rvu?: number;
  non_facility_pe_rvu?: number;
  facility_pe_rvu?: number;
  mp_rvu?: number;
  non_facility_total?: number;
  facility_total?: number;
  global_days?: string;
  year: number;
}

export default function FeeSchedulePage() {
  const [apiKey, setApiKey] = useState('');
  const [searchMode, setSearchMode] = useState<'price' | 'search'>('price');

  // Price lookup state
  const [code, setCode] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [year, setYear] = useState(2025);
  const [setting, setSetting] = useState<'facility' | 'non_facility'>('non_facility');
  const [priceResult, setPriceResult] = useState<PriceResult | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  const lookupPrice = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!code.trim()) {
      setError('Please enter a CPT/HCPCS code');
      return;
    }
    if (!zipCode.trim() || zipCode.length !== 5) {
      setError('Please enter a valid 5-digit ZIP code');
      return;
    }

    setLoading(true);
    setError('');
    setPriceResult(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';
      const response = await fetch(
        `${baseUrl}/api/v1/fee-schedule/price?code=${encodeURIComponent(code.trim())}&zip=${zipCode}&year=${year}&setting=${setting}`,
        {
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`,
          },
        }
      );

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`API error (${response.status}): ${errorBody}`);
      }

      const data = await response.json();
      setPriceResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to lookup price. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const searchCodes = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    setSearchResults([]);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';
      const response = await fetch(
        `${baseUrl}/api/v1/fee-schedule/search?query=${encodeURIComponent(searchQuery.trim())}&year=${year}&limit=20`,
        {
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`,
          },
        }
      );

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`API error (${response.status}): ${errorBody}`);
      }

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err: any) {
      setError(err.message || 'Failed to search codes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectCodeFromSearch = (result: SearchResult) => {
    setCode(result.hcpcs_code);
    setSearchMode('price');
    setSearchResults([]);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <DollarSign className="w-8 h-8 text-green-600" />
              <span className="text-xl font-bold text-gray-900">Medicare Fee Schedule Lookup</span>
            </Link>
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            CMS Medicare Fee Schedule Explorer
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Look up Medicare reimbursement rates for any CPT/HCPCS code.
            Get location-adjusted pricing based on your ZIP code.
          </p>
        </div>

        {/* API Key Input */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Key
          </label>
          <input
            type="text"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter your API key (mk_...)"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-2">
            Don&apos;t have an API key? <Link href="/signup" className="text-green-600 hover:underline">Sign up for free</Link> to get started.
          </p>
        </div>

        {/* Mode Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setSearchMode('price')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                searchMode === 'price'
                  ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <DollarSign className="w-4 h-4 inline mr-2" />
              Price Lookup
            </button>
            <button
              onClick={() => setSearchMode('search')}
              className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                searchMode === 'search'
                  ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Search className="w-4 h-4 inline mr-2" />
              Search Codes
            </button>
          </div>

          {/* Price Lookup Form */}
          {searchMode === 'price' && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CPT/HCPCS Code
                  </label>
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    placeholder="e.g., 99213"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <MapPin className="w-4 h-4 inline mr-1" />
                    ZIP Code
                  </label>
                  <input
                    type="text"
                    value={zipCode}
                    onChange={(e) => setZipCode(e.target.value.replace(/\D/g, '').slice(0, 5))}
                    placeholder="e.g., 10001"
                    maxLength={5}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year
                  </label>
                  <select
                    value={year}
                    onChange={(e) => setYear(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value={2025}>2025</option>
                    <option value={2024}>2024</option>
                    <option value={2023}>2023</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Setting
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSetting('non_facility')}
                      className={`flex-1 px-3 py-2 text-sm rounded-md flex items-center justify-center gap-1 transition-colors ${
                        setting === 'non_facility'
                          ? 'bg-green-100 text-green-700 border-2 border-green-500'
                          : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                      }`}
                    >
                      <Home className="w-4 h-4" />
                      Office
                    </button>
                    <button
                      onClick={() => setSetting('facility')}
                      className={`flex-1 px-3 py-2 text-sm rounded-md flex items-center justify-center gap-1 transition-colors ${
                        setting === 'facility'
                          ? 'bg-green-100 text-green-700 border-2 border-green-500'
                          : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                      }`}
                    >
                      <Building2 className="w-4 h-4" />
                      Facility
                    </button>
                  </div>
                </div>
              </div>
              <button
                onClick={lookupPrice}
                disabled={loading || !apiKey || !code || !zipCode}
                className="w-full md:w-auto px-8 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Looking up...
                  </>
                ) : (
                  <>
                    <DollarSign className="w-5 h-5" />
                    Get Medicare Price
                  </>
                )}
              </button>
            </div>
          )}

          {/* Search Codes Form */}
          {searchMode === 'search' && (
            <div className="p-6">
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search by Code or Description
                  </label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="e.g., 99213 or 'office visit'"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    onKeyPress={(e) => e.key === 'Enter' && searchCodes()}
                  />
                </div>
                <div className="w-32">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year
                  </label>
                  <select
                    value={year}
                    onChange={(e) => setYear(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value={2025}>2025</option>
                    <option value={2024}>2024</option>
                    <option value={2023}>2023</option>
                  </select>
                </div>
              </div>
              <button
                onClick={searchCodes}
                disabled={loading || !apiKey || !searchQuery}
                className="w-full md:w-auto px-8 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Search
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium">Error</p>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Price Result */}
        {priceResult && (
          <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
            {/* Main Price Card */}
            <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm opacity-80 mb-1">
                    Medicare {setting === 'facility' ? 'Facility' : 'Non-Facility'} Rate
                  </div>
                  <div className="text-5xl font-bold">{formatCurrency(priceResult.price)}</div>
                  <div className="text-sm opacity-80 mt-2">
                    {priceResult.locality.locality_name}, {priceResult.locality.state}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">{priceResult.hcpcs_code}</div>
                  <div className="text-sm opacity-80 max-w-xs">{priceResult.description}</div>
                </div>
              </div>
            </div>

            {/* Price Comparison */}
            <div className="p-6 border-b">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Your Location Rate</div>
                  <div className="text-3xl font-bold text-green-600">{formatCurrency(priceResult.price)}</div>
                  <div className="text-xs text-gray-500 mt-1">ZIP: {priceResult.locality.zip_code}</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">National Average</div>
                  <div className="text-3xl font-bold text-gray-700">{formatCurrency(priceResult.national_price)}</div>
                  <div className="text-xs text-gray-500 mt-1">GPCI = 1.0</div>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Location Adjustment</div>
                  <div className="text-3xl font-bold text-blue-600">
                    {((priceResult.price / priceResult.national_price - 1) * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {priceResult.price > priceResult.national_price ? 'Above' : 'Below'} national average
                  </div>
                </div>
              </div>
            </div>

            {/* Toggle Details */}
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="w-full p-4 flex items-center justify-center gap-2 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              {showDetails ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              {showDetails ? 'Hide' : 'Show'} Calculation Details
            </button>

            {/* Detailed Breakdown */}
            {showDetails && (
              <div className="p-6 bg-gray-50 border-t">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Info className="w-5 h-5" />
                  Price Calculation Breakdown
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* RVU Table */}
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Relative Value Units (RVUs)</h5>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 text-gray-600">Component</th>
                          <th className="text-right py-2 text-gray-600">RVU</th>
                          <th className="text-right py-2 text-gray-600">GPCI</th>
                          <th className="text-right py-2 text-gray-600">Adjusted</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b">
                          <td className="py-2">Work</td>
                          <td className="text-right">{priceResult.work_rvu?.toFixed(2) || '0.00'}</td>
                          <td className="text-right">{priceResult.locality.work_gpci.toFixed(4)}</td>
                          <td className="text-right">
                            {((priceResult.work_rvu || 0) * priceResult.locality.work_gpci).toFixed(2)}
                          </td>
                        </tr>
                        <tr className="border-b">
                          <td className="py-2">Practice Expense</td>
                          <td className="text-right">{priceResult.pe_rvu?.toFixed(2) || '0.00'}</td>
                          <td className="text-right">{priceResult.locality.pe_gpci.toFixed(4)}</td>
                          <td className="text-right">
                            {((priceResult.pe_rvu || 0) * priceResult.locality.pe_gpci).toFixed(2)}
                          </td>
                        </tr>
                        <tr className="border-b">
                          <td className="py-2">Malpractice</td>
                          <td className="text-right">{priceResult.mp_rvu?.toFixed(2) || '0.00'}</td>
                          <td className="text-right">{priceResult.locality.mp_gpci.toFixed(4)}</td>
                          <td className="text-right">
                            {((priceResult.mp_rvu || 0) * priceResult.locality.mp_gpci).toFixed(2)}
                          </td>
                        </tr>
                        <tr className="font-semibold">
                          <td className="py-2">Total</td>
                          <td className="text-right">{priceResult.total_rvu?.toFixed(2) || '0.00'}</td>
                          <td className="text-right">-</td>
                          <td className="text-right">
                            {(
                              ((priceResult.work_rvu || 0) * priceResult.locality.work_gpci) +
                              ((priceResult.pe_rvu || 0) * priceResult.locality.pe_gpci) +
                              ((priceResult.mp_rvu || 0) * priceResult.locality.mp_gpci)
                            ).toFixed(2)}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Formula & Additional Info */}
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Calculation Formula</h5>
                    <div className="bg-white p-4 rounded-lg border text-sm font-mono">
                      <div className="text-gray-600 mb-2">Price = Adjusted RVUs × Conversion Factor</div>
                      <div className="text-gray-800">
                        = {(
                          ((priceResult.work_rvu || 0) * priceResult.locality.work_gpci) +
                          ((priceResult.pe_rvu || 0) * priceResult.locality.pe_gpci) +
                          ((priceResult.mp_rvu || 0) * priceResult.locality.mp_gpci)
                        ).toFixed(4)} × {priceResult.conversion_factor.toFixed(4)}
                      </div>
                      <div className="text-green-600 font-semibold mt-1">
                        = {formatCurrency(priceResult.price)}
                      </div>
                    </div>

                    <div className="mt-4 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Conversion Factor ({priceResult.year})</span>
                        <span className="font-medium">${priceResult.conversion_factor.toFixed(4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Global Days</span>
                        <span className="font-medium">{priceResult.global_days || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status Code</span>
                        <span className="font-medium">{priceResult.status_code || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Locality Code</span>
                        <span className="font-medium">{priceResult.locality.locality_code}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b bg-gray-50">
              <h3 className="font-semibold text-gray-900">
                Search Results ({searchResults.length} codes)
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Click on a code to look up its price
              </p>
            </div>
            <div className="divide-y max-h-96 overflow-y-auto">
              {searchResults.map((result, index) => (
                <button
                  key={index}
                  onClick={() => selectCodeFromSearch(result)}
                  className="w-full p-4 hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-bold text-gray-900 text-lg">{result.hcpcs_code}</span>
                      {result.modifier && (
                        <span className="ml-2 text-xs bg-gray-200 px-2 py-1 rounded">{result.modifier}</span>
                      )}
                      <p className="text-sm text-gray-600 mt-1">{result.description}</p>
                    </div>
                    <div className="text-right text-sm">
                      <div className="text-gray-500">Non-Fac: {result.non_facility_total?.toFixed(2) || 'N/A'}</div>
                      <div className="text-gray-500">Facility: {result.facility_total?.toFixed(2) || 'N/A'}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="font-semibold text-gray-900 mb-2">What is the Medicare Fee Schedule?</h3>
            <p className="text-sm text-gray-600">
              The Medicare Physician Fee Schedule (MPFS) determines how much Medicare pays for over 10,000
              physician services. Payments are based on Relative Value Units (RVUs) adjusted for geographic differences.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="font-semibold text-gray-900 mb-2">Understanding GPCIs</h3>
            <p className="text-sm text-gray-600">
              Geographic Practice Cost Indices (GPCIs) adjust payments based on local costs. Areas with higher
              costs of living (like NYC or SF) have higher GPCIs, resulting in higher Medicare payments.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="font-semibold text-gray-900 mb-2">Facility vs Non-Facility</h3>
            <p className="text-sm text-gray-600">
              Non-facility rates (office setting) are typically higher because they include practice overhead costs.
              Facility rates assume the hospital/ASC covers those expenses.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-8 bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-8 text-center text-white">
          <h2 className="text-2xl font-bold mb-3">Need to Compare Payer Contracts?</h2>
          <p className="text-lg opacity-90 mb-6 max-w-2xl mx-auto">
            Upload your fee schedule to see how your contracted rates compare to Medicare.
            Identify underpaid codes and calculate revenue impact.
          </p>
          <Link
            href="/dashboard/fee-schedule"
            className="inline-block px-8 py-3 bg-white text-green-600 font-semibold rounded-md hover:bg-gray-100 transition-colors"
          >
            Try Contract Analyzer
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-sm text-gray-600">
          <p>Data sourced from CMS Medicare Physician Fee Schedule files.</p>
          <p className="mt-1">
            <Link href="/docs" className="text-green-600 hover:underline">API Documentation</Link>
            {' '}&bull;{' '}
            <Link href="/dashboard" className="text-green-600 hover:underline">Dashboard</Link>
            {' '}&bull;{' '}
            <Link href="/" className="text-green-600 hover:underline">Home</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}
