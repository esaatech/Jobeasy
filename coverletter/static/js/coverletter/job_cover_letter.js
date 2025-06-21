/**
 * Job Cover Letter Generator
 * 
 * This script manages a dynamic form for generating cover letters with the following features:
 * - Dual input methods for resume (manual entry or file upload)
 * - Dual input methods for job details (structured or unstructured)
 * - Drag and drop file upload support
 * - Real-time form field toggling
 * - Asynchronous form submission with loading states
 * - Error handling with visual feedback
 * 
 * Required DOM Elements:
 * #coverLetterForm - Main form container
 * #results - Results display container
 * #coverLetterContent - Generated cover letter container
 * #manual-entry-section - Manual resume entry section
 * #upload-section - Resume file upload section
 * #structured-job-section - Structured job details section
 * #unstructured-job-section - Unstructured job details section
 * 
 * Input Elements:
 * input[name="input_method"] - Resume input method radio buttons
 * input[name="job_input_method"] - Job input method radio buttons
 * 
 * File Upload Elements:
 * #file-preview - File preview container
 * #file-name - Filename display element
 * #dropzone-content - Dropzone content container
 */

/* Function Documentation:

handleResumeUpload(input)
- Processes file selection
- Updates UI with file preview
- Parameters: input (HTMLInputElement) - File input element

removeResume()
- Clears file input value
- Resets file preview UI
- Cleans up FormData if present

handleFileUpload(event)
- Handles file input change events
- Triggers file preview update
- Parameters: event (Event) - File input change event

showFilePreview(file)
- Updates UI with file information
- Parameters: file (File) - Selected file object

getCookie(name)
- Retrieves cookie value by name
- Used for CSRF token
- Parameters: name (string) - Cookie name to retrieve

showError(message)
- Displays error message with styling
- Auto-removes after 5 seconds
- Parameters: message (string) - Error message to display

updateCoverLetterContent(coverLetter)
- Formats and updates cover letter display
- Handles line breaks and spacing
- Parameters: coverLetter (string) - Cover letter content

Event Handlers:
- Resume input method toggle
- Job input method toggle
- Form submission
- File drag and drop
- File selection

Form Submission Process:
1. Prevents default form submission
2. Shows loading state
3. Collects form data
4. Sends to backend endpoint
5. Handles response/errors
6. Updates UI with results

Error Handling:
- Network errors
- Form validation
- File upload errors
- Server response errors

Dependencies:
- Modern browser with FormData support
- CSRF token implementation
- Tailwind CSS for styling classes
*/

console.log("job cover letter page loaded");



document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('coverLetterForm');
    const results = document.getElementById('results');
    const coverLetterContent = document.getElementById('coverLetterContent');
    
    // Elements for resume input method toggle
    const manualEntrySection = document.getElementById('manual-entry-section');
    const uploadSection = document.getElementById('upload-section');
    const resumeInputs = document.querySelectorAll('input[name="input_method"]');

    // Elements for job input method toggle
    const structuredJobSection = document.getElementById('structured-job-section');
    const unstructuredJobSection = document.getElementById('unstructured-job-section');
    const jobInputs = document.querySelectorAll('input[name="job_input_method"]');

    // Handle resume input method toggle
    resumeInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value === 'manual') {
                manualEntrySection.classList.remove('hidden');
                uploadSection.classList.add('hidden');
                // Enable manual entry fields
                manualEntrySection.querySelectorAll('input, textarea').forEach(field => {
                    field.disabled = false;
                });
                // Disable upload fields
                uploadSection.querySelectorAll('input').forEach(field => {
                    field.disabled = true;
                });
            } else {
                manualEntrySection.classList.add('hidden');
                uploadSection.classList.remove('hidden');
                // Disable manual entry fields
                manualEntrySection.querySelectorAll('input, textarea').forEach(field => {
                    field.disabled = true;
                });
                // Enable upload fields
                uploadSection.querySelectorAll('input').forEach(field => {
                    field.disabled = false;
                });
            }
        });
    });

    // Handle job input method toggle
    jobInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value === 'structured') {
                structuredJobSection.classList.remove('hidden');
                unstructuredJobSection.classList.add('hidden');
                // Enable structured fields
                structuredJobSection.querySelectorAll('input, textarea').forEach(field => {
                    field.disabled = false;
                });
                // Disable unstructured fields
                unstructuredJobSection.querySelectorAll('textarea').forEach(field => {
                    field.disabled = true;
                });
            } else {
                structuredJobSection.classList.add('hidden');
                unstructuredJobSection.classList.remove('hidden');
                // Disable structured fields
                structuredJobSection.querySelectorAll('input, textarea').forEach(field => {
                    field.disabled = true;
                });
                // Enable unstructured fields
                unstructuredJobSection.querySelectorAll('textarea').forEach(field => {
                    field.disabled = false;
                });
            }
        });
    });

    // Handle resume file upload
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

    // Handle resume removal
    function removeResume() {
        // Get the file input and preview elements
        const fileInput = document.querySelector('input[type="file"]');
        const filePreview = document.getElementById('file-preview');
        const fileName = document.getElementById('file-name');

        // Clear the file input value
        fileInput.value = '';

        // Hide the file preview
        filePreview.classList.add('hidden');
        
        // Clear the filename display
        fileName.textContent = '';

        // If using FormData, you might want to clear that as well
        if (window.formData) {
            window.formData.delete('resume');
        }
    }

    // Make these functions globally available
    window.handleResumeUpload = handleResumeUpload;
    window.removeResume = removeResume;

    const resultsModal = document.getElementById('resultsModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const saveButton = document.getElementById('saveButton');

    // Show modal function
    function showModal() {
        resultsModal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden'); // Prevent background scroll
    }

    // Hide modal function
    function hideModal() {
        resultsModal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    // Close modal on close button click
    closeModalBtn.addEventListener('click', hideModal);
    // Close modal on overlay click (but not when clicking inside modal)
    resultsModal.addEventListener('click', function(e) {
        if (e.target === resultsModal) hideModal();
    });

    // Save button placeholder
    saveButton.addEventListener('click', function() {
        alert('Save functionality coming soon!');
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
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
            
            // Determine which endpoint to use based on input method
            const inputMethod = form.querySelector('input[name="input_method"]:checked').value;
            const endpoint = '/job-cover-letter/';

            // Send request to backend
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.error('Server response:', errorData);
                throw new Error(errorData.error || 'Failed to generate cover letter');
            }

            const data = await response.json();
            
            if (!data.success) {
                console.error('Server error:', data.error);
                throw new Error(data.error || 'Failed to generate cover letter');
            }

            // Display the generated cover letter in the modal
            coverLetterContent.innerHTML = data.cover_letter;
            showModal();

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

    // Add this to your existing file input handling code
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (file) {
            showFilePreview(file);
        }
    }

    function showFilePreview(file) {
        const filePreview = document.getElementById('file-preview');
        const fileName = document.getElementById('file-name');
        
        // Show the preview container
        filePreview.classList.remove('hidden');
        
        // Update the filename display
        fileName.textContent = file.name;
    }

    // Add event listeners when the document loads
    document.addEventListener('DOMContentLoaded', function() {
        const fileInput = document.querySelector('input[type="file"]');
        
        // Handle file selection
        fileInput.addEventListener('change', handleFileUpload);

        // Handle drag and drop
        const dropZone = fileInput.parentElement;
        
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
                fileInput.files = files;
                showFilePreview(files[0]);
            }
        });
    });

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
});