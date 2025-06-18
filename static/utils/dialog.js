/**
 * Dialog Component Class
 * Creates and manages a modal dialog with customizable content
 */
class Dialog {
    /**
     * Initialize the dialog
     * @param {Object} options - Configuration options for the dialog
     * @param {string} options.title - Dialog title
     * @param {string} options.content - Dialog content (can be HTML)
     * @param {string} options.primaryButtonText - Text for primary button (optional)
     * @param {string} options.secondaryButtonText - Text for secondary button (optional)
     * @param {Function} options.onPrimaryClick - Callback for primary button click
     * @param {Function} options.onSecondaryClick - Callback for secondary button click
     * @param {boolean} options.showClose - Whether to show close button (default: true)
     */
    constructor(options = {}) {
        this.options = {
            title: options.title || '',
            content: options.content || '',
            primaryButtonText: options.primaryButtonText,
            secondaryButtonText: options.secondaryButtonText,
            onPrimaryClick: options.onPrimaryClick || (() => this.close()),
            onSecondaryClick: options.onSecondaryClick || (() => this.close()),
            showClose: options.showClose !== undefined ? options.showClose : true
        };
        
        this.element = this.createDialog();
        this.attachEventListeners();
    }

    /**
     * Create the dialog HTML structure
     * @private
     */
    createDialog() {
        // Create the main dialog container
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 z-50 overflow-y-auto hidden';
        
        // Create the dialog HTML structure
        dialog.innerHTML = `
            <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                <!-- Background overlay -->
                <div class="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" aria-hidden="true"></div>

                <!-- Center dialog -->
                <div class="relative inline-block px-4 pt-5 pb-4 overflow-hidden text-left align-bottom transition-all transform bg-white rounded-lg shadow-xl sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                    <!-- Close button -->
                    ${this.options.showClose ? `
                    <div class="absolute top-0 right-0 pt-4 pr-4">
                        <button type="button" class="text-gray-400 hover:text-gray-500 focus:outline-none">
                            <span class="sr-only">Close</span>
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    ` : ''}

                    <!-- Title -->
                    ${this.options.title ? `
                    <div class="mb-4">
                        <h3 class="text-lg font-medium leading-6 text-gray-900">${this.options.title}</h3>
                    </div>
                    ` : ''}

                    <!-- Content -->
                    <div class="mt-2">
                        ${this.options.content}
                    </div>

                    <!-- Buttons -->
                    ${(this.options.primaryButtonText || this.options.secondaryButtonText) ? `
                    <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                        ${this.options.primaryButtonText ? `
                        <button type="button" class="primary-btn inline-flex justify-center w-full px-4 py-2 text-base font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none sm:col-start-2 sm:text-sm">
                            ${this.options.primaryButtonText}
                        </button>
                        ` : ''}
                        ${this.options.secondaryButtonText ? `
                        <button type="button" class="secondary-btn inline-flex justify-center w-full px-4 py-2 mt-3 text-base font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none sm:mt-0 sm:col-start-1 sm:text-sm">
                            ${this.options.secondaryButtonText}
                        </button>
                        ` : ''}
                    </div>
                    ` : ''}
                </div>
            </div>
        `;

        // Add dialog to body
        document.body.appendChild(dialog);
        return dialog;
    }

    /**
     * Attach event listeners to dialog elements
     * @private
     */
    attachEventListeners() {
        // Close button click
        if (this.options.showClose) {
            this.element.querySelector('button[type="button"]').addEventListener('click', () => this.close());
        }

        // Background overlay click
        this.element.querySelector('.bg-opacity-75').addEventListener('click', () => this.close());

        // Primary button click
        const primaryBtn = this.element.querySelector('.primary-btn');
        if (primaryBtn) {
            primaryBtn.addEventListener('click', () => this.options.onPrimaryClick(this));
        }

        // Secondary button click
        const secondaryBtn = this.element.querySelector('.secondary-btn');
        if (secondaryBtn) {
            secondaryBtn.addEventListener('click', () => this.options.onSecondaryClick(this));
        }

        // Escape key press
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.element.classList.contains('hidden')) {
                this.close();
            }
        });
    }

    /**
     * Show the dialog
     */
    show() {
        this.element.classList.remove('hidden');
    }

    /**
     * Hide the dialog
     */
    close() {
        this.element.classList.add('hidden');
    }

    /**
     * Update dialog content
     * @param {string} content - New content HTML
     */
    updateContent(content) {
        this.element.querySelector('.mt-2').innerHTML = content;
    }

    /**
     * Clean up and remove dialog
     */
    destroy() {
        this.element.remove();
    }
}

// Export the Dialog class
export default Dialog; 