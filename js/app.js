// Phronesis LEX - Main Application Initialization

// Register all Alpine.js components and stores
document.addEventListener('alpine:init', () => {
    // Register Components
    registerEvidenceDrive();
    registerEntityMap();
    registerDataVisualizer();

    // Register Stores
    registerAppStore();
    registerCaseStore();
    registerChatStore();
});

// Initialize application after Alpine is ready
document.addEventListener('alpine:initialized', () => {
    Alpine.store('case').loadCase('PE23C50095');
    Alpine.store('chat').init();
});
