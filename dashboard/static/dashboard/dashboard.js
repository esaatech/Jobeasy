document.addEventListener('DOMContentLoaded', function() {
    // Resume selection functionality
    const resumeCards = document.querySelectorAll('.resume-card');
    const resumeRadios = document.querySelectorAll('.resume-radio');
    
    resumeCards.forEach((card, index) => {
        card.addEventListener('click', function() {
            // Remove active state from all cards
            resumeCards.forEach(c => {
                c.classList.remove('border-blue-500', 'bg-blue-50');
                c.classList.add('border-transparent', 'bg-gray-50');
            });
            
            // Uncheck all radios
            resumeRadios.forEach(radio => radio.checked = false);
            
            // Add active state to clicked card
            this.classList.remove('border-transparent', 'bg-gray-50');
            this.classList.add('border-blue-500', 'bg-blue-50');
            
            // Check the corresponding radio
            if (resumeRadios[index]) {
                resumeRadios[index].checked = true;
            }
        });
    });

    // Carousel navigation
    const carousel = document.getElementById('resume-carousel');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (prevBtn && nextBtn && carousel) {
        prevBtn.addEventListener('click', () => {
            carousel.scrollBy({ left: -200, behavior: 'smooth' });
        });
        
        nextBtn.addEventListener('click', () => {
            carousel.scrollBy({ left: 200, behavior: 'smooth' });
        });
    }

    // Job application generation functionality
    const generateBtn = document.getElementById('generate-btn');
    
    generateBtn.addEventListener('click', withSubscriptionCheck('Plus', async function() {
        // Validation
        const selectedResume = document.querySelector('input[name="selected_resume"]:checked');
        const jobDescription = document.getElementById('job-description').value;
        const optimizeResume = document.getElementById('optimize-resume').checked;
        const generateCoverLetter = document.getElementById('generate-cover-letter').checked;
        
        if (!selectedResume) {
            alert('Please select a resume');
            return;
        }
        
        if (!jobDescription.trim()) {
            alert('Please enter a job description');
            return;
        }
        
        if (!optimizeResume && !generateCoverLetter) {
            alert('Please select at least one action');
            return;
        }
        
        // Disable button for 3 seconds to prevent multiple clicks
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        setTimeout(() => {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate';
        }, 3000); // Re-enable after 3 seconds

        // Create processing item immediately
        const jobId = Date.now();
        createProcessingItem(jobId);
        
        // Send AJAX request
        try {
            const formData = new FormData();
            formData.append('resume_id', selectedResume.value);
            formData.append('job_description', jobDescription);
            formData.append('optimize_resume', optimizeResume);
            formData.append('generate_cover_letter', generateCoverLetter);
            
            const response = await fetch('/dashboard/api/generate-job-application/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'completed') {
                updateJobApplicationItem(jobId, data);
            } else if (data.status === 'failed') {
                updateJobApplicationItem(jobId, data);
            }
            
        } catch (error) {
            console.error('Error:', error);
            updateJobApplicationItem(jobId, { status: 'failed', error: 'Network error' });
        }
    }));
});

function createProcessingItem(jobId) {
    const container = document.getElementById('job-applications-container');
    
    // Remove empty state if it exists
    const emptyState = container.querySelector('.text-center');
    if (emptyState) {
        emptyState.remove();
    }
    
    const processingItem = `
        <div id="job-application-${jobId}" class="bg-white rounded-lg shadow-md p-6 mb-4 border-l-4 border-blue-500">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900">Processing...</h3>
                        <p class="text-sm text-gray-500">${new Date().toLocaleString()}</p>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Processing
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', processingItem);
}

function updateJobApplicationItem(jobId, data) {
    const item = document.getElementById(`job-application-${jobId}`);
    
    if (data.status === 'completed') {
        // Update stats
        if (data.counts) {
            document.getElementById('resume-count').textContent = data.counts.resumes;
            document.getElementById('cover-letter-count').textContent = data.counts.cover_letters;
            document.getElementById('job-application-count').textContent = data.counts.job_applications;
        }

        item.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900">${data.job_name}</h3>
                        <p class="text-sm text-gray-500">${data.created_at}</p>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Completed
                        </span>
                    </div>
                </div>
                <div class="flex flex-col gap-3">
                    <div class="flex flex-wrap md:flex-nowrap gap-2">
                        ${data.resume_id ? `
                        <a href="${window.resumeViewUrlTemplate.replace('{resume_id}', data.resume_id)}" target="_blank" class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Open Resume">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                            </svg>
                        </a>
                        <a href="${window.resumeDownloadUrlTemplate.replace('{resume_id}', data.resume_id)}" class="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors" title="Download Resume">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                        </a>
                        ` : ''}
                        ${data.cover_letter_id ? `
                            <a href="/coverletter/view/${data.cover_letter_id}/" target="_blank" class="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors" title="Open Cover Letter">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                                </svg>
                            </a>
                            <button onclick="downloadCoverLetterPDF('')" class="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors" title="Download Cover Letter">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                            </button>
                        ` : ''}
                        <button onclick="deleteJobApplication(${data.job_id})" class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete Job Application">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="self-end">
                        <button onclick="emailJobApplication(${data.job_id})" class="btn btn-success btn-sm">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            Email
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        item.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                        <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900">Failed</h3>
                        <p class="text-sm text-gray-500">${data.error || 'Unknown error'}</p>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Failed
                        </span>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="deleteJobApplication(${data.job_id || jobId})" class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete Job Application">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }
}

function openResume(url) {
    window.open(url, '_blank');
}

function downloadResume(url) {
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    link.click();
}

function openCoverLetter(url) {
    window.open(url, '_blank');
}

function downloadCoverLetter(url) {
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    link.click();
}

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

async function deleteJobApplication(jobId) {
    if (!confirm('Are you sure you want to delete this job application? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/dashboard/api/delete-job-application/${jobId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();

        if (data.status === 'success') {
            // Remove the item from the UI
            const item = document.getElementById(`job-application-${jobId}`);
            if (item) {
                item.remove();
            }

            // Update stats
            if (data.counts) {
                document.getElementById('resume-count').textContent = data.counts.resumes;
                document.getElementById('cover-letter-count').textContent = data.counts.cover_letters;
                document.getElementById('job-application-count').textContent = data.counts.job_applications;
            }

            // Check if container is empty and show empty state
            const container = document.getElementById('job-applications-container');
            if (container.children.length === 0) {
                container.innerHTML = `
                    <div class="bg-white rounded-lg shadow-md p-8 text-center">
                        <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2V6"></path>
                            </svg>
                        </div>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">No job applications yet</h3>
                        <p class="text-gray-500">Start by generating your first job application above</p>
                    </div>
                `;
            }
        } else {
            alert('Failed to delete job application. Please try again.');
        }
    } catch (error) {
        console.error('Error deleting job application:', error);
        alert('An error occurred while deleting the job application.');
    }
}

function emailJobApplication(jobApplicationId) {
    // Redirect to email composition with job application context
    window.location.href = `/email/compose/job_application/${jobApplicationId}/`;
}
