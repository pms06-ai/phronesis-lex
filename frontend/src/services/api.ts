/**
 * API Service for Phronesis LEX
 * Comprehensive REST API client
 */
import axios from 'axios';
import type {
  Case, Document, Claim, Contradiction, BiasSignal,
  TimelineEvent, ToulminArgument, Entity, LegalRule,
  AnalysisRun, DashboardStats, CaseStats, PaginatedResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================================================
// Cases API
// ============================================================================

export const casesApi = {
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<Case>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<Document>> => {
    const { data } = await api.get('/documents/', { params });
    return data;
  },

  get: async (id: string): Promise<Document> => {
    const { data } = await api.get(`/documents/${id}/`);
    return data;
  },

  upload: async (caseId: string, file: File, metadata: any): Promise<Document> => {
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

  forCase: async (caseId: string, params?: Record<string, any>): Promise<PaginatedResponse<Document>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<Claim>> => {
    const { data } = await api.get('/claims/', { params });
    return data;
  },

  get: async (id: string): Promise<Claim> => {
    const { data } = await api.get(`/claims/${id}/`);
    return data;
  },

  forCase: async (caseId: string, params?: Record<string, any>): Promise<PaginatedResponse<Claim>> => {
    const { data } = await api.get(`/cases/${caseId}/claims/`, { params });
    return data;
  },
};

// ============================================================================
// Contradictions API
// ============================================================================

export const contradictionsApi = {
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<Contradiction>> => {
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

  forCase: async (caseId: string, params?: Record<string, any>): Promise<PaginatedResponse<Contradiction>> => {
    const { data } = await api.get(`/cases/${caseId}/contradictions/`, { params });
    return data;
  },

  detect: async (caseId: string): Promise<{
    run_id: string;
    status: string;
    contradictions_found: number;
    claims_analyzed: number;
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<BiasSignal>> => {
    const { data } = await api.get('/bias-signals/', { params });
    return data;
  },

  forCase: async (caseId: string, params?: Record<string, any>): Promise<PaginatedResponse<BiasSignal>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<TimelineEvent>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<ToulminArgument>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<Entity>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<LegalRule>> => {
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
  list: async (params?: Record<string, any>): Promise<PaginatedResponse<AnalysisRun>> => {
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

export default api;

