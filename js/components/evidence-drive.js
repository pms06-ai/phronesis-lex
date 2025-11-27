// Evidence Drive Component
function registerEvidenceDrive() {
    Alpine.data('evidenceDrive', () => ({
        currentPath: [],

        get currentItems() {
            const pathKey = this.currentPath.join('/');
            return fileTree[pathKey] || fileTree[''] || [];
        },

        openFolder(name) {
            this.currentPath.push(name);
        },

        goUp() {
            this.currentPath.pop();
        },

        goToRoot() {
            this.currentPath = [];
        },

        navigateTo(idx) {
            this.currentPath = this.currentPath.slice(0, idx + 1);
        },

        openFile(item) {
            const fullPath = this.currentPath.length > 0
                ? `${FILE_BASE_PATH}/${this.currentPath.join('/')}/${item.name}`
                : `${FILE_BASE_PATH}/${item.name}`;
            window.open('file:///' + fullPath.replace(/ /g, '%20'), '_blank');
        },

        openQuickFile(relativePath) {
            const fullPath = `${FILE_BASE_PATH}/${relativePath}`;
            window.open('file:///' + fullPath.replace(/ /g, '%20'), '_blank');
        }
    }));
}
