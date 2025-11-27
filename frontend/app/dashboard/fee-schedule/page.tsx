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
  Check,
  X
} from 'lucide-react';

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

export default function FeeScheduleAnalyzerPage() {
  const [apiKey, setApiKey] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [year, setYear] = useState(2025);
  const [setting, setSetting] = useState<'facility' | 'non_facility'>('non_facility');

  // File upload state
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Manual entry state
  const [manualCodes, setManualCodes] = useState<ManualCode[]>([
    { code: '', rate: '', volume: '' }
  ]);
  const [inputMode, setInputMode] = useState<'upload' | 'manual'>('manual');

  // Results state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
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
    setZipCode('10001');
  };

  const analyzeContract = async () => {
    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }
    if (!zipCode.trim() || zipCode.length !== 5) {
      setError('Please enter a valid 5-digit ZIP code');
      return;
    }

    setLoading(true);
    setError('');
    setAnalysisResult(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai';

      if (inputMode === 'upload' && file) {
        // Upload CSV file
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(
          `${baseUrl}/api/v1/fee-schedule/analyze/upload?zip_code=${zipCode}&year=${year}&setting=${setting}`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${apiKey.trim()}`,
            },
            body: formData,
          }
        );

        if (!response.ok) {
          const errorBody = await response.text();
          throw new Error(`API error (${response.status}): ${errorBody}`);
        }

        const data = await response.json();
        setAnalysisResult(data);
      } else {
        // Manual entry
        const validCodes = manualCodes
          .filter(c => c.code.trim() && c.rate.trim())
          .map(c => ({
            code: c.code.trim().toUpperCase(),
            rate: parseFloat(c.rate),
            volume: c.volume ? parseInt(c.volume) : undefined,
          }));

        if (validCodes.length === 0) {
          throw new Error('Please enter at least one code with a rate');
        }

        const response = await fetch(`${baseUrl}/api/v1/fee-schedule/analyze`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            codes: validCodes,
            zip_code: zipCode,
            year,
            setting,
          }),
        });

        if (!response.ok) {
          const errorBody = await response.text();
          throw new Error(`API error (${response.status}): ${errorBody}`);
        }

        const data = await response.json();
        setAnalysisResult(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!analysisResult) return;

    const headers = ['Code', 'Description', 'Contracted Rate', 'Medicare Rate', 'Variance', 'Variance %', 'Volume', 'Revenue Impact'];
    const rows = analysisResult.line_items.map(item => [
      item.code,
      item.description || '',
      item.contracted_rate.toFixed(2),
      item.medicare_rate?.toFixed(2) || 'N/A',
      item.variance?.toFixed(2) || 'N/A',
      item.variance_pct?.toFixed(2) || 'N/A',
      item.volume || '',
      item.revenue_impact?.toFixed(2) || '',
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'contract_analysis.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <DollarSign className="w-8 h-8 text-green-600" />
          Contract Analyzer
        </h1>
        <p className="text-gray-600 mt-2">
          Compare your contracted rates against Medicare to identify underpaid codes and calculate revenue impact.
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* Configuration */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <MapPin className="w-4 h-4 inline mr-1" />
              ZIP Code (for GPCI adjustment)
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
              CMS Year
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
            <select
              value={setting}
              onChange={(e) => setSetting(e.target.value as 'facility' | 'non_facility')}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="non_facility">Non-Facility (Office)</option>
              <option value="facility">Facility (Hospital/ASC)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Input Mode Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="flex border-b">
          <button
            onClick={() => setInputMode('manual')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
              inputMode === 'manual'
                ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Manual Entry
          </button>
          <button
            onClick={() => setInputMode('upload')}
            className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
              inputMode === 'upload'
                ? 'text-green-600 border-b-2 border-green-600 bg-green-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Upload CSV
          </button>
        </div>

        <div className="p-6">
          {inputMode === 'manual' ? (
            <>
              {/* Manual Entry Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-2">CPT/HCPCS Code</th>
                      <th className="text-left py-2 px-2">Contracted Rate ($)</th>
                      <th className="text-left py-2 px-2">Annual Volume (optional)</th>
                      <th className="w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {manualCodes.map((item, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2 px-2">
                          <input
                            type="text"
                            value={item.code}
                            onChange={(e) => updateManualCode(index, 'code', e.target.value.toUpperCase())}
                            placeholder="99213"
                            className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-1 focus:ring-green-500"
                          />
                        </td>
                        <td className="py-2 px-2">
                          <input
                            type="text"
                            value={item.rate}
                            onChange={(e) => updateManualCode(index, 'rate', e.target.value.replace(/[^\d.]/g, ''))}
                            placeholder="85.00"
                            className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-1 focus:ring-green-500"
                          />
                        </td>
                        <td className="py-2 px-2">
                          <input
                            type="text"
                            value={item.volume}
                            onChange={(e) => updateManualCode(index, 'volume', e.target.value.replace(/\D/g, ''))}
                            placeholder="500"
                            className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-1 focus:ring-green-500"
                          />
                        </td>
                        <td className="py-2 px-2">
                          <button
                            onClick={() => removeManualCode(index)}
                            disabled={manualCodes.length === 1}
                            className="p-1 text-gray-400 hover:text-red-500 disabled:opacity-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex gap-3">
                <button
                  onClick={addManualCode}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-sm flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Row
                </button>
                <button
                  onClick={loadSampleData}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-sm"
                >
                  Load Sample Data
                </button>
              </div>
            </>
          ) : (
            <>
              {/* File Upload */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-green-500 transition-colors"
              >
                <FileSpreadsheet className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                {file ? (
                  <div>
                    <p className="text-green-600 font-medium">{file.name}</p>
                    <p className="text-sm text-gray-500 mt-1">Click to change file</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-gray-700 font-medium">Click to upload CSV</p>
                    <p className="text-sm text-gray-500 mt-1">or drag and drop</p>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium">CSV Format</p>
                    <p className="mt-1">Your CSV should have columns: <code className="bg-blue-100 px-1 rounded">code</code>, <code className="bg-blue-100 px-1 rounded">rate</code>, and optionally <code className="bg-blue-100 px-1 rounded">volume</code></p>
                    <p className="mt-1">Example:</p>
                    <pre className="mt-1 bg-blue-100 p-2 rounded text-xs">
{`code,rate,volume
99213,85.00,500
99214,120.00,200`}
                    </pre>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Analyze Button */}
          <div className="mt-6">
            <button
              onClick={analyzeContract}
              disabled={loading || !apiKey || !zipCode || (inputMode === 'upload' && !file)}
              className="w-full md:w-auto px-8 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <DollarSign className="w-5 h-5" />
                  Analyze Contract
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-sm text-gray-600">Total Codes</div>
              <div className="text-3xl font-bold text-gray-900">{analysisResult.total_codes}</div>
              <div className="text-xs text-gray-500 mt-1">
                {analysisResult.codes_matched} matched, {analysisResult.codes_unmatched} not found
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-red-500">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <TrendingDown className="w-4 h-4 text-red-500" />
                Below Medicare
              </div>
              <div className="text-3xl font-bold text-red-600">{analysisResult.codes_below_medicare}</div>
              <div className="text-xs text-gray-500 mt-1">codes paying less than Medicare</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <TrendingUp className="w-4 h-4 text-green-500" />
                Above Medicare
              </div>
              <div className="text-3xl font-bold text-green-600">{analysisResult.codes_above_medicare}</div>
              <div className="text-xs text-gray-500 mt-1">codes paying more than Medicare</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow border-l-4 border-yellow-500">
              <div className="text-sm text-gray-600">Revenue Impact</div>
              <div className={`text-3xl font-bold ${analysisResult.total_revenue_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {formatCurrency(Math.abs(analysisResult.total_revenue_impact))}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {analysisResult.total_revenue_impact < 0 ? 'potential lost revenue' : 'above Medicare baseline'}
              </div>
            </div>
          </div>

          {/* Red Flags */}
          {analysisResult.red_flags.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg overflow-hidden">
              <div className="bg-red-600 p-4 text-white flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Red Flags - Codes Significantly Below Medicare ({analysisResult.red_flags.length})
                </h3>
              </div>
              <div className="p-4">
                <p className="text-sm text-red-800 mb-4">
                  These codes are more than 10% below Medicare rates. Consider renegotiating these rates.
                </p>
                <div className="space-y-2">
                  {analysisResult.red_flags.map((flag, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg border border-red-200 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-lg">{flag.code}</span>
                        <span className="text-sm text-gray-600 ml-3">{flag.description}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm">
                          <span className="text-gray-600">Your rate: </span>
                          <span className="font-medium">{formatCurrency(flag.contracted_rate)}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">Medicare: </span>
                          <span className="font-medium">{formatCurrency(flag.medicare_rate)}</span>
                        </div>
                        <div className="text-red-600 font-bold">
                          {flag.variance_pct.toFixed(1)}%
                        </div>
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
              <button
                onClick={exportToCSV}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-sm flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Code</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-600">Description</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Contracted</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Medicare</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Variance</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">%</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Volume</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Impact</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {analysisResult.line_items.map((item, index) => (
                    <tr key={index} className={item.is_below_medicare ? 'bg-red-50' : ''}>
                      <td className="py-3 px-4 font-medium">{item.code}</td>
                      <td className="py-3 px-4 text-gray-600 max-w-xs truncate">{item.description || '-'}</td>
                      <td className="py-3 px-4 text-right">{formatCurrency(item.contracted_rate)}</td>
                      <td className="py-3 px-4 text-right">
                        {item.medicare_rate ? formatCurrency(item.medicare_rate) : '-'}
                      </td>
                      <td className={`py-3 px-4 text-right ${(item.variance || 0) < 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {item.variance != null ? formatCurrency(item.variance) : '-'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {item.variance_pct != null ? (
                          <span className={`inline-flex items-center gap-1 ${(item.variance_pct) < 0 ? 'text-red-600' : 'text-green-600'}`}>
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
