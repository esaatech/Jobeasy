# utils/error/network_error_frontend.py
from .network_error_messages import (
    NETWORK_TIMEOUT_TITLE, NETWORK_TIMEOUT_MESSAGE,
    NETWORK_CONNECTION_TITLE, NETWORK_CONNECTION_MESSAGE,
    NETWORK_GENERIC_TITLE, NETWORK_GENERIC_MESSAGE
)

def get_network_error_javascript():
    """Returns JavaScript code for handling network errors in the frontend."""
    return """
// Network Error Handling Utilities
const NETWORK_ERROR_MESSAGES = {
    network_timeout: {
        title: "%s",
        message: "%s",
        level: "warning"
    },
    network_connection: {
        title: "%s", 
        message: "%s",
        level: "error"
    },
    network_generic: {
        title: "%s",
        message: "%s", 
        level: "error"
    }
};

function showNetworkErrorDialog(errorType = "network_generic", customMessage = null) {
    const error = NETWORK_ERROR_MESSAGES[errorType] || NETWORK_ERROR_MESSAGES.network_generic;
    const message = customMessage || error.message;
    
    // Create error dialog element
    const dialog = document.createElement("div");
    dialog.className = `fixed top-8 left-1/2 transform -translate-x-1/2 z-50 bg-white border border-gray-300 shadow-lg rounded-lg p-6 max-w-sm w-full text-center ${
        error.level === "warning" ? "border-yellow-400" : "border-red-400"
    }`;
    
    dialog.innerHTML = `
        <div class="flex items-center justify-center mb-4">
            <div class="w-12 h-12 rounded-full flex items-center justify-center ${
                error.level === "warning" ? "bg-yellow-100 text-yellow-600" : "bg-red-100 text-red-600"
            }">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            </div>
        </div>
        <h3 class="text-lg font-bold mb-2 text-gray-900">${error.title}</h3>
        <p class="text-gray-700 mb-4">${message}</p>
        <button onclick="this.parentElement.remove()" class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
            Close
        </button>
    `;
    
    // Add to page
    document.body.appendChild(dialog);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (dialog.parentElement) {
            dialog.remove();
        }
    }, 5000);
}

function handleNetworkError(response, errorType = "network_generic") {
    if (!response.ok) {
        if (response.status === 408 || response.status === 504) {
            showNetworkErrorDialog("network_timeout");
        } else if (response.status === 0 || response.status >= 500) {
            showNetworkErrorDialog("network_connection");
        } else {
            showNetworkErrorDialog(errorType);
        }
        return true; // Error was handled
    }
    return false; // No error
}
""" % (
        NETWORK_TIMEOUT_TITLE, NETWORK_TIMEOUT_MESSAGE,
        NETWORK_CONNECTION_TITLE, NETWORK_CONNECTION_MESSAGE,
        NETWORK_GENERIC_TITLE, NETWORK_GENERIC_MESSAGE
    ) 