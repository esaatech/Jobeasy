class ResumePreviewTab {
    constructor() {
        this.currentResumeId = null;
        this.currentTemplate = 'professional';
        this.initializeTemplateButtons();
    }
    
    initializeTemplateButtons() {
        console.log('🔧 ResumePreviewTab: Initializing template buttons');
        // Add click event listeners to template buttons
        document.addEventListener('click', (e) => {
            console.log('🔍 Click event on:', e.target);
            if (e.target.classList.contains('template-btn')) {
                const templateId = e.target.getAttribute('data-template');
                console.log('🎨 Template button clicked:', templateId);
                if (templateId) {
                    this.switchTemplate(templateId);
                }
            }
        });
    }
    
    setResumeInfo(resumeId, resumeName, templateId) {
        console.log('📄 ResumePreviewTab: Setting resume info:', { resumeId, resumeName, templateId });
        this.currentResumeId = resumeId;
        this.currentTemplate = templateId || 'professional';
        
        // Load the resume preview using HTMX
        if (resumeId) {
            this.loadResumePreview(resumeId, templateId);
        }
    }
    
    loadResumePreview(resumeId, templateId = null) {
        console.log('📄 ResumePreviewTab: Loading resume preview for ID:', resumeId, 'template:', templateId);
        
        const template = templateId || this.currentTemplate;
        
        // Get the URL pattern from the data attribute
        const resumePreviewTab = document.getElementById('resumePreviewTab');
        const urlPattern = resumePreviewTab ? resumePreviewTab.getAttribute('data-resume-url') : null;
        
        if (!urlPattern) {
            console.error('❌ URL pattern not found in data-resume-url attribute');
            return;
        }
        
        // Replace the placeholder with the actual resume ID
        const url = urlPattern.replace('0', resumeId);
        const fullUrl = templateId ? `${url}?template=${templateId}` : url;
        
        console.log('🔗 Full URL:', fullUrl);
        
        // Show loading state
        const resumeContent = document.getElementById('resumeContent');
        if (resumeContent) {
            resumeContent.innerHTML = '<div class="text-center py-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div><p class="mt-2 text-gray-600">Loading resume...</p></div>';
        }
        
        // Use HTMX to load the entire tab content
        htmx.ajax('GET', fullUrl, {
            target: '#resume-preview-tab',
            swap: 'innerHTML',
            headers: {
                'HX-Request': 'true'
            },
            success: (response) => {
                console.log('✅ Resume preview loaded successfully');
                this.updateTemplateButtonStates(templateId || this.currentTemplate);
            },
            error: (error) => {
                console.error('❌ Error loading resume preview:', error);
                if (resumeContent) {
                    resumeContent.innerHTML = '<div class="text-center py-8 text-red-600">Error loading resume preview</div>';
                }
            }
        });
    }
    
    updateTemplateButtonStates(activeTemplate) {
        // Update button states
        const templateButtons = document.querySelectorAll('.template-btn');
        templateButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-template') === activeTemplate) {
                btn.classList.add('active');
            }
        });
    }
    
    switchTemplate(templateId) {
        console.log('🎨 ResumePreviewTab: Switching template to:', templateId);
        this.currentTemplate = templateId;
        
        if (this.currentResumeId) {
            this.loadResumePreview(this.currentResumeId, templateId);
        } else {
            console.warn('⚠️ No resume ID available for template switching');
        }
    }
}

// Global function for template switching
function switchResumeTemplate(templateId) {
    console.log('🎨 Global switchResumeTemplate called with:', templateId);
    if (window.resumePreviewTab) {
        window.resumePreviewTab.switchTemplate(templateId);
    } else {
        console.warn('⚠️ ResumePreviewTab not initialized');
    }
}