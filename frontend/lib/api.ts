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
