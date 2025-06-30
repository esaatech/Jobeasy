/**
 * Alert System Usage Examples
 * This file demonstrates how to use the Alert system in your applications
 */

// Import the Alert system (adjust path as needed)
// import Alert from '../utils/alert.js';

// Example 1: Basic alerts
function showBasicAlerts() {
    // Success alert
    Alert.success('Your resume has been saved successfully!');
    
    // Error alert
    Alert.error('Failed to save resume. Please try again.');
    
    // Warning alert
    Alert.warning('You have unsaved changes. Are you sure you want to leave?');
    
    // Info alert
    Alert.info('Your session will expire in 5 minutes.');
}

// Example 2: Alerts with titles
function showAlertsWithTitles() {
    Alert.success({
        title: 'Success!',
        message: 'Your profile has been updated successfully.'
    });
    
    Alert.error({
        title: 'Error',
        message: 'Unable to connect to the server. Please check your internet connection.'
    });
}

// Example 3: Confirmation dialogs
function showConfirmationDialogs() {
    // Basic confirmation
    Alert.confirm('Are you sure you want to delete this resume?', {
        onConfirm: () => {
            console.log('User confirmed deletion');
            // Perform deletion
            deleteResume();
        },
        onCancel: () => {
            console.log('User cancelled deletion');
        }
    });
    
    // Confirmation with custom buttons
    Alert.confirm({
        title: 'Delete Resume',
        message: 'This action cannot be undone. Are you sure you want to proceed?',
        confirmText: 'Delete',
        cancelText: 'Keep',
        onConfirm: () => {
            console.log('Resume deleted');
        }
    });
}

// Example 4: Toast notifications
function showToastNotifications() {
    // Auto-closing toast
    Alert.toast('Changes saved automatically');
    
    // Toast with custom duration
    Alert.toast('File uploaded successfully', {
        type: 'success',
        autoCloseDelay: 5000
    });
    
    // Toast with callback
    Alert.toast('Processing your request...', {
        type: 'info',
        autoCloseDelay: 2000,
        onConfirm: () => {
            console.log('Toast closed');
        }
    });
}

// Example 5: Advanced usage with custom options
function showAdvancedAlerts() {
    // Alert with custom styling
    Alert.success({
        title: 'Premium Feature',
        message: 'You have successfully upgraded to premium!',
        confirmText: 'Continue',
        onConfirm: () => {
            window.location.href = '/dashboard';
        }
    });
    
    // Error with retry functionality
    Alert.error({
        title: 'Connection Error',
        message: 'Failed to load data. Please check your connection.',
        confirmText: 'Retry',
        cancelText: 'Cancel',
        onConfirm: () => {
            retryConnection();
        }
    });
}

// Example 6: Form validation alerts
function validateForm() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (!email) {
        Alert.error('Please enter your email address');
        return false;
    }
    
    if (!password) {
        Alert.error('Please enter your password');
        return false;
    }
    
    if (password.length < 6) {
        Alert.warning('Password must be at least 6 characters long');
        return false;
    }
    
    Alert.success('Form validation passed!');
    return true;
}

// Example 7: API response handling
async function handleApiResponse(response) {
    if (response.ok) {
        const data = await response.json();
        Alert.success('Data loaded successfully');
        return data;
    } else {
        Alert.error('Failed to load data. Please try again later.');
        throw new Error('API request failed');
    }
}

// Example 8: Loading states
function showLoadingAlert() {
    const loadingAlert = Alert.info({
        title: 'Processing',
        message: 'Please wait while we process your request...',
        confirmText: 'Cancel',
        autoClose: false,
        onConfirm: () => {
            // Cancel the operation
            cancelOperation();
        }
    });
    
    // Simulate async operation
    setTimeout(() => {
        loadingAlert.close();
        Alert.success('Operation completed successfully!');
    }, 3000);
}

// Example 9: Multiple alerts
function showMultipleAlerts() {
    // Show multiple toasts
    Alert.toast('First notification', { type: 'info' });
    
    setTimeout(() => {
        Alert.toast('Second notification', { type: 'success' });
    }, 1000);
    
    setTimeout(() => {
        Alert.toast('Third notification', { type: 'warning' });
    }, 2000);
}

// Example 10: Custom alert types
function showCustomAlert() {
    const customAlert = new AlertDialog({
        type: 'info',
        title: 'Custom Alert',
        message: 'This is a custom alert with special styling.',
        confirmText: 'Got it',
        showCancel: true,
        cancelText: 'Learn More',
        onConfirm: () => {
            console.log('User clicked Got it');
        },
        onCancel: () => {
            window.open('/help', '_blank');
        }
    });
    
    customAlert.show();
}

// Utility functions (examples)
function deleteResume() {
    // Implementation for resume deletion
    console.log('Deleting resume...');
}

function retryConnection() {
    // Implementation for retrying connection
    console.log('Retrying connection...');
}

function cancelOperation() {
    // Implementation for canceling operation
    console.log('Operation cancelled');
}

// Export examples for use in other files
export {
    showBasicAlerts,
    showAlertsWithTitles,
    showConfirmationDialogs,
    showToastNotifications,
    showAdvancedAlerts,
    validateForm,
    handleApiResponse,
    showLoadingAlert,
    showMultipleAlerts,
    showCustomAlert
}; 