function resumePreviewDefaultTemplateId() {
    const el = document.getElementById('resumePreviewTab');
    return (el && el.dataset.defaultTemplate) ? el.dataset.defaultTemplate : 'professional';
}

function resumePreviewTabSkeletonHtml() {
    return [
        '<div class="animate-pulse space-y-5 px-1 py-2" aria-busy="true">',
        '<div class="h-14 rounded-md bg-slate-200 w-4/5 max-w-xl mx-auto"></div>',
        '<div class="h-2.5 bg-slate-100 rounded w-36 mx-auto"></div>',
        '<div class="space-y-2.5 pt-4 max-w-2xl mx-auto">',
        '<div class="h-2 bg-slate-100 rounded"></div>',
        '<div class="h-2 bg-slate-100 rounded w-11/12 max-w-2xl"></div>',
        '<div class="h-2 bg-slate-100 rounded w-4/5"></div>',
        '</div>',
        '<div class="h-2 bg-slate-200 rounded w-40 max-w-md mx-auto mt-8"></div>',
        '<div class="space-y-2 max-w-2xl mx-auto">',
        '<div class="h-2 bg-slate-100 rounded"></div>',
        '<div class="h-2 bg-slate-100 rounded w-[92%]"></div>',
        '<div class="h-2 bg-slate-100 rounded w-[88%]"></div>',
        '</div>',
        '</div>'
    ].join('');
}

class ResumePreviewTab {
    constructor() {
        this.currentResumeId = null;
        this.currentTemplate = resumePreviewDefaultTemplateId();
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
        this.currentTemplate = templateId || resumePreviewDefaultTemplateId();
        
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
        
        // Document-style skeleton (matches template gallery Row 2 loading treatment)
        const resumeContent = document.getElementById('resumeContent');
        if (resumeContent) {
            resumeContent.innerHTML = resumePreviewTabSkeletonHtml();
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

window.getTemplatePreviewSkeletonHtml = resumePreviewTabSkeletonHtml;