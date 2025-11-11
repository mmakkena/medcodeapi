'use client';

import { useState } from 'react';
import { Sparkles, Loader2, Code2, Stethoscope, AlertCircle } from 'lucide-react';

interface CodeResult {
  code_info: {
    code: string;
    description: string;
    code_system?: string;
  };
  similarity: number;
}

interface SearchResults {
  results: CodeResult[];
  total_results?: number;
  search_time_ms?: number;
}

const SAMPLE_NOTES = [
  {
    title: 'Type 2 Diabetes Follow-up',
    note: `Chief Complaint: Type 2 diabetes follow-up

History of Present Illness:
Patient is a 58-year-old male with a history of type 2 diabetes mellitus, presenting for routine follow-up. Reports good compliance with metformin 1000mg BID. Blood glucose readings have been mostly within target range (120-180 mg/dL). Denies polyuria, polydipsia, or recent weight changes.

Physical Examination:
Vital Signs: BP 138/82, HR 76, BMI 29.3
General: Alert and oriented, no acute distress
HEENT: Pupils equal, round, reactive to light
CV: Regular rate and rhythm, no murmurs
Resp: Clear to auscultation bilaterally
Extremities: No edema, pedal pulses intact

Assessment & Plan:
1. Type 2 diabetes mellitus - well controlled on current regimen
   - Continue metformin 1000mg BID
   - HbA1c ordered
   - Referral to ophthalmology for annual diabetic eye exam
2. Hypertension - borderline elevated
   - Discussed lifestyle modifications
   - Will monitor, may need medication if persistently elevated
3. Overweight (BMI 29.3)
   - Discussed diet and exercise
   - Nutrition consultation offered

Follow-up in 3 months.`
  },
  {
    title: 'Acute Myocardial Infarction',
    note: `Chief Complaint: Acute chest pain

History of Present Illness:
68-year-old female presents to ED with sudden onset chest pain that started 2 hours ago. Pain is substernal, pressure-like, 8/10 severity, radiating to left arm. Associated with shortness of breath and diaphoresis. Patient has history of hypertension and hyperlipidemia.

Physical Examination:
Vital Signs: BP 165/95, HR 102, RR 22, O2 sat 94% on room air
General: Anxious, diaphoretic
CV: Tachycardic, regular rhythm, no murmurs
Resp: Tachypneic, clear lung sounds bilaterally

Diagnostic Results:
- ECG: ST elevation in leads V2-V4
- Troponin I: Elevated at 2.5 ng/mL
- CXR: No acute findings

Assessment & Plan:
1. STEMI (ST-elevation myocardial infarction) - anterior wall
   - Cardiology consulted
   - Prepared for emergent cardiac catheterization
   - Aspirin 325mg, clopidogrel 600mg given
   - IV heparin initiated
2. Acute coronary syndrome
   - Admitted to CCU
   - Serial cardiac enzymes

Patient transferred to cath lab emergently.`
  },
  {
    title: 'Knee Meniscus Tear',
    note: `Chief Complaint: Right knee pain

History of Present Illness:
45-year-old male construction worker presents with right knee pain for the past 2 weeks. Pain is worse with weight-bearing and climbing stairs. No history of trauma. Reports occasional swelling and stiffness, especially in the morning.

Physical Examination:
Right Knee:
- Inspection: Mild effusion noted
- Palpation: Tenderness over medial joint line
- ROM: Full flexion/extension with pain at extremes
- McMurray test: Positive medial meniscus
- Lachman test: Negative

Imaging:
X-ray right knee: Mild degenerative changes, no fracture

Assessment & Plan:
1. Right knee medial meniscus tear
   - MRI ordered for confirmation
   - Orthopedic referral
2. Osteoarthritis of right knee
   - NSAIDs: Ibuprofen 600mg TID with food
   - Physical therapy referral

Follow-up in 2 weeks with MRI results.`
  },
  {
    title: 'Annual Wellness Visit',
    note: `Chief Complaint: Annual wellness visit

History of Present Illness:
42-year-old female here for annual wellness examination. Overall feels well. No acute complaints. Regular menstrual cycles. Non-smoker, occasional alcohol use. Exercises 3-4 times per week. Family history significant for breast cancer (mother, age 52).

Physical Examination:
Vital Signs: BP 118/76, HR 68, BMI 24.2
General: Well-appearing, no acute distress
CV: Regular rate and rhythm
Resp: Clear to auscultation bilaterally
Breast: No masses, no nipple discharge
Abdomen: Soft, non-tender

Screening & Preventive Care:
- Pap smear performed
- Mammogram ordered (family history of breast cancer)
- Lipid panel ordered
- Updated TDAP vaccination

Assessment & Plan:
1. Health maintenance examination - comprehensive
2. Family history of breast cancer
   - Will start annual mammography
   - Discussed genetic counseling
3. Preventive care up to date

Follow-up in 1 year or as needed.`
  },
  {
    title: 'Pediatric Pneumonia',
    note: `Chief Complaint: Cough and fever

History of Present Illness:
6-year-old boy brought in by mother with cough and fever for 3 days. Fever up to 102.5°F. Productive cough with yellow-green sputum. Decreased appetite. Some difficulty breathing noted. Immunizations up to date.

Physical Examination:
Vital Signs: Temp 101.8°F, HR 110, RR 28, O2 sat 95%
General: Ill-appearing child, mild respiratory distress
Resp: Increased work of breathing, crackles in right lower lung field

Diagnostic Results:
- Rapid flu: Negative
- CXR: Right lower lobe infiltrate consistent with pneumonia

Assessment & Plan:
1. Community-acquired pneumonia, right lower lobe
   - Azithromycin 10mg/kg/day x 5 days
   - Supportive care: fluids, rest
   - Ibuprofen for fever
2. Respiratory distress - mild
   - Monitoring at home appropriate

Follow-up in 48-72 hours or sooner if worsening.`
  }
];

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
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.nuvii.ai/api/v1';

      const [icd10Response, procedureResponse] = await Promise.all([
        fetch(`${baseUrl}/icd10/hybrid-search?query=${encodeURIComponent(currentNote)}&limit=5&semantic_weight=0.7`, {
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`
          }
        }),
        fetch(`${baseUrl}/procedure/hybrid-search?query=${encodeURIComponent(currentNote)}&limit=5&semantic_weight=0.7`, {
          headers: {
            'Authorization': `Bearer ${apiKey.trim()}`
          }
        })
      ]);

      if (!icd10Response.ok || !procedureResponse.ok) {
        const failedEndpoint = !icd10Response.ok ? 'ICD-10' : 'Procedure';
        const statusCode = !icd10Response.ok ? icd10Response.status : procedureResponse.status;
        const errorBody = !icd10Response.ok
          ? await icd10Response.text()
          : await procedureResponse.text();

        console.error(`${failedEndpoint} API failed:`, { statusCode, errorBody });
        throw new Error(`API request failed (${statusCode}): ${errorBody || 'Please check your API key.'}`);
      }

      const icd10Data = await icd10Response.json();
      const procedureData = await procedureResponse.json();

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
          Generate sample clinical notes and automatically suggest ICD-10 and CPT/HCPCS codes using hybrid search
        </p>
      </div>

      {/* API Key Input */}
      <div className="bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          API Key
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Enter your API key (mk_...)"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nuvii-blue focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-2">
          Get your API key from the <a href="/dashboard/api-keys" className="text-nuvii-blue hover:underline">API Keys</a> page
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={generateRandomNote}
          className="px-6 py-3 bg-nuvii-blue text-white rounded-md hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
        >
          <Sparkles className="w-5 h-5" />
          Generate Random Note
        </button>
        <button
          onClick={clearAll}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors font-medium"
        >
          Clear
        </button>
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

      {/* Clinical Note */}
      {currentNote && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-3 flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-nuvii-blue" />
            {noteTitle || 'Clinical Note'}
          </h2>
          <div className="bg-white border-l-4 border-nuvii-blue p-4 rounded whitespace-pre-wrap text-sm text-gray-700 max-h-96 overflow-y-auto">
            {currentNote}
          </div>

          {/* Get Codes Button */}
          <div className="mt-4">
            <button
              onClick={searchCodes}
              disabled={loading || !apiKey}
              className="px-6 py-3 bg-nuvii-teal text-white rounded-md hover:bg-green-700 transition-colors font-medium flex items-center gap-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
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
                  <p className="text-gray-700 text-sm">{code.code_info.description}</p>
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
