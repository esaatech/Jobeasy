// Dynamic Tab Management System
// Supports multiple tab types: Resume List, Cover Letters, Templates, etc.

window.tabRegistry = {
    'resume-list': {
        title: 'Resume List',
        icon: 'fas fa-file-alt',
        endpoint: '/resume/api/resume-list-tab/',
        permissions: ['authenticated'],
        cache: true // Cache the content
    },
    'cover-letter': {
        title: 'Cover Letters',
        icon: 'fas fa-envelope',
        endpoint: '/resume/api/cover-letter-tab/',
        permissions: ['authenticated'],
        cache: true
    },
    'templates': {
        title: 'Templates',
        icon: 'fas fa-palette',
        endpoint: '/resume/api/templates-tab/',
        permissions: ['authenticated'],
        cache: false // Don't cache templates
    }
    // Add more tabs here as needed
};

window.dynamicTabs = {
    openTabs: {},
    tabCache: {},

    // Main method to open a tab by its registry ID
    openTab: function(tabId, switchTo = true) {
        const tabConfig = window.tabRegistry[tabId];
        if (!tabConfig) {
            console.error(`❌ Tab "${tabId}" not found in registry`);
            return;
        }

        // Check if tab is already open
        if (this.openTabs[tabId]) {
            if (switchTo) this.switchToTab(tabId);
            return;
        }

        // Check permissions (if needed)
        if (!this.checkPermissions(tabConfig.permissions)) {
            console.error(`❌ Insufficient permissions for tab "${tabId}"`);
            return;
        }

        // Show loading state
        this.showLoadingTab(tabId, tabConfig);

        // Load tab content
        this.loadTabContent(tabId, tabConfig, switchTo);
    },

    // Load tab content from server or cache
    loadTabContent: function(tabId, tabConfig, switchTo) {
        // Check cache first
        if (tabConfig.cache && this.tabCache[tabId]) {
            this.createTab(tabId, tabConfig, this.tabCache[tabId], switchTo);
            return;
        }

        // Fetch from server
        fetch(tabConfig.endpoint, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'HX-Request': 'true'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.text();
        })
        .then(html => {
            // Cache if enabled
            if (tabConfig.cache) {
                this.tabCache[tabId] = html;
            }
            this.createTab(tabId, tabConfig, html, switchTo);
        })
        .catch(error => {
            console.error(`❌ Error loading tab "${tabId}":`, error);
            this.showErrorTab(tabId, tabConfig, error);
        });
    },

    // Create the actual tab with content
    createTab: function(tabId, tabConfig, html, switchTo) {
        // Remove loading state
        this.removeLoadingTab(tabId);

        // Add tab button
        const tabNav = document.querySelector('.tab-navigation');
        const tabBtn = document.createElement('button');
        tabBtn.className = 'tab-button';
        tabBtn.dataset.tab = tabId;
        tabBtn.innerHTML = `
            <i class="${tabConfig.icon}"></i>
            <span>${tabConfig.title}</span>
            <span class="close-tab" onclick="window.dynamicTabs.closeTab('${tabId}', event)">&times;</span>
        `;
        tabBtn.addEventListener('click', () => this.switchToTab(tabId));
        tabNav.appendChild(tabBtn);

        // Add tab content
        const rightContent = document.querySelector('.right-content');
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.id = `${tabId}-tab`;
        tabContent.innerHTML = html;
        rightContent.appendChild(tabContent);

        this.openTabs[tabId] = { 
            btn: tabBtn, 
            content: tabContent, 
            config: tabConfig 
        };

        if (switchTo) this.switchToTab(tabId);

        // Trigger any initialization scripts in the loaded content
        this.initializeTabScripts(tabId);
    },

    // Show loading state while fetching content
    showLoadingTab: function(tabId, tabConfig) {
        const tabNav = document.querySelector('.tab-navigation');
        const loadingBtn = document.createElement('button');
        loadingBtn.className = 'tab-button loading';
        loadingBtn.dataset.tab = tabId;
        loadingBtn.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading ${tabConfig.title}...</span>
        `;
        tabNav.appendChild(loadingBtn);

        // Add loading content
        const rightContent = document.querySelector('.right-content');
        const loadingContent = document.createElement('div');
        loadingContent.className = 'tab-content active';
        loadingContent.id = `${tabId}-tab`;
        loadingContent.innerHTML = `
            <div class="flex items-center justify-center h-full">
                <div class="text-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p class="text-gray-600">Loading ${tabConfig.title}...</p>
                </div>
            </div>
        `;
        rightContent.appendChild(loadingContent);

        this.openTabs[tabId] = { 
            btn: loadingBtn, 
            content: loadingContent, 
            config: tabConfig,
            loading: true 
        };
    },

    // Remove loading state
    removeLoadingTab: function(tabId) {
        const tab = this.openTabs[tabId];
        if (tab && tab.loading) {
            tab.btn.remove();
            tab.content.remove();
            delete this.openTabs[tabId];
        }
    },

    // Show error state
    showErrorTab: function(tabId, tabConfig, error) {
        this.removeLoadingTab(tabId);
        
        const tabNav = document.querySelector('.tab-navigation');
        const errorBtn = document.createElement('button');
        errorBtn.className = 'tab-button error';
        errorBtn.dataset.tab = tabId;
        errorBtn.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${tabConfig.title} (Error)</span>
            <span class="close-tab" onclick="window.dynamicTabs.closeTab('${tabId}', event)">&times;</span>
        `;
        errorBtn.addEventListener('click', () => this.switchToTab(tabId));
        tabNav.appendChild(errorBtn);

        const rightContent = document.querySelector('.right-content');
        const errorContent = document.createElement('div');
        errorContent.className = 'tab-content';
        errorContent.id = `${tabId}-tab`;
        errorContent.innerHTML = `
            <div class="flex items-center justify-center h-full">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Error Loading ${tabConfig.title}</h3>
                    <p class="text-gray-600 mb-4">${error.message}</p>
                    <button class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                            onclick="window.dynamicTabs.retryTab('${tabId}')">
                        <i class="fas fa-redo mr-2"></i>
                        Retry
                    </button>
                </div>
            </div>
        `;
        rightContent.appendChild(errorContent);

        this.openTabs[tabId] = { 
            btn: errorBtn, 
            content: errorContent, 
            config: tabConfig,
            error: true 
        };
    },

    // Retry loading a failed tab
    retryTab: function(tabId) {
        const tab = this.openTabs[tabId];
        if (tab && tab.error) {
            this.closeTab(tabId);
            this.openTab(tabId);
        }
    },

    // Switch to a specific tab
    switchToTab: function(tabId) {
        // Deactivate all tab buttons and contents
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Activate selected
        const btn = document.querySelector(`.tab-button[data-tab="${tabId}"]`);
        const content = document.getElementById(`${tabId}-tab`);
        if (btn) btn.classList.add('active');
        if (content) content.classList.add('active');
    },

    // Close a tab
    closeTab: function(tabId, event) {
        if (event) event.stopPropagation();
        
        const tab = this.openTabs[tabId];
        if (tab) {
            tab.btn.remove();
            tab.content.remove();
            delete this.openTabs[tabId];
        }
        
        // Switch to another tab (first available)
        const firstTabBtn = document.querySelector('.tab-button');
        if (firstTabBtn) {
            const firstTabId = firstTabBtn.dataset.tab;
            this.switchToTab(firstTabId);
        }
    },

    // Check user permissions
    checkPermissions: function(permissions) {
        // Implement your permission logic here
        // For now, assume user is authenticated
        return true;
    },

    // Initialize any scripts in the loaded tab content
    initializeTabScripts: function(tabId) {
        const tab = this.openTabs[tabId];
        if (tab && tab.content) {
            // Execute any script tags in the loaded content
            const scripts = tab.content.querySelectorAll('script');
            scripts.forEach(script => {
                if (script.src) {
                    // External script - load it
                    const newScript = document.createElement('script');
                    newScript.src = script.src;
                    document.head.appendChild(newScript);
                } else {
                    // Inline script - execute it
                    eval(script.innerHTML);
                }
            });
        }
    },

    // Clear cache for a specific tab or all tabs
    clearCache: function(tabId = null) {
        if (tabId) {
            delete this.tabCache[tabId];
        } else {
            this.tabCache = {};
        }
    },

    // Get list of open tabs
    getOpenTabs: function() {
        return Object.keys(this.openTabs);
    },

    // Check if a tab is open
    isTabOpen: function(tabId) {
        return !!this.openTabs[tabId];
    }
};

// Convenience functions for common operations
window.openResumeListTab = () => window.dynamicTabs.openTab('resume-list');
window.openCoverLetterTab = () => window.dynamicTabs.openTab('cover-letter');
window.openTemplatesTab = () => window.dynamicTabs.openTab('templates'); 