# Django Subscription App

A reusable Django app for handling subscription plans and payments using Stripe.

## Features
- Flexible subscription plans with multiple durations
- Stripe integration for payment processing
- Customizable features for each plan
- Reusable across different types of subscriptions
- Success/failure handling with custom return URLs

## Models

### SubscriptionPlan
Base model for defining subscription plans.
python
class SubscriptionPlan(BaseModel):
name = models.CharField(max_length=100)
description = models.TextField()
is_active = models.BooleanField(default=True)
features = models.ManyToManyField('Feature', through='PlanFeature')
python
class SubscriptionPlan(BaseModel):
name = models.CharField(max_length=100)
description = models.TextField()
is_active = models.BooleanField(default=True)
features = models.ManyToManyField('Feature', through='PlanFeature')

python
class PlanDuration(BaseModel):
plan = models.ForeignKey(SubscriptionPlan, related_name='durations')
duration_type = models.CharField(choices=DURATION_TYPES)
price = models.DecimalField(max_digits=10, decimal_places=2)
stripe_price_id = models.CharField(max_length=100)

### Feature
Defines features that can be included in subscription plans.

## Usage

### 1. Installation
```bash
# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    ...
    'subscriptions',
]

# Run migrations
python manage.py migrate subscriptions
```


bash:subscriptions/README.md
Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
...
'subscriptions',
]
Run migrations
python manage.py migrate subscriptions
```

### 2. Admin Configuration
```python
# Create subscription plans in admin
- Create features (tools/services)
- Create subscription plan
- Add durations with prices
- Link features to plan
```

### 3. Integration in Your App

#### URLs Configuration
```python
# your_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path(
        'your-subscription/',
        views.YourSubscriptionView.as_view(),
        name='your_subscription'
    ),
]
```

#### View Implementation
```python
# your_app/views.py
from django.views.generic import View
from subscriptions.models import SubscriptionPlan

class YourSubscriptionView(View):
    def get(self, request):
        plan = get_object_or_404(
            SubscriptionPlan,
            name='Your Plan Name',
            is_active=True
        )
        
        return_url = reverse('your_app:success')
        purchase_url = (
            f"{reverse('subscriptions:plan_purchase', args=[plan.id])}"
            f"?return_url={return_url}"
        )
        
        return redirect(purchase_url)
```

#### Template Usage
```html
<a href="{% url 'your_app:your_subscription' %}" class="btn">
    Subscribe Now
</a>
```

## Payment Flow

1. User selects subscription from your app
2. Redirected to subscription purchase page
3. User selects duration and enters payment details
4. Payment processed through Stripe
5. On success, redirected to your success URL
6. On failure, error displayed on purchase page

## Customization

### Adding Custom Features
```python
# Create features in admin
- Tools (e.g., "AI Writer", "Document Scanner")
- Services (e.g., "24/7 Support", "Priority Processing")
```

### Custom Duration Types
```python
# subscriptions/models.py
DURATION_TYPES = (
    ('ONE_TIME', 'One Time'),
    ('MONTHLY', 'Monthly'),
    ('QUARTERLY', 'Quarterly'),
    ('YEARLY', 'Yearly'),
)
```

## Example Implementation

```python
# study_abroad/views.py
class StudyAbroadSubscriptionView(View):
    def get(self, request):
        plan = get_object_or_404(
            SubscriptionPlan,
            name='Study Abroad',
            is_active=True
        )
        
        return_url = reverse('study_abroad:success')
        purchase_url = (
            f"{reverse('subscriptions:plan_purchase', args=[plan.id])}"
            f"?return_url={return_url}"
        )
        
        return redirect(purchase_url)
```

## Notes

1. Ensure Stripe keys are configured in settings.py
2. Create and manage plans through Django admin
3. Each plan can have multiple durations with different prices
4. Features can be reused across different plans
5. Return URLs can be customized per implementation

# Subscriptions App

## Overview

The Subscriptions app manages user subscription plans and provides a centralized subscription dialog system for restricting access to premium features across the application.

## Subscription Plans

- **Free**: Basic access to core features
- **Plus**: Enhanced features including resume optimization and unlimited saves
- **Ultimate**: Advanced AI-powered features and analytics

## Subscription Dialog System

### Overview

The subscription dialog system provides a consistent, professional way to restrict access to premium features and encourage users to upgrade their subscription. It's self-contained within the subscriptions app for portability.

### Files

- **`static/subscriptions/js/subscription_dialog.js`**: Main dialog system
- **`decorators.py`**: Backend decorators for view protection
- **`utils.py`**: Backend utilities for subscription checking

### Frontend Usage

#### 1. Basic Function Protection (Recommended)

Use the `withSubscriptionCheck` decorator to protect functions:

```javascript
// Protect a function that requires Plus subscription
const protectedFunction = withSubscriptionCheck('Plus', function() {
    // Your protected code here
    console.log('User has Plus access!');
    performResumeOptimization();
});

