import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  signup: (email: string, password: string, fullName?: string, companyName?: string, role?: string, website?: string) =>
    api.post('/api/v1/auth/signup', {
      email,
      password,
      full_name: fullName,
      company_name: companyName,
      role,
      website
    }),

  login: (email: string, password: string) =>
    api.post('/api/v1/auth/login', { email, password }),

  getMe: () => api.get('/api/v1/auth/me'),
};

// API Keys API
export const apiKeysAPI = {
  list: () => api.get('/api/v1/api-keys'),
  
  create: (name: string) => api.post('/api/v1/api-keys', { name }),
  
  revoke: (id: string) => api.delete(`/api/v1/api-keys/${id}`),
};

// Usage API
export const usageAPI = {
  getLogs: (limit = 50) => api.get(`/api/v1/usage/logs?limit=${limit}`),
  
  getStats: () => api.get('/api/v1/usage/stats'),
};

// Billing API
export const billingAPI = {
  getSubscription: () => api.get('/api/v1/billing/subscription'),
  getPortal: () => api.get('/api/v1/billing/portal'),
  createCheckout: (planName: string) => api.post(`/api/v1/billing/checkout?plan_name=${planName}`),
};

// Code Search API (requires API key)
export const codeAPI = {
  searchICD10: (query: string, apiKey: string, limit = 10) =>
    axios.get(`${API_URL}/api/v1/icd10/search`, {
      params: { query, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  suggest: (text: string, apiKey: string, maxResults = 5) =>
    axios.post(
      `${API_URL}/api/v1/suggest`,
      { text, max_results: maxResults },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),
};

// Fee Schedule API (requires API key)
export const feeScheduleAPI = {
  // Get price for a code at a specific location
  getPrice: (code: string, zip: string, apiKey: string, year = 2025, setting = 'non_facility', modifier?: string) =>
    axios.get(`${API_URL}/api/v1/fee-schedule/price`, {
      params: { code, zip, year, setting, modifier },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Search codes by code or description
  searchCodes: (query: string, apiKey: string, year = 2025, limit = 20) =>
    axios.get(`${API_URL}/api/v1/fee-schedule/search`, {
      params: { query, year, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get locality info by ZIP code
  getLocality: (zip: string, apiKey: string, year = 2025) =>
    axios.get(`${API_URL}/api/v1/fee-schedule/locality`, {
      params: { zip, year },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // List all localities
  getLocalities: (apiKey: string, year = 2025, state?: string) =>
    axios.get(`${API_URL}/api/v1/fee-schedule/localities`, {
      params: { year, state },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get available years
  getYears: (apiKey: string) =>
    axios.get(`${API_URL}/api/v1/fee-schedule/years`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get conversion factor
  getConversionFactor: (apiKey: string, year = 2025) =>
    axios.get(`${API_URL}/api/v1/fee-schedule/conversion-factor`, {
      params: { year },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Analyze contract (POST with JSON body)
  analyzeContract: (
    codes: Array<{ code: string; rate: number; volume?: number; description?: string }>,
    zipCode: string,
    apiKey: string,
    year = 2025,
    setting = 'non_facility'
  ) =>
    axios.post(
      `${API_URL}/api/v1/fee-schedule/analyze`,
      { codes, zip_code: zipCode, year, setting },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),

  // Analyze contract from CSV file
  analyzeContractCSV: (file: File, zipCode: string, apiKey: string, year = 2025, setting = 'non_facility') => {
    const formData = new FormData();
    formData.append('file', file);
    return axios.post(`${API_URL}/api/v1/fee-schedule/analyze/upload`, formData, {
      params: { zip_code: zipCode, year, setting },
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Saved Code Lists API (requires JWT auth)
export const savedListsAPI = {
  getLists: () => api.get('/api/v1/fee-schedule/lists'),

  getList: (id: string) => api.get(`/api/v1/fee-schedule/lists/${id}`),

  createList: (name: string, description?: string, codes?: Array<{ code: string; notes?: string }>) =>
    api.post('/api/v1/fee-schedule/lists', { name, description, codes: codes || [] }),

  updateList: (id: string, data: { name?: string; description?: string; codes?: Array<{ code: string; notes?: string }> }) =>
    api.put(`/api/v1/fee-schedule/lists/${id}`, data),

  deleteList: (id: string) => api.delete(`/api/v1/fee-schedule/lists/${id}`),
};

// =============================================================================
// CDI Analysis API (requires API key)
// =============================================================================
export interface NoteAnalysisRequest {
  clinical_note: string;
  include_suggestions?: boolean;
  include_gaps?: boolean;
  include_entities?: boolean;
}

export interface CDIQueryRequest {
  clinical_note: string;
  gap_type?: 'specificity' | 'acuity' | 'comorbidity' | 'medical_necessity';
  query_style?: 'open_ended' | 'yes_no' | 'documentation_based';
}

export const cdiAPI = {
  // Analyze clinical note for documentation gaps
  analyzeNote: (request: NoteAnalysisRequest, apiKey: string) =>
    axios.post(`${API_URL}/api/v1/cdi/analyze`, request, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Detect documentation gaps
  detectGaps: (clinicalNote: string, apiKey: string) =>
    axios.post(
      `${API_URL}/api/v1/cdi/gaps`,
      { clinical_note: clinicalNote },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),

  // Extract clinical entities
  extractEntities: (clinicalNote: string, apiKey: string) =>
    axios.post(
      `${API_URL}/api/v1/cdi/entities`,
      { clinical_note: clinicalNote },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),

  // Generate CDI query for physicians
  generateQuery: (request: CDIQueryRequest, apiKey: string) =>
    axios.post(`${API_URL}/api/v1/cdi/generate-query`, request, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get user's CDI query history (requires JWT)
  getQueryHistory: (limit = 50) =>
    api.get(`/api/v1/cdi/query-history?limit=${limit}`),

  // Search CDI guidelines
  searchGuidelines: (query: string, apiKey: string, limit = 10) =>
    axios.get(`${API_URL}/api/v1/cdi/guidelines`, {
      params: { query, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get guidelines for a specific condition
  getGuidelinesByCondition: (condition: string, apiKey: string) =>
    axios.get(`${API_URL}/api/v1/cdi/guidelines/${encodeURIComponent(condition)}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),
};

// =============================================================================
// Revenue Optimization API (requires API key)
// =============================================================================
export interface RevenueAnalysisRequest {
  clinical_note: string;
  setting?: 'inpatient' | 'outpatient' | 'ed' | 'observation';
  patient_type?: 'new' | 'established' | 'initial' | 'subsequent';
  include_em_coding?: boolean;
  include_hcc?: boolean;
  include_drg?: boolean;
}

export interface InvestigationRequest {
  clinical_note: string;
  condition?: string;
  severity_level?: string;
}

export const revenueAPI = {
  // Full revenue analysis
  analyze: (request: RevenueAnalysisRequest, apiKey: string) =>
    axios.post(`${API_URL}/api/v1/revenue/analyze`, request, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // E/M coding analysis only
  analyzeEMCoding: (
    clinicalNote: string,
    setting: string,
    patientType: string,
    apiKey: string
  ) =>
    axios.post(
      `${API_URL}/api/v1/revenue/em-coding`,
      {
        clinical_note: clinicalNote,
        setting,
        patient_type: patientType,
      },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),

  // HCC risk adjustment analysis
  analyzeHCC: (diagnoses: string[], modelVersion: string, apiKey: string) =>
    axios.post(
      `${API_URL}/api/v1/revenue/hcc`,
      { diagnoses, model_version: modelVersion },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),

  // DRG optimization analysis
  analyzeDRG: (
    principalDiagnosis: string,
    secondaryDiagnoses: string[],
    procedures: string[],
    apiKey: string
  ) =>
    axios.post(
      `${API_URL}/api/v1/revenue/drg`,
      {
        principal_diagnosis: principalDiagnosis,
        secondary_diagnoses: secondaryDiagnoses,
        procedures,
      },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),

  // Get recommended investigations
  recommendInvestigations: (request: InvestigationRequest, apiKey: string) =>
    axios.post(`${API_URL}/api/v1/revenue/investigations`, request, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get investigation protocols for a condition
  getInvestigationProtocols: (condition: string, apiKey: string, severityLevel?: string) =>
    axios.get(`${API_URL}/api/v1/revenue/investigation-protocols/${encodeURIComponent(condition)}`, {
      params: { severity_level: severityLevel },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),
};

// =============================================================================
// Quality Measures API (requires API key)
// =============================================================================
export interface HEDISRequest {
  clinical_note: string;
  patient_age: number;
  patient_gender: 'male' | 'female';
  icd10_codes?: string[];
  generate_queries?: boolean;
}

export const qualityAPI = {
  // Full HEDIS evaluation
  evaluateHEDIS: (request: HEDISRequest, apiKey: string) =>
    axios.post(`${API_URL}/api/v1/quality/hedis`, request, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // List available HEDIS measures
  getHEDISMeasures: (apiKey: string) =>
    axios.get(`${API_URL}/api/v1/quality/hedis/measures`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Get HEDIS evaluation history (requires JWT)
  getHEDISHistory: (limit = 50) =>
    api.get(`/api/v1/quality/hedis/history?limit=${limit}`),

  // Comprehensive quality analysis
  analyzeComprehensive: (
    clinicalNote: string,
    patientAge: number,
    patientGender: string,
    apiKey: string
  ) =>
    axios.post(
      `${API_URL}/api/v1/quality/comprehensive`,
      {
        clinical_note: clinicalNote,
        patient_age: patientAge,
        patient_gender: patientGender,
      },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),
};

// =============================================================================
// Enhanced Code Search API (requires API key)
// =============================================================================
export const codesAPI = {
  // ICD-10 Search
  searchICD10: (query: string, apiKey: string, limit = 10) =>
    axios.get(`${API_URL}/api/v1/codes/icd10/search`, {
      params: { query, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  searchICD10Semantic: (query: string, apiKey: string, limit = 10) =>
    axios.get(`${API_URL}/api/v1/codes/icd10/semantic`, {
      params: { query, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  searchICD10Hybrid: (query: string, apiKey: string, semanticWeight = 0.7, limit = 10) =>
    axios.get(`${API_URL}/api/v1/codes/icd10/hybrid`, {
      params: { query, semantic_weight: semanticWeight, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  getICD10ByCode: (code: string, apiKey: string) =>
    axios.get(`${API_URL}/api/v1/codes/icd10/${code}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  searchICD10Faceted: (params: Record<string, string | number | boolean>, apiKey: string) =>
    axios.get(`${API_URL}/api/v1/codes/icd10/faceted`, {
      params,
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // CPT/HCPCS Procedure Search
  searchProcedure: (query: string, apiKey: string, limit = 10) =>
    axios.get(`${API_URL}/api/v1/codes/procedure/search`, {
      params: { query, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  searchProcedureSemantic: (query: string, apiKey: string, limit = 10) =>
    axios.get(`${API_URL}/api/v1/codes/procedure/semantic`, {
      params: { query, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  searchProcedureHybrid: (query: string, apiKey: string, semanticWeight = 0.7, limit = 10) =>
    axios.get(`${API_URL}/api/v1/codes/procedure/hybrid`, {
      params: { query, semantic_weight: semanticWeight, limit },
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  getProcedureByCode: (code: string, apiKey: string) =>
    axios.get(`${API_URL}/api/v1/codes/procedure/${code}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    }),

  // Code Suggestions from Clinical Text
  suggestCodes: (text: string, apiKey: string, codeTypes = ['icd10', 'cpt']) =>
    axios.post(
      `${API_URL}/api/v1/codes/suggest`,
      { text, code_types: codeTypes },
      { headers: { Authorization: `Bearer ${apiKey}` } }
    ),
};
