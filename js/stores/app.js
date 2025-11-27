// App Store - Navigation, UI state, preferences
function registerAppStore() {
    const savedPrefs = storage.loadPrefs();

    Alpine.store('app', {
        currentPage: savedPrefs.currentPage || 'dashboard',
        assistantOpen: savedPrefs.assistantOpen !== false,
        sidebarCollapsed: savedPrefs.sidebarCollapsed || false,
        lastSaved: null,

        // Modal state
        modal: {
            open: false,
            type: null,  // 'task', 'violation', 'note'
            data: {}
        },

        openModal(type, data = {}) {
            this.modal = { open: true, type, data };
        },

        closeModal() {
            this.modal = { open: false, type: null, data: {} };
        },

        // Navigation with status indicators: LIVE = real data, MOCK = placeholder data, STUB = UI only
        navConfig: [
            { id: 'dashboard', icon: 'dashboard', label: 'Dashboard', status: 'live' },
            { section: 'Investigation Hub' },
            { id: 'subject-profiler', icon: 'person_search', label: 'Subject Profiler', status: 'hybrid' },
            { id: 'case-workflow', icon: 'account_tree', label: 'Case Workflow', status: 'mock' },
            { id: 'violation-matrix', icon: 'grid_view', label: 'Violation Matrix', status: 'mock' },
            { id: 'forensic-timeline', icon: 'timeline', label: 'Forensic Timeline', status: 'mock' },
            { section: 'Analytics Hub' },
            { id: 'data-visualizer', icon: 'bar_chart', label: 'Data Visualizer', status: 'hybrid' },
            { id: 'tone-analysis', icon: 'psychology', label: 'Tone Analysis', status: 'stub' },
            { section: 'Workspace Hub', badge: 'LOCAL' },
            { id: 'evidence-drive', icon: 'folder_open', label: 'Evidence Drive', status: 'live' },
            { id: 'report-docs', icon: 'description', label: 'Report Docs', status: 'stub' },
            { id: 'data-sheets', icon: 'table_chart', label: 'Data Sheets', status: 'live' },
            { section: 'Evidence Hub' },
            { id: 'entity-map', icon: 'hub', label: 'Entity Map', status: 'live' },
            { id: 'doc-comparator', icon: 'compare', label: 'Doc Comparator', status: 'stub' },
        ],

        savePrefs() {
            storage.savePrefs({
                currentPage: this.currentPage,
                assistantOpen: this.assistantOpen,
                sidebarCollapsed: this.sidebarCollapsed
            });
            this.lastSaved = new Date().toISOString();
        },

        navigateTo(pageId) {
            this.currentPage = pageId;
            this.savePrefs();
        },

        toggleAssistant() {
            this.assistantOpen = !this.assistantOpen;
            this.savePrefs();
        },

        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            this.savePrefs();
        }
    });
}
