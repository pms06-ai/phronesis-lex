/**
 * API Service for Phronesis LEX
 * Comprehensive REST API client with authentication support
 *
 * Works with FastAPI backend (default) or Django backend
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  Case, Document, Claim, Contradiction, BiasSignal,
  TimelineEvent, ToulminArgument, Entity, LegalRule,
  AnalysisRun, DashboardStats, CaseStats, PaginatedResponse
} from '../types';

// FastAPI backend (default) or Django backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'phronesis_access_token';
const REFRESH_TOKEN_KEY = 'phronesis_refresh_token';

// Error types for better handling
export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, string[]>;
}

// Auth types
export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}

// Token management
export const tokenManager = {
  getAccessToken: (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),

  setTokens: (tokens: AuthTokens): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  },

  clearTokens: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  isAuthenticated: (): boolean => !!localStorage.getItem(ACCESS_TOKEN_KEY),
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenManager.getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors and token refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenManager.getRefreshToken();
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          const { access } = response.data;
          localStorage.setItem(ACCESS_TOKEN_KEY, access);
          processQueue(null, access);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access}`;
          }
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError as AxiosError, null);
          tokenManager.clearTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      } else {
        tokenManager.clearTokens();
        window.location.href = '/login';
      }
    }

    // Format error message for display
    const apiError: ApiError = error.response?.data || {
      error: error.message || 'An unexpected error occurred',
      code: 'network_error',
    };

    // Don't log sensitive auth errors in production
    if (process.env.NODE_ENV !== 'production') {
      console.error('API Error:', apiError);
    }

    return Promise.reject(apiError);
  }
);

// ============================================================================
// Authentication API
// ============================================================================

export const authApi = {
  login: async (username: string, password: string): Promise<AuthTokens> => {
    const { data } = await axios.post(`${API_BASE_URL}/auth/token/`, {
      username,
      password,
    });
    tokenManager.setTokens(data);
    return data;
  },

  logout: (): void => {
    tokenManager.clearTokens();
  },

  refreshToken: async (): Promise<string> => {
    const refreshToken = tokenManager.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token');

    const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
      refresh: refreshToken,
    });
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
    return data.access;
  },

  getUser: async (): Promise<UserInfo> => {
    const { data } = await api.get('/auth/user/');
    return data;
  },

  isAuthenticated: (): boolean => tokenManager.isAuthenticated(),
};

// ============================================================================
// Cases API
// ============================================================================

export const casesApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<Case>> => {
    const { data } = await api.get('/cases/', { params });
    return data;
  },

  get: async (id: string): Promise<Case> => {
    const { data } = await api.get(`/cases/${id}/`);
    return data;
  },

  create: async (caseData: Partial<Case>): Promise<Case> => {
    const { data } = await api.post('/cases/', caseData);
    return data;
  },

  update: async (id: string, caseData: Partial<Case>): Promise<Case> => {
    const { data } = await api.patch(`/cases/${id}/`, caseData);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/cases/${id}/`);
  },

  getStats: async (id: string): Promise<CaseStats> => {
    const { data } = await api.get(`/cases/${id}/stats/`);
    return data;
  },

  analyze: async (id: string): Promise<{ run_id: string; message: string }> => {
    const { data } = await api.post(`/cases/${id}/analyze/`);
    return data;
  },

  getSummary: async (id: string) => {
    const { data } = await api.get(`/cases/${id}/summary/`);
    return data;
  },

  getDashboard: async (): Promise<DashboardStats> => {
    const { data } = await api.get('/cases/dashboard/');
    return data;
  },
};

// ============================================================================
// Documents API
// ============================================================================

export const documentsApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<Document>> => {
    const { data } = await api.get('/documents/', { params });
    return data;
  },

  get: async (id: string): Promise<Document> => {
    const { data } = await api.get(`/documents/${id}/`);
    return data;
  },

  upload: async (caseId: string, file: File, metadata: Record<string, unknown>): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('case_id', caseId);
    Object.entries(metadata).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, String(value));
      }
    });

    const { data } = await api.post('/documents/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 2 min for uploads
    });
    return data;
  },

  getContent: async (id: string) => {
    const { data } = await api.get(`/documents/${id}/content/`);
    return data;
  },

  analyze: async (id: string): Promise<{ message: string }> => {
    const { data } = await api.post(`/documents/${id}/analyze/`);
    return data;
  },

  forCase: async (caseId: string, params?: Record<string, unknown>): Promise<PaginatedResponse<Document>> => {
    const { data } = await api.get(`/cases/${caseId}/documents/`, { params });
    return data;
  },

  statsForCase: async (caseId: string) => {
    const { data } = await api.get(`/cases/${caseId}/documents/stats/`);
    return data;
  },
};

// ============================================================================
// Claims API
// ============================================================================

export const claimsApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<Claim>> => {
    const { data } = await api.get('/claims/', { params });
    return data;
  },

  get: async (id: string): Promise<Claim> => {
    const { data } = await api.get(`/claims/${id}/`);
    return data;
  },

  forCase: async (caseId: string, params?: Record<string, unknown>): Promise<PaginatedResponse<Claim>> => {
    const { data } = await api.get(`/cases/${caseId}/claims/`, { params });
    return data;
  },
};

// ============================================================================
// Contradictions API
// ============================================================================

export const contradictionsApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<Contradiction>> => {
    const { data } = await api.get('/contradictions/', { params });
    return data;
  },

  get: async (id: string): Promise<Contradiction> => {
    const { data } = await api.get(`/contradictions/${id}/`);
    return data;
  },

  resolve: async (id: string, note: string): Promise<Contradiction> => {
    const { data } = await api.post(`/contradictions/${id}/resolve/`, { note });
    return data;
  },

  forCase: async (caseId: string, params?: Record<string, unknown>): Promise<PaginatedResponse<Contradiction>> => {
    const { data } = await api.get(`/cases/${caseId}/contradictions/`, { params });
    return data;
  },

  detect: async (caseId: string): Promise<{
    run_id: string;
    status: string;
    contradictions_found?: number;
    claims_analyzed?: number;
    message?: string;
  }> => {
    const { data } = await api.post(`/cases/${caseId}/detect-contradictions/`);
    return data;
  },

  getSummary: async (caseId: string) => {
    const { data } = await api.get(`/cases/${caseId}/contradiction-summary/`);
    return data;
  },
};

// ============================================================================
// Bias Signals API
// ============================================================================

export const biasApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<BiasSignal>> => {
    const { data } = await api.get('/bias-signals/', { params });
    return data;
  },

  forCase: async (caseId: string, params?: Record<string, unknown>): Promise<PaginatedResponse<BiasSignal>> => {
    const { data } = await api.get(`/cases/${caseId}/bias-signals/`, { params });
    return data;
  },

  getReport: async (caseId: string) => {
    const { data } = await api.get(`/cases/${caseId}/bias-report/`);
    return data;
  },
};

// ============================================================================
// Timeline API
// ============================================================================

export const timelineApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<TimelineEvent>> => {
    const { data } = await api.get('/timeline/', { params });
    return data;
  },

  forCase: async (caseId: string): Promise<PaginatedResponse<TimelineEvent>> => {
    const { data } = await api.get(`/cases/${caseId}/timeline/`);
    return data;
  },

  getConflicts: async (caseId: string) => {
    const { data } = await api.get(`/cases/${caseId}/timeline/conflicts/`);
    return data;
  },
};

// ============================================================================
// Arguments API
// ============================================================================

export const argumentsApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<ToulminArgument>> => {
    const { data } = await api.get('/arguments/', { params });
    return data;
  },

  forCase: async (caseId: string): Promise<PaginatedResponse<ToulminArgument>> => {
    const { data } = await api.get(`/cases/${caseId}/arguments/`);
    return data;
  },

  generate: async (caseId: string, findingType: string, claimText?: string): Promise<{
    argument_id: string;
    argument: ToulminArgument;
  }> => {
    const { data } = await api.post(`/cases/${caseId}/generate-arguments/`, {
      finding_type: findingType,
      claim_text: claimText,
    });
    return data;
  },
};

// ============================================================================
// Entities API
// ============================================================================

export const entitiesApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<Entity>> => {
    const { data } = await api.get('/entities/', { params });
    return data;
  },

  forCase: async (caseId: string): Promise<PaginatedResponse<Entity>> => {
    const { data } = await api.get(`/cases/${caseId}/entities/`);
    return data;
  },

  getGraph: async (caseId: string) => {
    const { data } = await api.get(`/cases/${caseId}/entity-graph/`);
    return data;
  },
};

// ============================================================================
// Legal Rules API
// ============================================================================

export const legalRulesApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<LegalRule>> => {
    const { data } = await api.get('/legal-rules/', { params });
    return data;
  },

  get: async (id: string): Promise<LegalRule> => {
    const { data } = await api.get(`/legal-rules/${id}/`);
    return data;
  },
};

// ============================================================================
// Analysis Runs API
// ============================================================================

export const analysisRunsApi = {
  list: async (params?: Record<string, unknown>): Promise<PaginatedResponse<AnalysisRun>> => {
    const { data } = await api.get('/analysis-runs/', { params });
    return data;
  },

  get: async (id: string): Promise<AnalysisRun> => {
    const { data } = await api.get(`/analysis-runs/${id}/`);
    return data;
  },

  forCase: async (caseId: string): Promise<PaginatedResponse<AnalysisRun>> => {
    const { data } = await api.get(`/cases/${caseId}/analysis-runs/`);
    return data;
  },
};

// ============================================================================
// AI Subscription Workflow API (Prompt Generation & Response Parsing)
// ============================================================================

export interface PromptType {
  type: string;
  description: string;
}

export interface GeneratedPrompt {
  prompt_id: string;
  prompt_type: string;
  document?: string;
  full_prompt: string;
  estimated_tokens: number;
  recommended_platforms: string[];
  notes: string;
  instructions?: string;
}

export interface ParseResult {
  success: boolean;
  prompt_type: string;
  parsed_at?: string;
  errors?: string[];
  warnings?: string[];
  stored?: { claims: number; events: number; other: number };
  data?: Record<string, unknown>;
  partial_data?: Record<string, unknown>;
}

export interface WorkflowStatus {
  case_id: string;
  status: {
    documents: number;
    claims_total: number;
    claims_imported: number;
    timeline_events: number;
    contradictions_analyzed: number;
  };
  workflow_progress: {
    documents_uploaded: boolean;
    claims_extracted: boolean;
    timeline_built: boolean;
    contradictions_analyzed: boolean;
  };
  recommended_next_steps: Array<{
    priority: number;
    action: string;
    endpoint: string;
  }>;
}

export const promptsApi = {
  // List available prompt types
  listTypes: async (): Promise<{ types: PromptType[]; workflow: Record<string, unknown> }> => {
    const { data } = await api.get('/prompts/types');
    return data;
  },

  // Generate prompts for different analysis types
  generateClaimExtraction: async (docId: string): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('doc_id', docId);
    const { data } = await api.post('/prompts/generate/claim-extraction', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  generateDocumentSummary: async (docId: string): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('doc_id', docId);
    const { data } = await api.post('/prompts/generate/document-summary', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  generateCredibilityAssessment: async (
    docId: string,
    author: string,
    documentType: string = 'statement'
  ): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('doc_id', docId);
    formData.append('author', author);
    formData.append('document_type', documentType);
    const { data } = await api.post('/prompts/generate/credibility-assessment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  generateClaimAnalysis: async (claimId: string): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('claim_id', claimId);
    const { data } = await api.post('/prompts/generate/claim-analysis', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  generateContradictionAnalysis: async (claimAId: string, claimBId: string): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('claim_a_id', claimAId);
    formData.append('claim_b_id', claimBId);
    const { data } = await api.post('/prompts/generate/contradiction-analysis', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  generateTimeline: async (caseId: string, docIds?: string[]): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('case_id', caseId);
    if (docIds && docIds.length > 0) {
      formData.append('doc_ids', docIds.join(','));
    }
    const { data } = await api.post('/prompts/generate/timeline', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  generateLegalFramework: async (caseId: string, situation: string): Promise<GeneratedPrompt> => {
    const formData = new FormData();
    formData.append('case_id', caseId);
    formData.append('situation', situation);
    const { data } = await api.post('/prompts/generate/legal-framework', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  // Parse AI responses
  parseResponse: async (
    responseText: string,
    promptType: string,
    caseId?: string,
    docId?: string
  ): Promise<ParseResult> => {
    const formData = new FormData();
    formData.append('response_text', responseText);
    formData.append('prompt_type', promptType);
    if (caseId) formData.append('case_id', caseId);
    if (docId) formData.append('doc_id', docId);
    const { data } = await api.post('/prompts/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  parseBatch: async (
    responses: Array<{ response_text: string; prompt_type: string; doc_id?: string }>,
    caseId?: string
  ): Promise<{
    total_processed: number;
    successful: number;
    stored?: { claims: number; events: number };
    results: Array<{ prompt_type: string; success: boolean; claims_count: number; errors: string[] }>;
  }> => {
    const formData = new FormData();
    formData.append('responses', JSON.stringify(responses));
    if (caseId) formData.append('case_id', caseId);
    const { data } = await api.post('/prompts/parse/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  // Get workflow status
  getWorkflowStatus: async (caseId: string): Promise<WorkflowStatus> => {
    const { data } = await api.get(`/prompts/workflow-status/${caseId}`);
    return data;
  },
};

export default api;
