from .subscription_messages import (
    PLUS_UPGRADE_TITLE, PLUS_UPGRADE_MESSAGE,
    ULTIMATE_UPGRADE_TITLE, ULTIMATE_UPGRADE_MESSAGE,
    RESUME_UPDATE_PLUS_TITLE, RESUME_UPDATE_PLUS_MESSAGE,
    RESUME_UPDATE_ULTIMATE_TITLE, RESUME_UPDATE_ULTIMATE_MESSAGE,
    PLUS_FEATURES, ULTIMATE_FEATURES
)

def get_subscription_javascript():
    """Returns JavaScript code for handling subscription dialogs in the frontend."""
    return """
// Subscription Dialog Handling Utilities
const SUBSCRIPTION_DIALOGS = {
    plus_upgrade: {
        title: "%s",
        message: "%s",
        level: "info",
        plan: "plus",
        features: %s,
        upgrade_url: "/subscriptions/pricing/?plan=plus"
    },
    ultimate_upgrade: {
        title: "%s", 
        message: "%s",
        level: "info",
        plan: "ultimate",
        features: %s,
        upgrade_url: "/subscriptions/pricing/?plan=ultimate"
    },
    resume_update_plus: {
        title: "%s",
        message: "%s", 
        level: "warning",
        plan: "plus",
        features: %s
    },
    resume_update_ultimate: {
        title: "%s",
        message: "%s",
        level: "warning", 
        plan: "ultimate",
        features: %s
    }
};

// Frontend Subscription Decorator
function requireSubscription(requiredPlan = 'Plus') {
    return function(target, propertyKey, descriptor) {
        const originalMethod = descriptor.value;
        
        descriptor.value = function(...args) {
            // Get user's subscription from global variable
            const userPlan = window.userSubscriptionPlan || 'Free';
            const planHierarchy = {'Free': 0, 'Plus': 1, 'Ultimate': 2, 'Test': 2};
            
            const userLevel = planHierarchy[userPlan] || 0;
            const requiredLevel = planHierarchy[requiredPlan] || 1;
            
            if (userLevel < requiredLevel) {
                // Show subscription dialog
                showSubscriptionDialog(requiredPlan);
                return false;
            }
            
            // User has access, proceed with original method
            return originalMethod.apply(this, args);
        };
        
        return descriptor;
    };
}

// Alternative function wrapper for non-decorator environments
function withSubscriptionCheck(requiredPlan, originalFunction) {
    return function(...args) {
        // Get user's subscription from global variable
        const userPlan = window.userSubscriptionPlan || 'Free';
        const planHierarchy = {'Free': 0, 'Plus': 1, 'Ultimate': 2, 'Test': 2};
        
        const userLevel = planHierarchy[userPlan] || 0;
        const requiredLevel = planHierarchy[requiredPlan] || 1;
        
        if (userLevel < requiredLevel) {
            // Show subscription dialog
            showSubscriptionDialog(requiredPlan);
            return false;
        }
        
        // User has access, proceed with original function
        return originalFunction.apply(this, args);
    };
}

function showSubscriptionDialog(dialogType = "plus_upgrade") {
    const dialog = SUBSCRIPTION_DIALOGS[dialogType] || SUBSCRIPTION_DIALOGS.plus_upgrade;
    
    // Create subscription dialog element
    const dialogElement = document.createElement("div");
    dialogElement.className = "fixed inset-0 z-50 overflow-y-auto";
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
                        Upgrade to ${dialog.plan.charAt(0).toUpperCase() + dialog.plan.slice(1)}
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
}

function closeSubscriptionDialog() {
    const dialog = document.getElementById('subscription-dialog');
    if (dialog) {
        dialog.remove();
        document.body.style.overflow = 'auto';
    }
}

function upgradeToPlan(plan) {
    // Close the dialog first
    closeSubscriptionDialog();
    
    // Redirect to pricing page with plan pre-selected
    const pricingUrl = `/subscriptions/pricing/?plan=${plan}`;
    window.location.href = pricingUrl;
}

function checkSubscriptionAccess(feature, requiredPlan = 'plus') {
    // This function would typically make an AJAX call to check user's subscription
    // For now, we'll assume the backend handles this and returns appropriate response
    return fetch(`/subscriptions/check-access/${feature}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.has_access) {
            const dialogType = requiredPlan === 'ultimate' ? 'ultimate_upgrade' : 'plus_upgrade';
            showSubscriptionDialog(dialogType);
            return false;
        }
        return true;
    })
    .catch(error => {
        console.error('Error checking subscription access:', error);
        return false;
    });
}

// Auto-close dialog when clicking outside
document.addEventListener('click', function(event) {
    const dialog = document.getElementById('subscription-dialog');
    if (dialog && event.target === dialog) {
        closeSubscriptionDialog();
    }
});

// Close dialog on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeSubscriptionDialog();
    }
});
""" % (
        PLUS_UPGRADE_TITLE, PLUS_UPGRADE_MESSAGE, str(PLUS_FEATURES),
        ULTIMATE_UPGRADE_TITLE, ULTIMATE_UPGRADE_MESSAGE, str(ULTIMATE_FEATURES),
        RESUME_UPDATE_PLUS_TITLE, RESUME_UPDATE_PLUS_MESSAGE, str(PLUS_FEATURES),
        RESUME_UPDATE_ULTIMATE_TITLE, RESUME_UPDATE_ULTIMATE_MESSAGE, str(ULTIMATE_FEATURES)
    ) 