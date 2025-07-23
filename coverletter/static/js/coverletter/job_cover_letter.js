/**
 * Job Cover Letter Generator
 * 
 * This script manages a dynamic form for generating cover letters with the following features:
 * - Resume selection from user's existing resumes OR file upload
 * - Job description input via text area
 * - Asynchronous form submission with loading states
 * - Error handling with visual feedback
 * 
 * Required DOM Elements:
 * #coverLetterForm - Main form container
 * #results - Results display container
 * #coverLetterContent - Generated cover letter container
 * 
 * Input Elements:
 * input[name="selected_resume"] - Selected resume radio button
 * input[name="resume"] - File upload input
 * textarea[name="job_posting"] - Job description text area
 */

console.log("job cover letter page loaded");

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('coverLetterForm');
    const results = document.getElementById('results');
    const coverLetterContent = document.getElementById('coverLetterContent');

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Check which tab is active
        const activeTab = document.querySelector('.resume-tab-button.active');
        if (!activeTab) {
            showError('Please select a resume input method.');
            return;
        }
        
        const activeTabName = activeTab.getAttribute('data-tab');
        
        // Check validation based on active tab
        let isValid = false;
        if (activeTabName === 'saved-resume') {
            // Check if a resume is selected
            const selectedResume = document.querySelector('input[name="selected_resume"]:checked');
            if (selectedResume) {
                isValid = true;
            } else {
                showError('Please select a resume from your saved resumes.');
                return;
            }
        } else if (activeTabName === 'upload-resume') {
            // Check if a file is uploaded
            const uploadedFile = document.querySelector('input[name="resume"]').files[0];
            if (uploadedFile) {
                isValid = true;
            } else {
                showError('Please upload a resume file.');
                return;
            }
        }
        
        if (!isValid) {
            showError('Please provide a resume using the selected method.');
            return;
        }
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <svg class="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generating...
        `;

        try {
            // Get form data
            const formData = new FormData(form);
            
            // Debug: Log form data
            console.log('Form data being sent:');
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
            
            // Send request to backend
            const response = await fetch('/coverletter/job-cover-letter/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: formData
            });

            if (response.redirected) {
                // Handle redirect to response page
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('Server response:', errorData);
                throw new Error(errorData.error || 'Failed to generate cover letter');
            }

            // If we get here, it means no redirect (shouldn't happen with current setup)
            const data = await response.json();
            
            if (!data.success) {
                console.error('Server error:', data.error);
                throw new Error(data.error || 'Failed to generate cover letter');
            }

            // This should not be reached with current redirect setup
            console.log('Unexpected response format');

        } catch (error) {
            console.error('Error:', error);
            showError('Failed to generate cover letter. Please try again.');
        } finally {
            // Reset button state
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Helper function to show errors
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded';
        errorDiv.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">${message}</p>
                </div>
            </div>
        `;
        form.insertBefore(errorDiv, form.firstChild);
        setTimeout(() => errorDiv.remove(), 5000);
    }

    function updateCoverLetterContent(coverLetter) {
        const contentDiv = document.getElementById('coverLetterContent');
        if (contentDiv) {
            const formattedContent = coverLetter
                .split('\n')
                .map(line => line.trim())
                .filter(line => line)
                .join('<br>');
            
            contentDiv.innerHTML = formattedContent;
            
            // Debug log
            console.log('Content updated:', contentDiv.innerHTML);
        }
    }

    // Handle copy button
    const copyButton = document.getElementById('copyButton');
    if (copyButton) {
        copyButton.addEventListener('click', function() {
            const content = document.getElementById('coverLetterContent');
            if (content) {
                const textToCopy = content.innerText || content.textContent;
                navigator.clipboard.writeText(textToCopy).then(function() {
                    // Show success message
                    const originalText = copyButton.textContent;
                    copyButton.textContent = 'Copied!';
                    copyButton.classList.add('bg-green-500');
                    setTimeout(() => {
                        copyButton.textContent = originalText;
                        copyButton.classList.remove('bg-green-500');
                    }, 2000);
                }).catch(function(err) {
                    console.error('Could not copy text: ', err);
                    showError('Failed to copy to clipboard');
                });
            }
        });
    }

    // Handle edit button
    const editButton = document.getElementById('editButton');
    if (editButton) {
        editButton.addEventListener('click', function() {
            // Scroll back to form
            form.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Handle drag and drop for file upload
    const dropZone = document.querySelector('input[type="file"]').parentElement;
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-blue-500');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-blue-500');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-blue-500');
        
        const files = e.dataTransfer.files;
        if (files.length) {
            const fileInput = document.querySelector('input[type="file"]');
            fileInput.files = files;
            handleResumeUpload(fileInput);
        }
    });
});

// Global functions for file upload handling
function handleResumeUpload(input) {
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const dropzoneContent = document.getElementById('dropzone-content');

    if (input.files && input.files[0]) {
        const file = input.files[0];
        fileName.textContent = file.name;
        filePreview.classList.remove('hidden');
        dropzoneContent.classList.add('hidden');
    }
}

function removeResume() {
    const fileInput = document.querySelector('input[type="file"]');
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    const dropzoneContent = document.getElementById('dropzone-content');

    fileInput.value = '';
    filePreview.classList.add('hidden');
    fileName.textContent = '';
    dropzoneContent.classList.remove('hidden');

    if (window.formData) {
        window.formData.delete('resume');
    }
}