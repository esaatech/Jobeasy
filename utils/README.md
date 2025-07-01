# Utils App

A Django app containing reusable utilities and components that can be shared across multiple applications.

## Features

- **Alert System**: Comprehensive alert dialog system with multiple types and customization options
- **Date Utilities**: Helper functions for date manipulation
- **Error Handling**: Network error handling and user-friendly error messages
- **Reusable Components**: UI components that can be used across different apps

## Structure

```
utils/
├── static/
│   └── utils/
│       ├── css/
│       │   └── alerts.css          # Alert system styling
│       ├── components/
│       │   ├── alert.js            # Main alert system (regular script)
│       │   └── dialog.js           # Base dialog component (regular script)
├── templates/
│   └── utils/
│       └── alert_demo.html         # Django template for demo
├── error/                          # Error handling utilities
├── date_utils.py                   # Date utility functions
├── apps.py                         # Django app configuration
├── urls.py                         # URL patterns
├── views.py                        # Views
└── README.md                       # This file
```

## Alert System

The alert system provides a comprehensive, reusable alert dialog system with the following features:

### Features
- Multiple alert types: Success, Error, Warning, Info
- Confirmation dialogs with customizable buttons
- Toast notifications with auto-close
- Responsive design
- Consistent styling across all apps

### Usage

#### Basic Alerts
```javascript
// Success alert
window.Alert.success('Your resume has been saved successfully!');

// Error alert
window.Alert.error('Failed to save resume. Please try again.');

// Warning alert
window.Alert.warning('You have unsaved changes.');

// Info alert
window.Alert.info('Your session will expire in 5 minutes.');
```

#### Confirmation Dialogs
```javascript
window.Alert.confirm('Are you sure you want to delete this resume?', {
    onConfirm: () => {
        deleteResume();
    }
});
```

#### Toast Notifications
```javascript
window.Alert.toast('Changes saved automatically');
```

### Integration

1. **Include in Django Template**:
```html
{% load static %}
<link rel="stylesheet" href="{% static 'utils/css/alerts.css' %}">
<script src="{% static 'utils/components/dialog.js' %}"></script>
<script src="{% static 'utils/components/alert.js' %}"></script>
```

2. **No import needed in JavaScript**:
- Just use `window.Alert` in your inline or external scripts.
- No need for `import` or `type="module"` anywhere.

3. **Demo Page**: Visit `/utils/alert-demo/` to see all features in action

## Date Utilities

The `date_utils.py` file contains helper functions for date manipulation and formatting.

## Error Handling

The `error/` directory contains utilities for handling network errors and providing user-friendly error messages.

## Installation

1. Add `'utils'` to your `INSTALLED_APPS` in `settings.py`:
```python
INSTALLED_APPS = [
    # ... other apps
    'utils',
]
```

2. Include the utils URLs in your main `urls.py`:
```python
urlpatterns = [
    # ... other URL patterns
    path('utils/', include('utils.urls')),
]
```

3. Run migrations (if any):
```bash
python manage.py migrate
```

## Demo

Visit `/utils/alert-demo/` to see the alert system in action with interactive examples.

## Contributing

When adding new utilities to this app:

1. Follow the existing structure
2. Add appropriate documentation
3. Include examples if applicable
4. Update this README with new features

## License

This app is part of the Jobeas project and follows the same licensing terms. 