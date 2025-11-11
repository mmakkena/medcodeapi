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
  signup: (email: string, password: string, fullName?: string, companyName?: string, role?: string) =>
    api.post('/api/v1/auth/signup', {
      email,
      password,
      full_name: fullName,
      company_name: companyName,
      role
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
