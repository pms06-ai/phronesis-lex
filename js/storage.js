// Local Storage Persistence
const storage = {
    PREFIX: 'phronesis_',

    save(key, data) {
        try {
            localStorage.setItem(this.PREFIX + key, JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('Storage save failed:', e);
            return false;
        }
    },

    load(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(this.PREFIX + key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (e) {
            console.error('Storage load failed:', e);
            return defaultValue;
        }
    },

    remove(key) {
        localStorage.removeItem(this.PREFIX + key);
    },

    saveUserData(caseId, data) {
        this.save(`case_${caseId}_user`, data);
    },

    loadUserData(caseId) {
        return this.load(`case_${caseId}_user`, null);
    },

    savePrefs(prefs) {
        this.save('prefs', prefs);
    },

    loadPrefs() {
        return this.load('prefs', { currentPage: 'dashboard', assistantOpen: true });
    }
};