// Call the protected function
protectedFunction();
```

#### 2. Simple Access Check

Use `checkSubscriptionAccess` for simple checks:

```javascript
// Check access and show dialog if needed
if (checkSubscriptionAccess('Ultimate')) {
    // User has access, proceed with code
    showAdvancedAnalytics();
}
```

#### 3. Pure Access Check (No Dialog)

Use `hasSubscriptionAccess` for pure checks without showing dialog:

```javascript
// Check access without showing dialog
if (hasSubscriptionAccess('Plus')) {
    // Custom logic here
    enablePremiumFeatures();
} else {
    // Custom handling
    showCustomUpgradeMessage();
}
```

#### 4. Manual Dialog Display

Show subscription dialog manually:

```javascript
// Show dialog for specific plan
showSubscriptionDialog('Plus');
```

### Backend Usage

#### 1. View Protection with Decorator

```python
from subscriptions.decorators import require_plus_subscription

@require_plus_subscription(feature_identifier='resume_update')
def upload_resume(request):
    # This view requires Plus subscription
    # If user doesn't have access, they'll be redirected to subscription page
    pass
```

#### 2. Manual Subscription Check

```python
from subscriptions.decorators import check_subscription_access

def some_view(request):
    access_info = check_subscription_access(
        user=request.user,
        feature_identifier='resume_update',
        required_plan='Plus'
    )
    
    if not access_info['has_access']:
        # Handle access denied
        return JsonResponse({'error': 'Subscription required'})
    
    # Proceed with protected functionality
    pass
```

### Dialog Configuration

The dialog content is configured in `subscription_dialog.js`:

```javascript
const SUBSCRIPTION_DIALOGS = {
    plus: {
        title: "Upgrade to Plus",
        message: "This feature is available with our Plus plan...",
        features: [
            "Save unlimited resumes",
            "Multiple professional templates",
            // ... more features
        ],
        upgrade_url: "/subscriptions/pricing/?plan=plus"
    },
    ultimate: {
        // Similar structure for Ultimate plan
    }
};
```

### Available Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `withSubscriptionCheck(plan, function)` | Decorator that protects a function | Wrapped function |
| `checkSubscriptionAccess(plan)` | Check access and show dialog if needed | Boolean |
| `hasSubscriptionAccess(plan)` | Pure access check without dialog | Boolean |
| `showSubscriptionDialog(plan)` | Show dialog for specific plan | void |
| `closeSubscriptionDialog()` | Close the dialog | void |

### Integration

#### 1. Load in Base Template

The dialog system is automatically loaded in `templates/base.html`:

```html
<!-- Subscription Dialog System -->
<script src="{% static 'subscriptions/js/subscription_dialog.js' %}"></script>
```

#### 2. Set User Subscription

The user's subscription plan is set globally:

```javascript
window.userSubscriptionPlan = '{{ user.subscription.plan.name|default:"Free" }}';
```

### Example Use Cases

#### Resume Builder - Tab Protection

```javascript
function switchTab(tabName) {
    if (tabName === 'optimize') {
        return withSubscriptionCheck('Plus', function() {
            performTabSwitch(tabName);
            return true;
        })();
    }
    return performTabSwitch(tabName);
}
```

#### Button Click Protection

```javascript
document.getElementById('premium-button').addEventListener('click', 
    withSubscriptionCheck('Ultimate', function() {
        // Premium functionality
        showAdvancedFeatures();
    })
);
```

#### Form Submission Protection

```javascript
document.getElementById('resume-form').addEventListener('submit', 
    withSubscriptionCheck('Plus', function(e) {
        // Allow form submission
        return true;
    })
);
```

### Customization

#### 1. Update Dialog Content

Edit the `SUBSCRIPTION_DIALOGS` object in `subscription_dialog.js` to change:
- Dialog titles and messages
- Feature lists
- Upgrade URLs

#### 2. Styling

The dialog uses Tailwind CSS classes. Modify the `dialogContent` template to change:
- Colors and styling
- Layout and spacing
- Button appearance

#### 3. Behavior

Customize dialog behavior by modifying:
- `showSubscriptionDialog()`: Dialog creation and display
- `closeSubscriptionDialog()`: Dialog cleanup
- Event handlers for closing

### Best Practices

1. **Use Decorators**: Prefer `withSubscriptionCheck()` for function protection
2. **Plan Hierarchy**: Remember Free < Plus < Ultimate
3. **Consistent Messaging**: Use the same dialog across the app
4. **Graceful Degradation**: Provide alternatives for free users
5. **Testing**: Test with different subscription levels

### Troubleshooting

#### Dialog Not Showing
- Check if `subscription_dialog.js` is loaded
- Verify `window.userSubscriptionPlan` is set
- Check browser console for errors

#### Function Not Protected
- Ensure `withSubscriptionCheck()` is called correctly
- Check that the original function is passed as second parameter
- Verify the protected function is actually called

#### Backend Decorator Issues
- Import the decorator correctly
- Ensure user is authenticated
- Check subscription model relationships

### Moving to Another App

To move the subscription system to another Django project:

1. Copy the `subscriptions` app folder
2. Include the static files in your new project
3. Update the base template to load `subscription_dialog.js`
4. Set `window.userSubscriptionPlan` in your templates
5. Update dialog URLs to match your new project structure

The system is designed to be self-contained and portable!