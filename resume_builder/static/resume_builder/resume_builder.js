class ResumeBuilder {
    constructor(isAuthenticated) {
        this.isAuthenticated = isAuthenticated;
        /** @type {string|null} Data URL for guests when template supports profile photo (not sent to upload API). */
        this.pendingProfilePhotoDataUrl = null;
        /** When true, anonymous user removed photo; do not carry over a previous personalInfo URL. */
        this._anonProfilePhotoCleared = false;
        this.personalInfo = {};
        this.experience = [];
        this.education = [];
        this.skills = {};
        this.additional = {};
        this.templateId = 'professional';

        // Add event listeners for template selection
        this.initializeTemplateListeners();
        const initialChecked = document.querySelector('input[name="template_id"]:checked')?.value;
        if (initialChecked) {
            this.templateId = initialChecked;
        }
    }

    // Initialize template selection listeners
    initializeTemplateListeners() {
        const templateRadios = document.querySelectorAll('input[name="template_id"]');
        templateRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateTemplate(e.target.value);
            });
        });
    }

    // Update template selection
    updateTemplate(templateId) {
        this.templateId = templateId;
        console.log('Template updated to:', templateId);
        if (typeof refreshTemplateDependentUi === 'function') {
            refreshTemplateDependentUi();
        }
    }

    // Step 1: Personal Info
    nextToExperience() {
        if (!this.validatePersonalInfo()) return false;
        const caps =
            typeof selectedTemplateCapabilities === 'function'
                ? selectedTemplateCapabilities()
                : { supports_profile_photo: false };
        const prevAnonPhoto =
            !this.isAuthenticated && caps.supports_profile_photo && !this._anonProfilePhotoCleared
                ? this.pendingProfilePhotoDataUrl || this.personalInfo.profile_photo_display_url || ''
                : '';
        this.personalInfo = {
            resume_name: document.querySelector('[name="resume_name"]').value,
            fullName: document.querySelector('[name="fullName"]').value,
            title: document.querySelector('[name="title"]').value,
            email: document.querySelector('[name="email"]').value,
            phone: document.querySelector('[name="phone"]').value,
            location: document.querySelector('[name="location"]')?.value || '',
            street_address: document.querySelector('[name="street_address"]')?.value || '',
            linkedin: document.querySelector('[name="linkedin"]')?.value || '',
            template_id: document.querySelector('input[name="template_id"]:checked')?.value || 'professional'
        };
        if (prevAnonPhoto) {
            this.personalInfo.profile_photo_display_url = prevAnonPhoto;
        }
        this.templateId = this.personalInfo.template_id;
        return true;
    }

    // Step 2: Experience
    nextToEducation() {
        if (!this.validateExperience()) return false;
        // Copy experience data from form
        const entries = document.querySelectorAll('.experience-entry');
        this.experience = [];
        for (let entry of entries) {
            const entryData = {};
            const inputs = entry.querySelectorAll('input, textarea');
            for (let input of inputs) {
                const nameParts = input.name.split('.');
                const name = nameParts[nameParts.length - 1];
                if (input.tagName === 'TEXTAREA' && input.id && window.ckeditor5Instances[input.id]) {
                    entryData[name] = window.ckeditor5Instances[input.id].getData();
                } else {
                    entryData[name] = input.value;
                }
            }
            // Handle startDate from dropdowns
            const startMonthSelect = entry.querySelector('[name*="startDate_month"]');
            const startYearSelect = entry.querySelector('[name*="startDate_year"]');
            if (startMonthSelect && startYearSelect) {
                const startMonth = startMonthSelect.value;
                const startYear = startYearSelect.value;
                entryData['start_date'] = `${startYear}-${String(startMonth).padStart(2, '0')}`;
            }
            // Handle endDate from dropdowns
            const endPresentCheckbox = entry.querySelector('[name*="endDate_present"]');
            if (endPresentCheckbox && endPresentCheckbox.checked) {
                entryData['end_date'] = endPresentCheckbox.value; // 'Present'
            } else {
                const endMonthSelect = entry.querySelector('[name*="endDate_month"]');
                const endYearSelect = entry.querySelector('[name*="endDate_year"]');
                if (endMonthSelect && endYearSelect) {
                    const endMonth = endMonthSelect.value;
                    const endYear = endYearSelect.value;
                    entryData['end_date'] = `${endYear}-${String(endMonth).padStart(2, '0')}`;
                }
            }
            // Map form field names to database field names
            const mappedEntryData = {
                company: entryData['company'],
                title: entryData['position'],
                start_date: entryData['start_date'],
                end_date: entryData['end_date'],
                description: entryData['description']
            };
            this.experience.push(mappedEntryData);
        }
        return true;
    }

    // Step 3: Education
    nextToSkills() {
        if (!this.validateEducation()) return false;
        // Copy education data from form
        const entries = document.querySelectorAll('.education-entry');
        this.education = [];
        for (let entry of entries) {
            const entryData = {};
            const inputs = entry.querySelectorAll('input, textarea');
            for (let input of inputs) {
                const nameParts = input.name.split('.');
                const name = nameParts[nameParts.length - 1];
                if (input.tagName === 'TEXTAREA' && input.id && window.ckeditor5Instances[input.id]) {
                    entryData[name] = window.ckeditor5Instances[input.id].getData();
                } else {
                    entryData[name] = input.value;
                }
            }
            // Handle startDate from dropdowns
            const startMonthSelect = entry.querySelector('[name*="startDate_month"]');
            const startYearSelect = entry.querySelector('[name*="startDate_year"]');
            if (startMonthSelect && startYearSelect) {
                const startMonth = startMonthSelect.value;
                const startYear = startYearSelect.value;
                entryData['start_date'] = `${startYear}-${String(startMonth).padStart(2, '0')}`;
            }
            // Handle endDate from dropdowns
            const endPresentCheckbox = entry.querySelector('[name*="endDate_present"]');
            if (endPresentCheckbox && endPresentCheckbox.checked) {
                entryData['end_date'] = endPresentCheckbox.value; // 'Present'
            } else {
                const endMonthSelect = entry.querySelector('[name*="endDate_month"]');
                const endYearSelect = entry.querySelector('[name*="endDate_year"]');
                if (endMonthSelect && endYearSelect) {
                    const endMonth = endMonthSelect.value;
                    const endYear = endYearSelect.value;
                    entryData['end_date'] = `${endYear}-${String(endMonth).padStart(2, '0')}`;
                }
            }
            // Map form field names to database field names
            const mappedEntryData = {
                institution: entryData['institution'],
                degree: entryData['degree'],
                start_date: entryData['start_date'],
                end_date: entryData['end_date'],
                description: entryData['description']
            };
            this.education.push(mappedEntryData);
        }
        return true;
    }

    // Step 4: Skills
    nextToAdditional() {
        if (!this.validateSkills()) return false;
        this.skills = {
            technical: document.querySelector('[name="technicalSkills"]').value.split(',').map(s => s.trim()).filter(Boolean),
            soft: document.querySelector('[name="softSkills"]').value.split(',').map(s => s.trim()).filter(Boolean),
            languages: document.querySelector('[name="languages"]').value.split(',').map(s => s.trim()).filter(Boolean),
        };
        if (typeof selectedTemplateCapabilities === 'function' && selectedTemplateCapabilities().supports_rated_skills) {
            const rated =
                typeof collectRatedSkills === 'function' ? collectRatedSkills() : null;
            if (rated !== null) this.skills.rated = rated;
        }
        return true;
    }

    // Step 5: Additional
    finalizeStep() {
        if (!this.validateAdditional()) return false;
        const refsFn = typeof collectReferencesFromDom === 'function' ? collectReferencesFromDom : null;
        this.additional = {
            certifications: (window.ckeditor5Instances['certifications-editor'])
                ? window.ckeditor5Instances['certifications-editor'].getData()
                : document.querySelector('[name="certifications"]').value,
            projects: (window.ckeditor5Instances['projects-editor'])
                ? window.ckeditor5Instances['projects-editor'].getData()
                : document.querySelector('[name="projects"]').value,
        };
        if (typeof selectedTemplateCapabilities === 'function' && selectedTemplateCapabilities().supports_references) {
            this.additional.references = refsFn ? refsFn() : [];
        }
        return true;
    }

    // Validation methods (copied from your existing code)
    validatePersonalInfo() {
        const requiredFields = ['resume_name', 'fullName', 'title', 'email'];
        
        for (let field of requiredFields) {
            let value;
            if (field === 'summary' && window.ckeditor5Instances['summary-editor']) {
                value = window.ckeditor5Instances['summary-editor'].getData().trim();
            } else {
                value = document.querySelector(`[name="${field}"]`).value.trim();
            }
            if (!value) {
                window.Alert.error(`Please fill in the ${field.replace(/([A-Z])/g, ' $1').toLowerCase()} field.`);
                return false;
            }
        }
        return true;
    }
    validateExperience() {
        const entries = document.querySelectorAll('.experience-entry');
        if (entries.length === 0) {
            window.Alert.warning('Please add at least one work experience entry.');
            return false;
        }
        for (let i = 0; i < entries.length; i++) {
            const entry = entries[i];
            const company = entry.querySelector('[name*="company"]');
            if (!company || !company.value.trim()) {
                window.Alert.error('Please fill in the company name in the experience section.');
                company && company.focus();
                return false;
            }
            const position = entry.querySelector('[name*="position"]');
            if (!position || !position.value.trim()) {
                window.Alert.error('Please fill in the position in the experience section.');
                position && position.focus();
                return false;
            }
            const descriptionField = entry.querySelector('[name*="description"]');
            let descriptionValue = '';
            if (descriptionField && descriptionField.id && window.ckeditor5Instances[descriptionField.id]) {
                descriptionValue = window.ckeditor5Instances[descriptionField.id].getData().trim();
            } else if (descriptionField) {
                descriptionValue = descriptionField.value.trim();
            }
            if (!descriptionValue) {
                window.Alert.error('Please fill in the description in the experience section.');
                descriptionField && descriptionField.focus();
                return false;
            }
            // Check start date
            const startMonth = entry.querySelector('[name*="startDate_month"]');
            const startYear = entry.querySelector('[name*="startDate_year"]');
            if (!startMonth || !startMonth.value || !startYear || !startYear.value) {
                window.Alert.error('Please select both month and year for the start date in the experience section.');
                return false;
            }
            // Check end date
            const endPresent = entry.querySelector('[name*="endDate_present"]');
            if (!(endPresent && endPresent.checked)) {
                const endMonth = entry.querySelector('[name*="endDate_month"]');
                const endYear = entry.querySelector('[name*="endDate_year"]');
                if (!endMonth || !endMonth.value || !endYear || !endYear.value) {
                    window.Alert.error('Please select both month and year for the end date in the experience section, or check Present.');
                    return false;
                }
            }
        }
        return true;
    }
    validateEducation() {
        const entries = document.querySelectorAll('.education-entry');
        if (entries.length === 0) {
            window.Alert.warning('Please add at least one education entry.');
            return false;
        }
        for (let entry of entries) {
            const requiredFields = ['institution', 'degree'];
            for (let field of requiredFields) {
                const value = entry.querySelector(`[name*="${field}"]`).value.trim();
                if (!value) {
                    window.Alert.error('Please fill in all required fields in the education section.');
                    entry.querySelector(`[name*="${field}"]`).focus();
                    return false;
                }
            }
            const startMonth = entry.querySelector('[name*="startDate_month"]');
            const startYear = entry.querySelector('[name*="startDate_year"]');
            if (!startMonth || !startMonth.value || !startYear || !startYear.value) {
                window.Alert.error('Please select both month and year for the education start date.');
                return false;
            }
            const endPresent = entry.querySelector('[name*="endDate_present"]');
            if (!(endPresent && endPresent.checked)) {
                const endMonth = entry.querySelector('[name*="endDate_month"]');
                const endYear = entry.querySelector('[name*="endDate_year"]');
                if (!endMonth || !endMonth.value || !endYear || !endYear.value) {
                    window.Alert.error('Please select both month and year for the education end date, or check Present.');
                    return false;
                }
            }
        }
        return true;
    }
    validateSkills() {
        // For now, skills are optional
        return true;
    }
    validateAdditional() {
        // For now, additional info is optional
        return true;
    }

    // Utility
    getResumeData() {
        // Always get the current template selection from the form
        const currentTemplate = document.querySelector('input[name="template_id"]:checked')?.value || 'professional';
        
        return {
            personalInfo: this.personalInfo,
            experience: this.experience,
            education: this.education,
            skills: this.skills,
            additional: this.additional,
            templateId: currentTemplate,
            resume_name: this.personalInfo.resume_name || 'My Resume'
        };
    }

    saveAndExit() {
        if (this.isAuthenticated) {
            // Call backend as before
        } else {
            // Show dialog to prompt login/register
        }
    }
} 