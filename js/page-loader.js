/**
 * Page Loader for Phronesis LEX
 * Dynamically loads page templates from separate HTML files
 */

const PageLoader = {
    cache: {},
    containerSelector: '#page-container',
    
    /**
     * Available pages and their template paths
     */
    pages: {
        'dashboard': 'templates/pages/dashboard.html',
        'subject-profiler': 'templates/pages/subject-profiler.html',
        'case-workflow': 'templates/pages/case-workflow.html',
        'violation-matrix': 'templates/pages/violation-matrix.html',
        'forensic-timeline': 'templates/pages/forensic-timeline.html',
        'evidence-drive': 'templates/pages/evidence-drive.html',
        'entity-map': 'templates/pages/entity-map.html',
        'data-sheets': 'templates/pages/data-sheets.html',
        'data-visualizer': 'templates/pages/data-visualizer.html',
        'doc-comparator': 'templates/pages/doc-comparator.html',
        'report-docs': 'templates/pages/report-docs.html',
        'tone-analysis': 'templates/pages/tone-analysis.html'
    },
    
    /**
     * Load a page template
     * @param {string} pageId - The page identifier
     * @returns {Promise<string>} The HTML content
     */
    async load(pageId) {
        // Return cached if available
        if (this.cache[pageId]) {
            return this.cache[pageId];
        }
        
        const path = this.pages[pageId];
        if (!path) {
            console.warn(`Unknown page: ${pageId}`);
            return this.getFallbackContent(pageId);
        }
        
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`Failed to load ${path}: ${response.status}`);
            }
            const html = await response.text();
            this.cache[pageId] = html;
            return html;
        } catch (error) {
            console.error(`Error loading page ${pageId}:`, error);
            return this.getFallbackContent(pageId);
        }
    },
    
    /**
     * Render a page into the container
     * @param {string} pageId - The page identifier
     */
    async render(pageId) {
        const container = document.querySelector(this.containerSelector);
        if (!container) {
            console.error('Page container not found');
            return;
        }
        
        // Show loading state
        container.innerHTML = `
            <div class="flex items-center justify-center h-full">
                <div class="text-center">
                    <span class="material-symbols-outlined text-4xl text-accent-brass animate-pulse">hourglass_top</span>
                    <p class="text-sm text-gray-500 mt-2 font-mono">Loading...</p>
                </div>
            </div>
        `;
        
        const html = await this.load(pageId);
        container.innerHTML = html;
        
        // Re-initialize Alpine on new content
        if (window.Alpine) {
            Alpine.initTree(container);
        }
    },
    
    /**
     * Get fallback content for unknown/error pages
     * @param {string} pageId - The page identifier
     * @returns {string} Fallback HTML
     */
    getFallbackContent(pageId) {
        return `
            <div class="h-full flex items-center justify-center">
                <div class="text-center">
                    <span class="material-symbols-outlined text-6xl text-accent-brass mb-4">construction</span>
                    <h2 class="font-display text-2xl text-white mb-2">${this.formatPageName(pageId)}</h2>
                    <p class="text-sm text-gray-500 font-mono">This module is under development</p>
                    <p class="text-xs text-gray-600 font-mono mt-2">Page ID: ${pageId}</p>
                </div>
            </div>
        `;
    },
    
    /**
     * Format page ID to display name
     * @param {string} pageId - The page identifier
     * @returns {string} Formatted name
     */
    formatPageName(pageId) {
        return pageId
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    },
    
    /**
     * Preload all pages into cache
     */
    async preloadAll() {
        const promises = Object.keys(this.pages).map(pageId => this.load(pageId));
        await Promise.all(promises);
        console.log('All pages preloaded');
    }
};

// Export for use in Alpine stores
window.PageLoader = PageLoader;

