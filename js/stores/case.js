// Case Store - Case data, tasks, violations, timeline
// Now supports real extracted data from investigation-engine
function registerCaseStore() {
    Alpine.store('case', {
        activeCase: null,
        loading: false,
        error: null,
        subjects: [],
        violations: [],
        timeline: [],
        tasks: [],
        documents: [],
        entities: [],
        userNotes: [],

        // Real data from extraction
        entityExtractions: [],
        uniqueEntities: [],
        relationships: [],
        extractionStats: {},

        get violationStats() {
            return {
                total: this.violations.length,
                critical: this.violations.filter(v => v.severity === 'critical').length,
                high: this.violations.filter(v => v.severity === 'high').length,
                medium: this.violations.filter(v => v.severity === 'medium').length,
                low: this.violations.filter(v => v.severity === 'low').length
            };
        },

        get taskStats() {
            return {
                todo: this.tasks.filter(t => t.status === 'todo').length,
                inProgress: this.tasks.filter(t => t.status === 'in_progress').length,
                review: this.tasks.filter(t => t.status === 'review').length,
                completed: this.tasks.filter(t => t.status === 'completed').length,
                total: this.tasks.length
            };
        },

        get tasksByStatus() {
            return {
                todo: this.tasks.filter(t => t.status === 'todo'),
                in_progress: this.tasks.filter(t => t.status === 'in_progress'),
                review: this.tasks.filter(t => t.status === 'review'),
                completed: this.tasks.filter(t => t.status === 'completed')
            };
        },

        get dashboardStats() {
            // Use real extraction stats if available
            const docCount = this.extractionStats.documents || this.documents.length;
            const entityCount = this.extractionStats.uniqueEntities || this.entities.length;

            return {
                documents: docCount,
                documentProgress: Math.min(100, (docCount / 60) * 100),
                complianceStatus: this.violationStats.critical > 0 ? 'Critical' : this.violationStats.high > 0 ? 'High Risk' : 'Compliant',
                reportStatus: 'Draft',
                aiConfidence: 92,
                // Real data stats
                totalExtractions: this.extractionStats.totalExtractions || 0,
                uniqueEntityCount: entityCount,
                relationshipCount: this.relationships.length
            };
        },

        get primarySubject() {
            return this.subjects.find(s => s.isPrimary) || this.subjects[0];
        },

        // Get unique entities by type
        getEntitiesByType(type) {
            return this.uniqueEntities.filter(e => e.type === type);
        },

        // Get extractions for a specific document
        getExtractionsForDocument(documentId) {
            return this.entityExtractions.filter(e => e.documentId === documentId);
        },

        // Get relationships for a specific entity
        getRelationshipsForEntity(entityId) {
            return this.relationships.filter(r => r.from === entityId || r.to === entityId);
        },

        // Persistence methods
        saveUserData() {
            if (!this.activeCase) return;
            storage.saveUserData(this.activeCase.id, {
                tasks: this.tasks,
                violations: this.violations,
                userNotes: this.userNotes,
                savedAt: new Date().toISOString()
            });
        },

        loadUserData() {
            if (!this.activeCase) return;
            const userData = storage.loadUserData(this.activeCase.id);
            if (userData) {
                this.tasks = userData.tasks || this.tasks;
                this.violations = userData.violations || this.violations;
                this.userNotes = userData.userNotes || [];
            }
        },

        // Task management
        addTask(task) {
            const newTask = {
                id: Date.now(),
                ...task,
                createdAt: new Date().toISOString()
            };
            this.tasks.push(newTask);
            this.saveUserData();
            return newTask;
        },

        updateTask(taskId, updates) {
            const idx = this.tasks.findIndex(t => t.id === taskId);
            if (idx !== -1) {
                this.tasks[idx] = { ...this.tasks[idx], ...updates };
                this.saveUserData();
            }
        },

        deleteTask(taskId) {
            this.tasks = this.tasks.filter(t => t.id !== taskId);
            this.saveUserData();
        },

        moveTask(taskId, newStatus) {
            this.updateTask(taskId, { status: newStatus });
        },

        // Violation management
        addViolation(violation) {
            const newViolation = {
                id: 'V-' + String(this.violations.length + 1).padStart(3, '0'),
                ...violation,
                date: new Date().toISOString().split('T')[0]
            };
            this.violations.push(newViolation);
            this.saveUserData();
            return newViolation;
        },

        updateViolation(violationId, updates) {
            const idx = this.violations.findIndex(v => v.id === violationId);
            if (idx !== -1) {
                this.violations[idx] = { ...this.violations[idx], ...updates };
                this.saveUserData();
            }
        },

        // Notes management
        addNote(note) {
            this.userNotes.push({
                id: Date.now(),
                content: note,
                createdAt: new Date().toISOString()
            });
            this.saveUserData();
        },

        async loadCase(caseId) {
            this.loading = true;
            this.error = null;
            try {
                // Check if real data is available
                if (typeof realCaseData !== 'undefined' && realCaseData.case.id === caseId) {
                    // Load from real extracted data
                    this.activeCase = realCaseData.case;
                    this.entityExtractions = realCaseData.entityExtractions || [];
                    this.uniqueEntities = realCaseData.uniqueEntities || [];
                    this.relationships = realCaseData.relationships || [];
                    this.extractionStats = realCaseData.stats || {};

                    // Map documents from real data
                    this.documents = realCaseData.documents || [];

                    // Map unique entities to the entities array for backward compatibility
                    this.entities = this.uniqueEntities.filter(e => e.type !== 'DATE').map(e => ({
                        id: e.id,
                        name: e.name,
                        type: this.mapEntityType(e.type),
                        connectionStrength: Math.min(100, e.occurrences * 5),
                        occurrences: e.occurrences,
                        documents: e.documents
                    }));

                    // Create subjects from key entities (judges, authorities)
                    this.subjects = this.createSubjectsFromEntities();

                    // Load mock data for violations, tasks, timeline (not in extraction)
                    const mockData = await api.getCase(caseId);
                    this.violations = mockData.violations || [];
                    this.tasks = mockData.tasks || [];
                    this.timeline = mockData.timeline || [];

                    console.log(`Loaded real data: ${this.entityExtractions.length} extractions, ${this.uniqueEntities.length} unique entities`);
                } else {
                    // Fallback to mock data
                    const data = await api.getCase(caseId);
                    this.activeCase = data.case;
                    this.subjects = data.subjects || [];
                    this.violations = data.violations || [];
                    this.timeline = data.timeline || [];
                    this.tasks = data.tasks || [];
                    this.documents = data.documents || [];
                    this.entities = data.entities || [];
                }

                // Load any user modifications on top of base data
                this.loadUserData();
            } catch (err) {
                this.error = err.message;
                console.error('Failed to load case:', err);
            } finally {
                this.loading = false;
            }
        },

        // Map extraction entity types to display types
        mapEntityType(extractionType) {
            const typeMap = {
                'UK_JUDGE': 'person',
                'UK_LOCAL_AUTHORITY': 'organization',
                'UK_POLICE_FORCE': 'organization',
                'UK_COURT': 'institution',
                'CASE_NUMBER': 'case',
                'SOLICITOR_FIRM': 'organization',
                'DATE': 'date'
            };
            return typeMap[extractionType] || 'other';
        },

        // Create subject profiles from key entities
        createSubjectsFromEntities() {
            const subjects = [];

            // Get judges
            const judges = this.uniqueEntities.filter(e => e.type === 'UK_JUDGE').slice(0, 3);
            judges.forEach((judge, idx) => {
                subjects.push({
                    id: subjects.length + 1,
                    name: judge.name,
                    role: 'Judge',
                    isPrimary: idx === 0,
                    riskScore: 0,
                    riskLevel: 'Low',
                    status: 'Active',
                    profile: {
                        position: 'Family Court Judge',
                        organization: 'HM Courts & Tribunals Service',
                        occurrences: judge.occurrences
                    },
                    flags: []
                });
            });

            // Get local authorities
            const authorities = this.uniqueEntities.filter(e => e.type === 'UK_LOCAL_AUTHORITY');
            authorities.forEach(auth => {
                subjects.push({
                    id: subjects.length + 1,
                    name: auth.name,
                    role: 'Local Authority',
                    isPrimary: false,
                    riskScore: 45,
                    riskLevel: 'Medium',
                    status: 'Under Review',
                    profile: {
                        position: 'Applicant',
                        organization: auth.name,
                        occurrences: auth.occurrences
                    },
                    flags: ['Case Management']
                });
            });

            // Get police forces
            const police = this.uniqueEntities.filter(e => e.type === 'UK_POLICE_FORCE');
            police.forEach(p => {
                subjects.push({
                    id: subjects.length + 1,
                    name: p.name,
                    role: 'Police Force',
                    isPrimary: false,
                    riskScore: 30,
                    riskLevel: 'Low',
                    status: 'Disclosure Provider',
                    profile: {
                        position: 'Third Party',
                        organization: p.name,
                        occurrences: p.occurrences
                    },
                    flags: []
                });
            });

            return subjects;
        }
    });
}
