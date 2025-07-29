/**
 * Subscription Dialog System
 * Centralized subscription checking and dialog display for the entire application
 * Self-contained within the subscriptions app for portability
 */

// Subscription Dialog Configuration - will be loaded from database
let SUBSCRIPTION_DIALOGS = {};

// Store escape handler reference globally
let currentEscapeHandler = null;

/**
 * Load subscription dialog data from the server
 */
async function loadSubscriptionDialogData() {
    try {
        const response = await fetch('/subscriptions/api/dialog-data/');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                SUBSCRIPTION_DIALOGS = data.dialog_data;
                console.log('Subscription dialog data loaded successfully');
            } else {
                console.error('Failed to load subscription dialog data:', data.error);
                // Fallback to default data
                setDefaultDialogData();
            }
        } else {
            console.error('Failed to load subscription dialog data');
            // Fallback to default data
            setDefaultDialogData();
        }
    } catch (error) {
        console.error('Error loading subscription dialog data:', error);
        // Fallback to default data
        setDefaultDialogData();
    }
}

/**
 * Set default dialog data as fallback
 */
function setDefaultDialogData() {
    SUBSCRIPTION_DIALOGS = {
        plus: {
            title: "Upgrade to Plus",
            message: "This feature is available with our Plus plan. Upgrade to unlock premium features and enhance your experience.",
            features: [
                "AI-powered resume conversion to ATS format",
                "Save unlimited resumes",
                "Multiple professional templates", 
                "Export to PDF and Word",
                "Resume optimization tools",
                "Priority customer support"
            ],
            upgrade_url: "/subscriptions/pricing/?plan=plus"
        },
        ultimate: {
            title: "Upgrade to Ultimate",
            message: "Advanced features and AI-powered tools are available with our Ultimate plan. Get the best tools for your success.",
            features: [
                "Everything in Plus",
                "AI-powered resume optimization",
                "ATS compatibility scoring",
                "Interview preparation tools",
                "Advanced analytics",
                "Priority support"
            ],
            upgrade_url: "/subscriptions/pricing/?plan=ultimate"
        }
    };
}

/**
 * Show subscription dialog for the specified plan
 * @param {string} requiredPlan - The plan required ('Plus' or 'Ultimate')
 */
function showSubscriptionDialog(requiredPlan) {
    console.log('🔍 DEBUG: showSubscriptionDialog called');
    console.log('📋 Required plan:', requiredPlan);
    console.log('👤 User plan:', window.userSubscriptionPlan);
    console.log('📋 Stack trace:', new Error().stack);
    
    const dialog = SUBSCRIPTION_DIALOGS[requiredPlan.toLowerCase()] || SUBSCRIPTION_DIALOGS.plus;
    
    // Create subscription dialog element
    const dialogElement = document.createElement("div");
    dialogElement.className = "fixed inset-0 z-[9999] overflow-y-auto";
    dialogElement.id = "subscription-dialog";
    
    const dialogContent = `
        <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            
            <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div class="sm:flex sm:items-start">
                        <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                            <svg class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                            <h3 class="text-lg leading-6 font-medium text-gray-900">
                                ${dialog.title}
                            </h3>
                            <div class="mt-2">
                                <p class="text-sm text-gray-500">
                                    ${dialog.message}
                                </p>
                                <div class="mt-4">
                                    <h4 class="text-sm font-medium text-gray-900 mb-2">Features included:</h4>
                                    <ul class="text-sm text-gray-600 space-y-1">
                                        ${dialog.features.map(feature => `<li>• ${feature}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <a href="${dialog.upgrade_url}" 
                       class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm">
                        Upgrade to ${requiredPlan}
                    </a>
                    <button type="button" 
                            onclick="closeSubscriptionDialog()"
                            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    `;
    
    dialogElement.innerHTML = dialogContent;
    document.body.appendChild(dialogElement);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Close on outside click
    dialogElement.addEventListener('click', function(e) {
        if (e.target === dialogElement) {
            closeSubscriptionDialog();
        }
    });
    
    // Close on escape key
    currentEscapeHandler = function(e) {
        if (e.key === 'Escape') {
            closeSubscriptionDialog();
        }
    };
    document.addEventListener('keydown', currentEscapeHandler);
}

/**
 * Close the subscription dialog
 */
function closeSubscriptionDialog() {
    const dialog = document.getElementById('subscription-dialog');
    if (dialog) {
        // Remove the escape key handler
        if (currentEscapeHandler) {
            document.removeEventListener('keydown', currentEscapeHandler);
            currentEscapeHandler = null;
        }
        
        dialog.remove();
        document.body.style.overflow = 'auto';
    }
}

/**
 * Check if user has access to a specific subscription level
 * @param {string} requiredPlan - The plan required ('Plus' or 'Ultimate')
 * @returns {boolean} - True if user has access, false otherwise
 */
function hasSubscriptionAccess(requiredPlan) {
    const userPlan = window.userSubscriptionPlan || 'Free';
    const planHierarchy = {'Free': 0, 'Plus': 1, 'Ultimate': 2};
    
    const userLevel = planHierarchy[userPlan] || 0;
    const requiredLevel = planHierarchy[requiredPlan] || 1;
    
    return userLevel >= requiredLevel;
}

/**
 * Decorator function to check subscription before executing a function
 * @param {string} requiredPlan - The plan required ('Plus' or 'Ultimate')
 * @param {Function} originalFunction - The function to execute if access is granted
 * @returns {Function} - Wrapped function that checks subscription first
 */
function withSubscriptionCheck(requiredPlan, originalFunction) {
    return function(...args) {
        if (!hasSubscriptionAccess(requiredPlan)) {
            // Show subscription dialog
            showSubscriptionDialog(requiredPlan);
            return false;
        }
        
        // User has access, proceed with original function
        return originalFunction.apply(this, args);
    };
}

/**
 * Check subscription access and show dialog if needed
 * @param {string} requiredPlan - The plan required ('Plus' or 'Ultimate')
 * @returns {boolean} - True if user has access, false otherwise
 */
function checkSubscriptionAccess(requiredPlan) {
    console.log('🔍 DEBUG: checkSubscriptionAccess called');
    console.log('📋 Required plan:', requiredPlan);
    console.log('👤 User plan:', window.userSubscriptionPlan);
    console.log('📋 Stack trace:', new Error().stack);
    
    if (!hasSubscriptionAccess(requiredPlan)) {
        console.log('❌ User does not have access, showing dialog');
        showSubscriptionDialog(requiredPlan);
        return false;
    }
    console.log('✅ User has access');
    return true;
}

// Export functions to global scope for use across the application
window.showSubscriptionDialog = showSubscriptionDialog;
window.closeSubscriptionDialog = closeSubscriptionDialog;
window.hasSubscriptionAccess = hasSubscriptionAccess;
window.withSubscriptionCheck = withSubscriptionCheck;
window.checkSubscriptionAccess = checkSubscriptionAccess;

// Load subscription dialog data when the script loads
loadSubscriptionDialogData();

// Log that subscription utilities are loaded
console.log('Subscription dialog system loaded successfully'); 