// Chat Store - AI Assistant conversation
// Connects to backend Claude API when available, falls back to demo mode
// "The first step to wisdom is getting things by their right names." - Epictetus
function registerChatStore() {
    Alpine.store('chat', {
        messages: [],
        isTyping: false,
        inputValue: '',
        isDemo: true,
        backendConnected: false,
        aiEnabled: false,

        async init() {
            // Check backend connection
            await this.checkBackendStatus();

            // Initial messages based on connection status
            if (this.backendConnected && this.aiEnabled) {
                this.messages = [
                    {
                        id: 1,
                        role: 'system',
                        content: "Connected to Phronesis LEX Backend. AI analysis is enabled.",
                        timestamp: new Date().toISOString()
                    },
                    {
                        id: 2,
                        role: 'assistant',
                        content: "Phronesis LEX ready. I can analyze documents, extract claims, detect biases, and help you investigate case evidence. Upload documents or ask me about the current case data.",
                        timestamp: new Date().toISOString()
                    }
                ];
                this.isDemo = false;
            } else if (this.backendConnected) {
                this.messages = [
                    {
                        id: 1,
                        role: 'system',
                        content: "Backend connected but AI analysis not configured. Set ANTHROPIC_API_KEY to enable.",
                        timestamp: new Date().toISOString()
                    },
                    {
                        id: 2,
                        role: 'assistant',
                        content: "Backend is connected. Document upload and storage are available. AI analysis requires API key configuration.",
                        timestamp: new Date().toISOString()
                    }
                ];
                this.isDemo = true;
            } else {
                this.messages = [
                    {
                        id: 1,
                        role: 'system',
                        content: "Demo Mode: Backend not connected. Start the backend server for full functionality.",
                        timestamp: new Date().toISOString()
                    },
                    {
                        id: 2,
                        role: 'assistant',
                        content: "Case PE23C50095 loaded with pre-extracted data. Entity Map and Data Sheets show real extracted entities. Start the backend (python backend/app.py) for AI analysis.",
                        timestamp: new Date().toISOString()
                    }
                ];
                this.isDemo = true;
            }
        },

        async checkBackendStatus() {
            if (!window.phronesisApi) {
                this.backendConnected = false;
                this.aiEnabled = false;
                return;
            }

            try {
                const health = await window.phronesisApi.checkHealth();
                this.backendConnected = health.status === 'healthy';
                this.aiEnabled = health.ai_configured === true;
            } catch (e) {
                this.backendConnected = false;
                this.aiEnabled = false;
            }
        },

        async sendMessage(content) {
            if (!content || !content.trim()) return;

            // Add user message
            this.messages.push({
                id: Date.now(),
                role: 'user',
                content: content.trim(),
                timestamp: new Date().toISOString()
            });

            this.inputValue = '';
            this.isTyping = true;

            let response = '';

            // Try backend first if connected
            if (this.backendConnected && this.aiEnabled) {
                try {
                    response = await this.getAIResponse(content);
                } catch (error) {
                    response = `Error connecting to AI: ${error.message}. Falling back to local response.`;
                    response += '\n\n' + this.getDemoResponse(content);
                }
            } else {
                // Demo mode
                await new Promise(resolve => setTimeout(resolve, 800));
                response = this.getDemoResponse(content);
            }

            this.messages.push({
                id: Date.now() + 1,
                role: 'assistant',
                content: response,
                timestamp: new Date().toISOString()
            });

            this.isTyping = false;
        },

        async getAIResponse(content) {
            // For now, route specific commands to appropriate API endpoints
            const lowerContent = content.toLowerCase();
            const caseStore = Alpine.store('case');

            // Command: analyze document
            if (lowerContent.includes('analyze') && lowerContent.includes('document')) {
                // Get recent documents
                const docs = caseStore.documents || [];
                if (docs.length === 0) {
                    return "No documents loaded. Upload documents first using the Evidence Drive.";
                }
                return `Ready to analyze ${docs.length} documents. Use the Document panel to select and analyze specific documents, or I can provide an overview of the case data.`;
            }

            // Command: show claims
            if (lowerContent.includes('claim') || lowerContent.includes('assertion') || lowerContent.includes('allegation')) {
                const claims = caseStore.claims || [];
                if (claims.length === 0) {
                    return "No claims extracted yet. Run document analysis to extract claims from case documents.";
                }
                const byType = {};
                claims.forEach(c => { byType[c.claim_type] = (byType[c.claim_type] || 0) + 1; });
                const summary = Object.entries(byType).map(([t, n]) => `${t}: ${n}`).join(', ');
                return `Found ${claims.length} claims across the case documents:\n${summary}\n\nView the Claims Analyzer for detailed evidence mapping.`;
            }

            // Command: timeline
            if (lowerContent.includes('timeline') || lowerContent.includes('chronolog') || lowerContent.includes('event')) {
                const events = caseStore.timeline || [];
                if (events.length === 0) {
                    return "No timeline events extracted yet. Run document analysis to build the case timeline.";
                }
                return `Timeline contains ${events.length} events. The Forensic Timeline page shows chronological reconstruction with decision point analysis.`;
            }

            // Command: biases
            if (lowerContent.includes('bias') || lowerContent.includes('manipulation')) {
                const biases = caseStore.biases || [];
                if (biases.length === 0) {
                    return "No biases detected yet. Run bias detection analysis on case documents to identify cognitive biases and rhetorical manipulation.";
                }
                const bySeverity = { high: 0, medium: 0, low: 0 };
                biases.forEach(b => { bySeverity[b.severity] = (bySeverity[b.severity] || 0) + 1; });
                return `Detected ${biases.length} potential bias indicators:\nHigh severity: ${bySeverity.high}\nMedium severity: ${bySeverity.medium}\nLow severity: ${bySeverity.low}\n\nView the Bias Detector for detailed analysis.`;
            }

            // Command: entity/relationships
            if (lowerContent.includes('entity') || lowerContent.includes('relationship') || lowerContent.includes('map')) {
                const entities = caseStore.uniqueEntities || [];
                return `Entity Map contains ${entities.length} unique entities extracted from case documents. The visualization shows relationships based on document co-occurrence.`;
            }

            // Default: provide case overview
            return this.getCaseOverview();
        },

        getCaseOverview() {
            const caseStore = Alpine.store('case');
            const caseData = caseStore.case || {};
            const stats = {
                documents: (caseStore.documents || []).length,
                entities: (caseStore.uniqueEntities || []).length,
                claims: (caseStore.claims || []).length,
                timeline: (caseStore.timeline || []).length,
                biases: (caseStore.biases || []).length
            };

            return `**Case Overview: ${caseData.reference || 'Unknown'}**

Documents: ${stats.documents} processed
Entities: ${stats.entities} unique
Claims: ${stats.claims} extracted
Timeline Events: ${stats.timeline}
Bias Indicators: ${stats.biases}

Ask me to analyze documents, extract claims, detect biases, or explore specific aspects of the case.`;
        },

        getDemoResponse(content) {
            const lowerContent = content.toLowerCase();

            if (lowerContent.includes('entity') || lowerContent.includes('map')) {
                return "The Entity Map displays 386 unique entities extracted from case documents. Navigate to Entity Map to explore relationships between judges, courts, local authorities, and case references.";
            }
            if (lowerContent.includes('document') || lowerContent.includes('data')) {
                return "Data Sheets contains three tabs: Entities (386 unique), Extractions (4,135 instances), and Documents (53 processed). Use search and export features to analyze the data.";
            }
            if (lowerContent.includes('claim') || lowerContent.includes('assert')) {
                return "[Demo] Claims analysis requires backend AI. When connected, I can extract and analyze all assertions, allegations, and findings from documents.";
            }
            if (lowerContent.includes('bias') || lowerContent.includes('manipul')) {
                return "[Demo] Bias detection requires backend AI. When connected, I can identify confirmation bias, outcome bias, anchoring, and rhetorical manipulation.";
            }
            if (lowerContent.includes('timeline') || lowerContent.includes('chronolog')) {
                return "[Demo] Timeline reconstruction requires backend AI. When connected, I can extract all dated events and build a comprehensive case timeline.";
            }
            if (lowerContent.includes('help') || lowerContent.includes('what can')) {
                return `**Available with backend connected:**
- Document analysis & full text extraction
- Claims/assertions extraction with evidence links
- Bias detection (confirmation, outcome, anchoring)
- Timeline reconstruction
- Procedural compliance checking

**Currently available (demo data):**
- Entity Map with 386 entities
- Data Sheets with extraction data
- Evidence Drive for file browsing`;
            }

            const responses = [
                "Start the backend server (python backend/app.py) for full AI analysis capabilities.",
                "The Entity Map and Data Sheets contain real extracted data. Explore those while setting up the backend.",
                "Upload documents through Evidence Drive. With backend connected, I can analyze them for claims and biases.",
                "Ready for forensic analysis. Connect the backend to enable document processing and AI reasoning."
            ];
            return responses[Math.floor(Math.random() * responses.length)];
        },

        addSystemMessage(content) {
            this.messages.push({
                id: Date.now(),
                role: 'system',
                content: content,
                timestamp: new Date().toISOString()
            });
        }
    });
}
