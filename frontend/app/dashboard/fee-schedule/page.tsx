'use client';

import { useState, useRef } from 'react';
import {
  DollarSign,
  Upload,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Minus,
  Loader2,
  FileSpreadsheet,
  Download,
  MapPin,
  Info,
  Plus,
  Trash2,
  Search,
  Building2,
  Home,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

// ============================================================================
// Type Definitions
// ============================================================================

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

interface AnalysisLineItem {
  code: string;
  description?: string;
  contracted_rate: number;
  medicare_rate?: number;
  variance?: number;
  variance_pct?: number;
  is_below_medicare?: boolean;
  volume?: number;
  revenue_impact?: number;
  error?: string;
}

interface RedFlag {
  code: string;
  description?: string;
  contracted_rate: number;
  medicare_rate: number;
  variance: number;
  variance_pct: number;
}

interface AnalysisResult {
  total_codes: number;
  codes_matched: number;
  codes_unmatched: number;
  codes_below_medicare: number;
  codes_above_medicare: number;
  codes_equal: number;
  total_variance: number;
  total_revenue_impact: number;
  line_items: AnalysisLineItem[];
  red_flags: RedFlag[];
}

interface ManualCode {
  code: string;
  rate: string;
  volume: string;
}

// ============================================================================
// Main Component
// ============================================================================

export default function FeeScheduleAnalyzerPage() {
  // Main tab state
  const [activeTab, setActiveTab] = useState<'price' | 'search' | 'analyzer'>('price');

  // Shared state
  const [apiKey, setApiKey] = useState('');
  const [year, setYear] = useState(2025);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Price lookup state
  const [priceCode, setPriceCode] = useState('');
  const [priceZip, setPriceZip] = useState('');
  const [priceSetting, setPriceSetting] = useState<'facility' | 'non_facility'>('non_facility');
  const [priceResult, setPriceResult] = useState<PriceResult | null>(null);
  const [showPriceDetails, setShowPriceDetails] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

  // Analyzer state
  const [analyzerZip, setAnalyzerZip] = useState('');
  const [analyzerSetting, setAnalyzerSetting] = useState<'facility' | 'non_facility'>('non_facility');
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [manualCodes, setManualCodes] = useState<ManualCode[]>([{ code: '', rate: '', volume: '' }]);
  const [inputMode, setInputMode] = useState<'upload' | 'manual'>('manual');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  // ============================================================================
  // Price Lookup Functions
  // ============================================================================

  const lookupPrice = async () => {
    if (!apiKey.trim()) { setError('Please enter your API key'); return; }
    if (!priceCode.trim()) { setError('Please enter a CPT/HCPCS code'); return; }
    if (!priceZip.trim() || priceZip.length !== 5) { setError('Please enter a valid 5-digit ZIP code'); return; }

    setLoading(true);
    setError('');
    setPriceResult(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';
      const response = await fetch(
        `${baseUrl}/api/v1/fee-schedule/price?code=${encodeURIComponent(priceCode.trim())}&zip=${priceZip}&year=${year}&setting=${priceSetting}`,
        { headers: { 'Authorization': `Bearer ${apiKey.trim()}` } }
      );

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`API error (${response.status}): ${errorBody}`);
      }

      const data = await response.json();
      setPriceResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to lookup price');
    } finally {
      setLoading(false);
    }
  };

  // ============================================================================
  // Code Search Functions
  // ============================================================================

  const searchCodes = async () => {
    if (!apiKey.trim()) { setError('Please enter your API key'); return; }
    if (!searchQuery.trim()) { setError('Please enter a search query'); return; }

    setLoading(true);
    setError('');
    setSearchResults([]);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';
      const response = await fetch(
        `${baseUrl}/api/v1/fee-schedule/search?query=${encodeURIComponent(searchQuery.trim())}&year=${year}&limit=20`,
        { headers: { 'Authorization': `Bearer ${apiKey.trim()}` } }
      );

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`API error (${response.status}): ${errorBody}`);
      }

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err: any) {
      setError(err.message || 'Failed to search codes');
    } finally {
      setLoading(false);
    }
  };

  const selectCodeForPriceLookup = (code: string) => {
    setPriceCode(code);
    setActiveTab('price');
  };

  // ============================================================================
  // Contract Analyzer Functions
  // ============================================================================

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) { setFile(selectedFile); setError(''); }
  };

  const addManualCode = () => {
    setManualCodes([...manualCodes, { code: '', rate: '', volume: '' }]);
  };

  const updateManualCode = (index: number, field: keyof ManualCode, value: string) => {
    const updated = [...manualCodes];
    updated[index][field] = value;
    setManualCodes(updated);
  };

  const removeManualCode = (index: number) => {
    if (manualCodes.length > 1) {
      setManualCodes(manualCodes.filter((_, i) => i !== index));
    }
  };

  const loadSampleData = () => {
    setManualCodes([
      { code: '99213', rate: '75.00', volume: '500' },
      { code: '99214', rate: '100.00', volume: '200' },
      { code: '99215', rate: '135.00', volume: '50' },
      { code: '99203', rate: '90.00', volume: '100' },
      { code: '99204', rate: '130.00', volume: '75' },
    ]);
    setAnalyzerZip('10001');
  };

  const analyzeContract = async () => {
    if (!apiKey.trim()) { setError('Please enter your API key'); return; }
    if (!analyzerZip.trim() || analyzerZip.length !== 5) { setError('Please enter a valid 5-digit ZIP code'); return; }

    setLoading(true);
    setError('');
    setAnalysisResult(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';

      if (inputMode === 'upload' && file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(
          `${baseUrl}/api/v1/fee-schedule/analyze/upload?zip_code=${analyzerZip}&year=${year}&setting=${analyzerSetting}`,
          { method: 'POST', headers: { 'Authorization': `Bearer ${apiKey.trim()}` }, body: formData }
        );

        if (!response.ok) {
          const errorBody = await response.text();
          throw new Error(`API error (${response.status}): ${errorBody}`);
        }

        setAnalysisResult(await response.json());
      } else {
        const validCodes = manualCodes
          .filter(c => c.code.trim() && c.rate.trim())
          .map(c => ({ code: c.code.trim().toUpperCase(), rate: parseFloat(c.rate), volume: c.volume ? parseInt(c.volume) : undefined }));

        if (validCodes.length === 0) throw new Error('Please enter at least one code with a rate');

        const response = await fetch(`${baseUrl}/api/v1/fee-schedule/analyze`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${apiKey.trim()}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ codes: validCodes, zip_code: analyzerZip, year, setting: analyzerSetting }),
        });

        if (!response.ok) {
          const errorBody = await response.text();
          throw new Error(`API error (${response.status}): ${errorBody}`);
        }

        setAnalysisResult(await response.json());
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!analysisResult) return;
    const headers = ['Code', 'Description', 'Contracted Rate', 'Medicare Rate', 'Variance', 'Variance %', 'Volume', 'Revenue Impact'];
    const rows = analysisResult.line_items.map(item => [
      item.code, item.description || '', item.contracted_rate.toFixed(2), item.medicare_rate?.toFixed(2) || 'N/A',
      item.variance?.toFixed(2) || 'N/A', item.variance_pct?.toFixed(2) || 'N/A', item.volume || '', item.revenue_impact?.toFixed(2) || ''
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'contract_analysis.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <DollarSign className="w-8 h-8 text-green-600" />
          Medicare Fee Schedule Tools
        </h1>
        <p className="text-gray-600 mt-2">
          Look up Medicare rates, search codes, and analyze your contracts against Medicare baseline.
        </p>
      </div>

      {/* API Key Input */}
      <div className="bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter your API key (mk_...)"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* Main Feature Tabs */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('price')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
              activeTab === 'price' ? 'text-green-600 border-b-2 border-green-600 bg-green-50' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <DollarSign className="w-4 h-4 inline mr-2" />
            Price Lookup
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
              activeTab === 'search' ? 'text-green-600 border-b-2 border-green-600 bg-green-50' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Search className="w-4 h-4 inline mr-2" />
            Code Search
          </button>
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
              activeTab === 'analyzer' ? 'text-green-600 border-b-2 border-green-600 bg-green-50' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <TrendingDown className="w-4 h-4 inline mr-2" />
            Contract Analyzer
          </button>
        </div>

        {/* ================================================================== */}
        {/* Price Lookup Tab */}
        {/* ================================================================== */}
        {activeTab === 'price' && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CPT/HCPCS Code</label>
                <input
                  type="text"
                  value={priceCode}
                  onChange={(e) => setPriceCode(e.target.value.toUpperCase())}
                  placeholder="e.g., 99213"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <MapPin className="w-4 h-4 inline mr-1" />ZIP Code
                </label>
                <input
                  type="text"
                  value={priceZip}
                  onChange={(e) => setPriceZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
                  placeholder="e.g., 10001"
                  maxLength={5}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500">
                  <option value={2025}>2025</option>
                  <option value={2024}>2024</option>
                  <option value={2023}>2023</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Setting</label>
                <div className="flex gap-2">
                  <button onClick={() => setPriceSetting('non_facility')} className={`flex-1 px-3 py-2 text-sm rounded-md flex items-center justify-center gap-1 ${priceSetting === 'non_facility' ? 'bg-green-100 text-green-700 border-2 border-green-500' : 'bg-gray-100 text-gray-600 border-2 border-transparent'}`}>
                    <Home className="w-4 h-4" />Office
                  </button>
                  <button onClick={() => setPriceSetting('facility')} className={`flex-1 px-3 py-2 text-sm rounded-md flex items-center justify-center gap-1 ${priceSetting === 'facility' ? 'bg-green-100 text-green-700 border-2 border-green-500' : 'bg-gray-100 text-gray-600 border-2 border-transparent'}`}>
                    <Building2 className="w-4 h-4" />Facility
                  </button>
                </div>
              </div>
              <div className="flex items-end">
                <button onClick={lookupPrice} disabled={loading || !apiKey} className="w-full px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />}
                  Lookup
                </button>
              </div>
            </div>

            {/* Price Result */}
            {priceResult && (
              <div className="mt-6 border rounded-lg overflow-hidden">
                <div className="bg-gradient-to-r from-green-600 to-green-700 p-6 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm opacity-80 mb-1">Medicare {priceSetting === 'facility' ? 'Facility' : 'Non-Facility'} Rate</div>
                      <div className="text-4xl font-bold">{formatCurrency(priceResult.price)}</div>
                      <div className="text-sm opacity-80 mt-2">{priceResult.locality.locality_name}, {priceResult.locality.state}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold">{priceResult.hcpcs_code}</div>
                      <div className="text-sm opacity-80 max-w-xs">{priceResult.description}</div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-sm text-gray-600">Your Location</div>
                      <div className="text-2xl font-bold text-green-600">{formatCurrency(priceResult.price)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">National Average</div>
                      <div className="text-2xl font-bold text-gray-700">{formatCurrency(priceResult.national_price)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Adjustment</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {((priceResult.price / priceResult.national_price - 1) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>

                <button onClick={() => setShowPriceDetails(!showPriceDetails)} className="w-full p-3 flex items-center justify-center gap-2 text-gray-600 hover:bg-gray-50 border-t">
                  {showPriceDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  {showPriceDetails ? 'Hide' : 'Show'} RVU Details
                </button>

                {showPriceDetails && (
                  <div className="p-4 border-t bg-white">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2">Component</th>
                          <th className="text-right py-2">RVU</th>
                          <th className="text-right py-2">GPCI</th>
                          <th className="text-right py-2">Adjusted</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b">
                          <td className="py-2">Work</td>
                          <td className="text-right">{priceResult.work_rvu?.toFixed(2)}</td>
                          <td className="text-right">{priceResult.locality.work_gpci.toFixed(4)}</td>
                          <td className="text-right">{((priceResult.work_rvu || 0) * priceResult.locality.work_gpci).toFixed(2)}</td>
                        </tr>
                        <tr className="border-b">
                          <td className="py-2">Practice Expense</td>
                          <td className="text-right">{priceResult.pe_rvu?.toFixed(2)}</td>
                          <td className="text-right">{priceResult.locality.pe_gpci.toFixed(4)}</td>
                          <td className="text-right">{((priceResult.pe_rvu || 0) * priceResult.locality.pe_gpci).toFixed(2)}</td>
                        </tr>
                        <tr className="border-b">
                          <td className="py-2">Malpractice</td>
                          <td className="text-right">{priceResult.mp_rvu?.toFixed(2)}</td>
                          <td className="text-right">{priceResult.locality.mp_gpci.toFixed(4)}</td>
                          <td className="text-right">{((priceResult.mp_rvu || 0) * priceResult.locality.mp_gpci).toFixed(2)}</td>
                        </tr>
                      </tbody>
                    </table>
                    <div className="mt-3 text-sm text-gray-600">
                      Conversion Factor ({priceResult.year}): <span className="font-medium">${priceResult.conversion_factor.toFixed(4)}</span>
                      {priceResult.global_days && <span className="ml-4">Global Days: <span className="font-medium">{priceResult.global_days}</span></span>}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ================================================================== */}
        {/* Code Search Tab */}
        {/* ================================================================== */}
        {activeTab === 'search' && (
          <div className="p-6">
            <div className="flex gap-4 mb-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Search by Code or Description</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., 99213 or 'office visit'"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
                  onKeyPress={(e) => e.key === 'Enter' && searchCodes()}
                />
              </div>
              <div className="w-32">
                <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="w-full px-4 py-2 border border-gray-300 rounded-md">
                  <option value={2025}>2025</option>
                  <option value={2024}>2024</option>
                  <option value={2023}>2023</option>
                </select>
              </div>
              <div className="flex items-end">
                <button onClick={searchCodes} disabled={loading || !apiKey} className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  Search
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="mt-4 border rounded-lg overflow-hidden">
                <div className="p-3 bg-gray-50 border-b">
                  <span className="font-medium">{searchResults.length} results</span>
                  <span className="text-sm text-gray-500 ml-2">Click a code to look up its price</span>
                </div>
                <div className="divide-y max-h-96 overflow-y-auto">
                  {searchResults.map((result, index) => (
                    <div key={index} className="p-4 hover:bg-gray-50 cursor-pointer" onClick={() => selectCodeForPriceLookup(result.hcpcs_code)}>
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-bold text-lg text-green-600">{result.hcpcs_code}</span>
                          {result.modifier && <span className="ml-2 text-xs bg-gray-200 px-2 py-0.5 rounded">{result.modifier}</span>}
                          <p className="text-sm text-gray-600 mt-1">{result.description}</p>
                        </div>
                        <div className="text-right text-sm">
                          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                            <span className="text-gray-500">Work RVU:</span>
                            <span className="font-medium">{result.work_rvu?.toFixed(2) || '-'}</span>
                            <span className="text-gray-500">Non-Fac Total:</span>
                            <span className="font-medium">{result.non_facility_total?.toFixed(2) || '-'}</span>
                            <span className="text-gray-500">Facility Total:</span>
                            <span className="font-medium">{result.facility_total?.toFixed(2) || '-'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ================================================================== */}
        {/* Contract Analyzer Tab */}
        {/* ================================================================== */}
        {activeTab === 'analyzer' && (
          <div className="p-6">
            {/* Configuration */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <MapPin className="w-4 h-4 inline mr-1" />ZIP Code
                </label>
                <input
                  type="text"
                  value={analyzerZip}
                  onChange={(e) => setAnalyzerZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
                  placeholder="e.g., 10001"
                  maxLength={5}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CMS Year</label>
                <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="w-full px-4 py-2 border border-gray-300 rounded-md">
                  <option value={2025}>2025</option>
                  <option value={2024}>2024</option>
                  <option value={2023}>2023</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Setting</label>
                <select value={analyzerSetting} onChange={(e) => setAnalyzerSetting(e.target.value as 'facility' | 'non_facility')} className="w-full px-4 py-2 border border-gray-300 rounded-md">
                  <option value="non_facility">Non-Facility (Office)</option>
                  <option value="facility">Facility (Hospital/ASC)</option>
                </select>
              </div>
            </div>

            {/* Input Mode Tabs */}
            <div className="border rounded-lg mb-4">
              <div className="flex border-b">
                <button onClick={() => setInputMode('manual')} className={`flex-1 px-4 py-3 text-sm ${inputMode === 'manual' ? 'bg-gray-100 font-medium' : ''}`}>
                  <Plus className="w-4 h-4 inline mr-1" />Manual Entry
                </button>
                <button onClick={() => setInputMode('upload')} className={`flex-1 px-4 py-3 text-sm ${inputMode === 'upload' ? 'bg-gray-100 font-medium' : ''}`}>
                  <Upload className="w-4 h-4 inline mr-1" />Upload CSV
                </button>
              </div>

              <div className="p-4">
                {inputMode === 'manual' ? (
                  <>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-2">CPT/HCPCS Code</th>
                          <th className="text-left py-2 px-2">Contracted Rate ($)</th>
                          <th className="text-left py-2 px-2">Volume (optional)</th>
                          <th className="w-10"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {manualCodes.map((item, index) => (
                          <tr key={index} className="border-b">
                            <td className="py-2 px-2">
                              <input type="text" value={item.code} onChange={(e) => updateManualCode(index, 'code', e.target.value.toUpperCase())} placeholder="99213" className="w-full px-3 py-1.5 border rounded" />
                            </td>
                            <td className="py-2 px-2">
                              <input type="text" value={item.rate} onChange={(e) => updateManualCode(index, 'rate', e.target.value.replace(/[^\d.]/g, ''))} placeholder="85.00" className="w-full px-3 py-1.5 border rounded" />
                            </td>
                            <td className="py-2 px-2">
                              <input type="text" value={item.volume} onChange={(e) => updateManualCode(index, 'volume', e.target.value.replace(/\D/g, ''))} placeholder="500" className="w-full px-3 py-1.5 border rounded" />
                            </td>
                            <td className="py-2 px-2">
                              <button onClick={() => removeManualCode(index)} disabled={manualCodes.length === 1} className="p-1 text-gray-400 hover:text-red-500 disabled:opacity-50">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <div className="mt-3 flex gap-3">
                      <button onClick={addManualCode} className="px-4 py-2 border rounded-md hover:bg-gray-50 text-sm flex items-center gap-2">
                        <Plus className="w-4 h-4" />Add Row
                      </button>
                      <button onClick={loadSampleData} className="px-4 py-2 border rounded-md hover:bg-gray-50 text-sm">
                        Load Sample Data
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-green-500">
                      <FileSpreadsheet className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      {file ? (
                        <p className="text-green-600 font-medium">{file.name}</p>
                      ) : (
                        <p className="text-gray-700">Click to upload CSV</p>
                      )}
                      <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileSelect} className="hidden" />
                    </div>
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
                      <Info className="w-4 h-4 inline mr-1" />
                      CSV columns: <code className="bg-blue-100 px-1 rounded">code</code>, <code className="bg-blue-100 px-1 rounded">rate</code>, <code className="bg-blue-100 px-1 rounded">volume</code> (optional)
                    </div>
                  </>
                )}
              </div>
            </div>

            <button onClick={analyzeContract} disabled={loading || !apiKey || !analyzerZip || (inputMode === 'upload' && !file)} className="px-8 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <DollarSign className="w-5 h-5" />}
              Analyze Contract
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <div>
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && activeTab === 'analyzer' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600">Total Codes</div>
              <div className="text-3xl font-bold text-gray-900">{analysisResult.total_codes}</div>
              <div className="text-xs text-gray-500 mt-1">{analysisResult.codes_matched} matched, {analysisResult.codes_unmatched} not found</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-red-500">
              <div className="text-sm text-gray-600 flex items-center gap-1"><TrendingDown className="w-4 h-4 text-red-500" />Below Medicare</div>
              <div className="text-3xl font-bold text-red-600">{analysisResult.codes_below_medicare}</div>
              <div className="text-xs text-gray-500 mt-1">codes paying less than Medicare</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
              <div className="text-sm text-gray-600 flex items-center gap-1"><TrendingUp className="w-4 h-4 text-green-500" />Above Medicare</div>
              <div className="text-3xl font-bold text-green-600">{analysisResult.codes_above_medicare}</div>
              <div className="text-xs text-gray-500 mt-1">codes paying more than Medicare</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-yellow-500">
              <div className="text-sm text-gray-600">Revenue Impact</div>
              <div className={`text-3xl font-bold ${analysisResult.total_revenue_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {formatCurrency(Math.abs(analysisResult.total_revenue_impact))}
              </div>
              <div className="text-xs text-gray-500 mt-1">{analysisResult.total_revenue_impact < 0 ? 'potential lost revenue' : 'above Medicare baseline'}</div>
            </div>
          </div>

          {/* Red Flags */}
          {analysisResult.red_flags.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg overflow-hidden">
              <div className="bg-red-600 p-4 text-white">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />Red Flags - Codes Significantly Below Medicare ({analysisResult.red_flags.length})
                </h3>
              </div>
              <div className="p-4">
                <p className="text-sm text-red-800 mb-4">These codes are more than 10% below Medicare rates.</p>
                <div className="space-y-2">
                  {analysisResult.red_flags.map((flag, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg border border-red-200 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-lg">{flag.code}</span>
                        <span className="text-sm text-gray-600 ml-3">{flag.description}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm"><span className="text-gray-600">Your rate: </span>{formatCurrency(flag.contracted_rate)}</div>
                        <div className="text-sm"><span className="text-gray-600">Medicare: </span>{formatCurrency(flag.medicare_rate)}</div>
                        <div className="text-red-600 font-bold">{flag.variance_pct.toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Full Results Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Detailed Analysis</h3>
              <button onClick={exportToCSV} className="px-4 py-2 border rounded-md hover:bg-gray-50 text-sm flex items-center gap-2">
                <Download className="w-4 h-4" />Export CSV
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left py-3 px-4">Code</th>
                    <th className="text-left py-3 px-4">Description</th>
                    <th className="text-right py-3 px-4">Contracted</th>
                    <th className="text-right py-3 px-4">Medicare</th>
                    <th className="text-right py-3 px-4">Variance</th>
                    <th className="text-right py-3 px-4">%</th>
                    <th className="text-right py-3 px-4">Volume</th>
                    <th className="text-right py-3 px-4">Impact</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {analysisResult.line_items.map((item, index) => (
                    <tr key={index} className={item.is_below_medicare ? 'bg-red-50' : ''}>
                      <td className="py-3 px-4 font-medium">{item.code}</td>
                      <td className="py-3 px-4 text-gray-600 max-w-xs truncate">{item.description || '-'}</td>
                      <td className="py-3 px-4 text-right">{formatCurrency(item.contracted_rate)}</td>
                      <td className="py-3 px-4 text-right">{item.medicare_rate ? formatCurrency(item.medicare_rate) : '-'}</td>
                      <td className={`py-3 px-4 text-right ${(item.variance || 0) < 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {item.variance != null ? formatCurrency(item.variance) : '-'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {item.variance_pct != null ? (
                          <span className={`inline-flex items-center gap-1 ${item.variance_pct < 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {item.variance_pct < 0 ? <TrendingDown className="w-3 h-3" /> : item.variance_pct > 0 ? <TrendingUp className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                            {Math.abs(item.variance_pct).toFixed(1)}%
                          </span>
                        ) : '-'}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600">{item.volume || '-'}</td>
                      <td className={`py-3 px-4 text-right font-medium ${(item.revenue_impact || 0) < 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {item.revenue_impact != null ? formatCurrency(item.revenue_impact) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-100 font-semibold">
                  <tr>
                    <td colSpan={4} className="py-3 px-4">Totals</td>
                    <td className={`py-3 px-4 text-right ${analysisResult.total_variance < 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(analysisResult.total_variance)}
                    </td>
                    <td></td>
                    <td></td>
                    <td className={`py-3 px-4 text-right ${analysisResult.total_revenue_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {formatCurrency(analysisResult.total_revenue_impact)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
