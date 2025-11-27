// Phronesis LEX API Service
// Connects frontend to FastAPI backend (local or Vercel deployment)

// Auto-detect API base URL based on environment
const getApiBase = () => {
    const hostname = window.location.hostname;

    // Production (Vercel deployment)
    if (hostname.includes('vercel.app') || hostname.includes('phronesis')) {
        return '';  // Same origin - API routes handled by Vercel
    }

    // Local development
    return 'http://127.0.0.1:8000';
};

const api = {
    // Configuration
    baseUrl: getApiBase(),
    isConnected: false,
    isProduction: window.location.hostname.includes('vercel.app'),

    // Generic request handler
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Remove Content-Type for FormData
        if (options.body instanceof FormData) {
            delete config.headers['Content-Type'];
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },

    // Health check
    async checkHealth() {
        try {
            const result = await this.request('/health');
            this.isConnected = result.status === 'healthy';
            return result;
        } catch (error) {
            this.isConnected = false;
            return { status: 'disconnected', error: error.message };
        }
    },

    // ========== Cases ==========
    cases: {
        async list() {
            return api.request('/api/cases');
        },

        async get(caseId) {
            return api.request(`/api/cases/${caseId}`);
        },

        async create(data) {
            const formData = new FormData();
            Object.entries(data).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    formData.append(key, value);
                }
            });
            return api.request('/api/cases', {
                method: 'POST',
                body: formData
            });
        }
    },

    // ========== Documents ==========
    documents: {
        async list(caseId) {
            return api.request(`/api/cases/${caseId}/documents`);
        },

        async get(docId, includeText = false) {
            return api.request(`/api/documents/${docId}?include_text=${includeText}`);
        },

        async getText(docId) {
            return api.request(`/api/documents/${docId}/text`);
        },

        async upload(caseId, file, folder = null, docType = null) {
            const formData = new FormData();
            formData.append('file', file);
            if (folder) formData.append('folder', folder);
            if (docType) formData.append('doc_type', docType);

            return api.request(`/api/cases/${caseId}/documents`, {
                method: 'POST',
                body: formData
            });
        },

        async analyze(docId) {
            return api.request(`/api/documents/${docId}/analyze`, {
                method: 'POST'
            });
        },

        async detectBiases(docId) {
            return api.request(`/api/documents/${docId}/detect-biases`, {
                method: 'POST'
            });
        }
    },

    // ========== Claims ==========
    claims: {
        async list(caseId, claimType = null) {
            let url = `/api/cases/${caseId}/claims`;
            if (claimType) url += `?claim_type=${claimType}`;
            return api.request(url);
        }
    },

    // ========== Timeline ==========
    timeline: {
        async get(caseId) {
            return api.request(`/api/cases/${caseId}/timeline`);
        }
    },

    // ========== Biases ==========
    biases: {
        async list(caseId) {
            return api.request(`/api/cases/${caseId}/biases`);
        }
    },

    // ========== Professionals ==========
    professionals: {
        async list(caseId) {
            return api.request(`/api/cases/${caseId}/professionals`);
        },

        async create(data) {
            const formData = new FormData();
            Object.entries(data).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    formData.append(key, value);
                }
            });
            return api.request('/api/professionals', {
                method: 'POST',
                body: formData
            });
        }
    },

    // ========== AI Chat (Direct Claude API through backend) ==========
    chat: {
        async sendMessage(message, caseContext = null) {
            // For now, this will be handled by the chat store
            // In future, add a dedicated chat endpoint
            return api.request('/api/chat', {
                method: 'POST',
                body: JSON.stringify({ message, case_context: caseContext })
            });
        }
    }
};

// Export for use in other modules
window.phronesisApi = api;
