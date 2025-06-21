/**
 * CoverLetterUtils Class Documentation
 * 
 * A utility class for managing cover letter functionality including:
 * - File upload handling
 * - Cover letter content management
 * - PDF generation
 * - Clipboard operations
 * - Content editing
 * - Email functionality
 * - Toast notifications
 * 
 * Usage:
 * const utils = new CoverLetterUtils();
 * 
 * Required HTML Elements:
 * - File input element
 * - File preview element with ID 'filePreview'
 * - Clear file button with ID 'clearFile'
 * - Results container with ID 'results'
 * - Cover letter content div with ID 'coverLetterContent'
 * - Copy button with ID 'copyButton'
 * - Download button with ID 'downloadButton'
 * - Edit button with ID 'editButton'
 */

/* Method Documentation:

constructor()
Initializes the CoverLetterUtils instance by:
- Setting up element references
- Calling initializeEventListeners()

initializeEventListeners()
Sets up event listeners for:
- File upload handling
- Clear file functionality
- Copy to clipboard
- PDF download
- Content editing

handleFileUpload()
Handles file selection:
- Updates file preview
- Shows file name
- Manages visibility of preview element

clearFileUpload(event)
Clears the selected file:
- Creates new file input
- Resets preview
- Maintains event listeners

copyToClipboard()
Copies cover letter content to clipboard:
- Uses navigator.clipboard API
- Shows success/error toast

downloadAsPDF()
Generates and downloads PDF:
- Uses html2pdf library
- Configures PDF options
- Handles errors with toast notifications

makeEditable()
Toggles content editability:
- Switches between view/edit modes
- Updates UI elements
- Shows status toasts

emailCoverLetter()
Opens email client with cover letter:
- Creates mailto link
- Encodes content
- Opens default email client

showToast(message, isError)
Displays notification toast:
- Creates toast element
- Handles animations
- Supports success/error states
- Auto-removes after delay

Dependencies:
- html2pdf.js for PDF generation
- Modern browser with clipboard API support
*/

class CoverLetterUtils {
    constructor() {
        // File upload related elements
        this.fileInput = document.querySelector('input[type="file"]');
        this.filePreview = document.getElementById('filePreview');
        this.clearFileButton = document.getElementById('clearFile');
        
        // Response related elements
        this.results = document.getElementById('results');
        this.coverLetterContent = document.getElementById('coverLetterContent');
        this.copyButton = document.getElementById('copyButton');
        this.downloadButton = document.getElementById('downloadButton');
        this.editButton = document.getElementById('editButton');

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // File upload handling
        if (this.fileInput && this.clearFileButton) {
            this.fileInput.addEventListener('change', () => this.handleFileUpload());
            this.clearFileButton.addEventListener('click', (e) => this.clearFileUpload(e));
        }

        // Response handling
        if (this.copyButton) {
            this.copyButton.addEventListener('click', () => this.copyToClipboard());
        }
        if (this.downloadButton) {
            this.downloadButton.addEventListener('click', () => this.downloadAsPDF());
        }
        if (this.editButton) {
            this.editButton.addEventListener('click', () => this.makeEditable());
        }
    }

    handleFileUpload() {
        if (this.fileInput.files.length > 0) {
            const file = this.fileInput.files[0];
            if (this.filePreview) {
                this.filePreview.textContent = file.name;
                this.filePreview.parentElement.classList.remove('hidden');
            }
        }
    }

    clearFileUpload(event) {
        event.preventDefault();
        if (this.fileInput) {
            // Create a new file input
            const newFileInput = document.createElement('input');
            newFileInput.type = 'file';
            newFileInput.name = this.fileInput.name;
            newFileInput.accept = this.fileInput.accept;
            newFileInput.className = this.fileInput.className;
            
            // Replace old input with new one
            this.fileInput.parentNode.replaceChild(newFileInput, this.fileInput);
            this.fileInput = newFileInput;
            
            // Re-attach event listener
            this.fileInput.addEventListener('change', () => this.handleFileUpload());
        }
        
        if (this.filePreview) {
            this.filePreview.parentElement.classList.add('hidden');
            this.filePreview.textContent = '';
        }
    }

    async copyToClipboard() {
        try {
            const content = this.coverLetterContent.innerText;
            await navigator.clipboard.writeText(content);
            this.showToast('Cover letter copied to clipboard!');
        } catch (err) {
            this.showToast('Failed to copy to clipboard', true);
        }
    }

    async downloadAsPDF() {
        const element = this.coverLetterContent;
        const options = {
            margin: [10, 10],
            filename: 'cover-letter.pdf',
            html2canvas: { 
                scale: 2,
                useCORS: true,
                logging: true,
                // Add these options for better rendering
                letterRendering: true,
                allowTaint: true
            },
            jsPDF: { 
                unit: 'mm', 
                format: 'a4', 
                orientation: 'portrait',
                compress: true
            },
            // Add this to force download
            output: 'save'
        };

        try {
            // Use promise-based approach
            await html2pdf()
                .from(element)
                .set(options)
                .toPdf()
                .get('pdf')
                .then((pdf) => {
                    pdf.save('cover-letter.pdf');
                });
        } catch (error) {
            console.error('PDF generation error:', error);
            this.showToast('Error generating PDF', true);
        }
    }

    makeEditable() {
        if (!this.coverLetterContent.isContentEditable) {
            this.coverLetterContent.contentEditable = true;
            this.coverLetterContent.classList.add('border', 'border-blue-300', 'p-4', 'rounded');
            this.editButton.textContent = 'Save Changes';
            this.showToast('You can now edit the cover letter');
        } else {
            this.coverLetterContent.contentEditable = false;
            this.coverLetterContent.classList.remove('border', 'border-blue-300', 'p-4', 'rounded');
            this.editButton.textContent = 'Edit Letter';
            this.showToast('Changes saved');
        }
    }

    emailCoverLetter() {
        const content = this.coverLetterContent.innerText;
        const subject = encodeURIComponent('Cover Letter');
        const body = encodeURIComponent(content);
        
        // Create mailto link
        const mailtoLink = `mailto:?subject=${subject}&body=${body}`;
        
        // Open default email client
        window.location.href = mailtoLink;
    }

    showToast(message, isError = false) {
        // Remove any existing toasts
        const existingToasts = document.querySelectorAll('.toast-message');
        existingToasts.forEach(toast => toast.remove());

        // Create new toast
        const toast = document.createElement('div');
        toast.className = `toast-message fixed bottom-4 left-4 px-6 py-3 rounded-lg shadow-lg ${
            isError ? 'bg-red-500' : 'bg-green-500'
        } text-white transform transition-all duration-300 ease-in-out z-50`;
        
        // Add styles for initial position (off-screen)
        toast.style.transform = 'translateY(100%)';
        toast.style.opacity = '0';
        
        // Create message container with flex
        const messageContainer = document.createElement('div');
        messageContainer.className = 'flex items-center space-x-2';
        
        // Add icon based on type
        const icon = document.createElement('span');
        if (isError) {
            icon.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>`;
        } else {
            icon.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M5 13l4 4L19 7" />
                </svg>`;
        }
        
        // Add message text
        const text = document.createElement('span');
        text.textContent = message;
        
        // Assemble toast
        messageContainer.appendChild(icon);
        messageContainer.appendChild(text);
        toast.appendChild(messageContainer);
        document.body.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
        });

        // Remove after delay
        setTimeout(() => {
            toast.style.transform = 'translateY(100%)';
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.coverLetterUtils = new CoverLetterUtils();
}); 