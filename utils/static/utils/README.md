# Alert Dialog System

A comprehensive, reusable alert dialog system for Django applications.

## Features

- Multiple alert types: Success, Error, Warning, Info
- Confirmation dialogs with customizable buttons
- Toast notifications with auto-close
- Responsive design
- Consistent styling across all apps

## Quick Start

### 1. Include CSS and JS files

```html
<link rel="stylesheet" href="{% static 'css/alerts.css' %}">
<script type="module" src="{% static 'utils/alert.js' %}"></script>
```

### 2. Basic Usage

```javascript
// Success alert
Alert.success('Your resume has been saved successfully!');

// Error alert
Alert.error('Failed to save resume. Please try again.');

// Warning alert
Alert.warning('You have unsaved changes.');

// Info alert
Alert.info('Your session will expire in 5 minutes.');

// Confirmation dialog
Alert.confirm('Are you sure you want to delete this resume?', {
    onConfirm: () => {
        deleteResume();
    }
});

// Toast notification
Alert.toast('Changes saved automatically');
```

### 3. Advanced Usage

```javascript
// Alert with title and custom options
Alert.success({
    title: 'Success!',
    message: 'Your profile has been updated successfully.',
    confirmText: 'Continue',
    onConfirm: () => {
        window.location.href = '/dashboard';
    }
});

// Custom alert instance
const alert = new AlertDialog({
    type: 'warning',
    title: 'Custom Alert',
    message: 'This is a custom alert.',
    confirmText: 'Got it',
    showCancel: true,
    cancelText: 'Learn More'
});

alert.show();
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `type` | string | 'info' | Alert type (success, error, warning, info) |
| `title` | string | '' | Alert title |
| `message` | string | '' | Alert message |
| `confirmText` | string | 'OK' | Primary button text |
| `cancelText` | string | 'Cancel' | Secondary button text |
| `showCancel` | boolean | false | Whether to show cancel button |
| `onConfirm` | function | () => {} | Callback for confirm button |
| `onCancel` | function | () => {} | Callback for cancel button |
| `autoClose` | boolean | false | Whether to auto-close the alert |
| `autoCloseDelay` | number | 3000 | Auto-close delay in milliseconds |

## Integration with Django

### In Django Templates

```html
<script>
    // Show success message after form submission
    if ('{{ success_message }}') {
        Alert.success('{{ success_message }}');
    }
    
    // Show error message
    if ('{{ error_message }}') {
        Alert.error('{{ error_message }}');
    }
</script>
```

### API Response Handling

```javascript
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
```

## Files

- `alert.js` - Main alert system implementation
- `dialog.js` - Base dialog component
- `alerts.css` - Styling for alerts
- `alert-examples.js` - Usage examples 