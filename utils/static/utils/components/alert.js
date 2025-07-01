/**
 * Alert Dialog System
 * Provides a comprehensive alert system with different types and styling
 * Built on top of the Dialog component for consistency
 */

class AlertDialog {
    /**
     * Initialize the alert dialog
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.options = {
            type: options.type || 'info', // 'success', 'error', 'warning', 'info'
            title: options.title || '',
            message: options.message || '',
            confirmText: options.confirmText || 'OK',
            cancelText: options.cancelText || 'Cancel',
            showCancel: options.showCancel || false,
            onConfirm: options.onConfirm || (() => {}),
            onCancel: options.onCancel || (() => {}),
            autoClose: options.autoClose || false,
            autoCloseDelay: options.autoCloseDelay || 3000,
            ...options
        };
        
        this.dialog = null;
        this.autoCloseTimer = null;
    }

    /**
     * Get icon for alert type
     * @private
     */
    getIcon() {
        const icons = {
            success: `
                <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            `,
            error: `
                <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            `,
            warning: `
                <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            `,
            info: `
                <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            `
        };
        return icons[this.options.type] || icons.info;
    }

    /**
     * Get color classes for alert type
     * @private
     */
    getColorClasses() {
        const colors = {
            success: {
                bg: 'bg-green-50',
                border: 'border-green-200',
                text: 'text-green-800',
                button: 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
            },
            error: {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-800',
                button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
            },
            warning: {
                bg: 'bg-yellow-50',
                border: 'border-yellow-200',
                text: 'text-yellow-800',
                button: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500'
            },
            info: {
                bg: 'bg-blue-50',
                border: 'border-blue-200',
                text: 'text-blue-800',
                button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
            }
        };
        return colors[this.options.type] || colors.info;
    }

    /**
     * Create alert content
     * @private
     */
    createContent() {
        const colors = this.getColorClasses();
        const icon = this.getIcon();
        
        return `
            <div class="rounded-md p-4 ${colors.bg} ${colors.border} border">
                <div class="flex">
                    <div class="flex-shrink-0">
                        ${icon}
                    </div>
                    <div class="ml-3">
                        ${this.options.title ? `
                            <h3 class="text-sm font-medium ${colors.text}">
                                ${this.options.title}
                            </h3>
                        ` : ''}
                        ${this.options.message ? `
                            <div class="mt-2 text-sm ${colors.text}">
                                <p>${this.options.message}</p>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Show the alert dialog
     */
    show() {
        const colors = this.getColorClasses();
        
        this.dialog = new Dialog({
            title: this.options.title,
            content: this.createContent(),
            primaryButtonText: this.options.confirmText,
            secondaryButtonText: this.options.showCancel ? this.options.cancelText : null,
            onPrimaryClick: () => {
                this.close();
                this.options.onConfirm();
            },
            onSecondaryClick: () => {
                this.close();
                this.options.onCancel();
            },
            showClose: !this.options.autoClose
        });

        // Apply custom styling to buttons
        const primaryBtn = this.dialog.element.querySelector('.primary-btn');
        if (primaryBtn) {
            primaryBtn.className = `primary-btn inline-flex justify-center w-full px-4 py-2 text-base font-medium text-white border border-transparent rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 sm:col-start-2 sm:text-sm ${colors.button}`;
        }

        this.dialog.show();

        // Auto-close functionality
        if (this.options.autoClose) {
            this.autoCloseTimer = setTimeout(() => {
                this.close();
            }, this.options.autoCloseDelay);
        }
    }

    /**
     * Close the alert dialog
     */
    close() {
        if (this.autoCloseTimer) {
            clearTimeout(this.autoCloseTimer);
            this.autoCloseTimer = null;
        }
        
        if (this.dialog) {
            this.dialog.close();
            this.dialog = null;
        }
    }

    /**
     * Destroy the alert dialog
     */
    destroy() {
        if (this.autoCloseTimer) {
            clearTimeout(this.autoCloseTimer);
            this.autoCloseTimer = null;
        }
        
        if (this.dialog) {
            this.dialog.destroy();
            this.dialog = null;
        }
    }
}

/**
 * Static methods for quick alert creation
 */
class Alert {
    /**
     * Show a success alert
     * @param {string|Object} message - Alert message or options object
     * @param {Object} options - Additional options
     */
    static success(message, options = {}) {
        const alertOptions = typeof message === 'string' 
            ? { message, type: 'success', ...options }
            : { type: 'success', ...message, ...options };
        
        const alert = new AlertDialog(alertOptions);
        alert.show();
        return alert;
    }

    /**
     * Show an error alert
     * @param {string|Object} message - Alert message or options object
     * @param {Object} options - Additional options
     */
    static error(message, options = {}) {
        const alertOptions = typeof message === 'string' 
            ? { message, type: 'error', ...options }
            : { type: 'error', ...message, ...options };
        
        const alert = new AlertDialog(alertOptions);
        alert.show();
        return alert;
    }

    /**
     * Show a warning alert
     * @param {string|Object} message - Alert message or options object
     * @param {Object} options - Additional options
     */
    static warning(message, options = {}) {
        const alertOptions = typeof message === 'string' 
            ? { message, type: 'warning', ...options }
            : { type: 'warning', ...message, ...options };
        
        const alert = new AlertDialog(alertOptions);
        alert.show();
        return alert;
    }

    /**
     * Show an info alert
     * @param {string|Object} message - Alert message or options object
     * @param {Object} options - Additional options
     */
    static info(message, options = {}) {
        const alertOptions = typeof message === 'string' 
            ? { message, type: 'info', ...options }
            : { type: 'info', ...message, ...options };
        
        const alert = new AlertDialog(alertOptions);
        alert.show();
        return alert;
    }

    /**
     * Show a confirmation dialog
     * @param {string|Object} message - Alert message or options object
     * @param {Object} options - Additional options
     */
    static confirm(message, options = {}) {
        const alertOptions = typeof message === 'string' 
            ? { 
                message, 
                type: 'warning', 
                showCancel: true,
                confirmText: 'Confirm',
                cancelText: 'Cancel',
                ...options 
            }
            : { 
                type: 'warning', 
                showCancel: true,
                confirmText: 'Confirm',
                cancelText: 'Cancel',
                ...message, 
                ...options 
            };
        
        const alert = new AlertDialog(alertOptions);
        alert.show();
        return alert;
    }

    /**
     * Show a toast notification (auto-closing)
     * @param {string|Object} message - Alert message or options object
     * @param {Object} options - Additional options
     */
    static toast(message, options = {}) {
        const alertOptions = typeof message === 'string' 
            ? { 
                message, 
                type: 'info', 
                autoClose: true,
                autoCloseDelay: 3000,
                showClose: false,
                ...options 
            }
            : { 
                type: 'info', 
                autoClose: true,
                autoCloseDelay: 3000,
                showClose: false,
                ...message, 
                ...options 
            };
        
        const alert = new AlertDialog(alertOptions);
        alert.show();
        return alert;
    }
}

window.Alert = Alert; // Expose Alert globally