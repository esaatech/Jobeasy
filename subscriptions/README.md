# Django Subscription App

A reusable Django app for handling subscription plans and payments using Stripe.

## Features
- Flexible subscription plans with multiple durations
- Stripe integration for payment processing
- Customizable features for each plan
- Reusable across different types of subscriptions
- Success/failure handling with custom return URLs
- **Centralized feature management** with admin interface
- **Dynamic subscription dialogs** that pull features from database

## Models

### SubscriptionPlan
Base model for defining subscription plans.
```python
class SubscriptionPlan(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    features = models.ManyToManyField('Feature', through='PlanFeature')
```

### FeatureCatalog
Defines features that can be included in subscription plans.
```python
class FeatureCatalog(BaseModel):
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    type = models.CharField(choices=[('TOOL', 'Tool'), ('SERVICE', 'Service')])
    is_active = models.BooleanField(default=True)
```

### PlanDuration
Defines available durations and prices for subscription plans.
```python
class PlanDuration(BaseModel):
    plan = models.ForeignKey(SubscriptionPlan, related_name='durations')
    duration_type = models.CharField(choices=DURATION_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100)
```

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

# Set up default subscription plans and features
python manage.py setup_subscription_plans
```

### 2. Admin Configuration
The app provides a comprehensive admin interface for managing:

#### Features (FeatureCatalog)
- Create and manage features/tools
- Set feature types (Tool/Service)
- Enable/disable features
- Auto-generate identifiers from names

#### Subscription Plans
- Create subscription plans
- Assign features to plans
- Set full access flags
- Manage plan durations and pricing

#### Plan Durations
- Set up multiple pricing tiers (monthly, yearly, etc.)
- Configure Stripe price IDs
- Enable/disable specific durations

#### User Subscriptions
- View all user subscriptions
- Monitor subscription status
- Track payment history

### 3. Centralized Feature Management

#### Admin Interface
Access the admin at `/admin/subscriptions/` to:
- **Features**: Add/edit features like "AI Resume Conversion", "ATS Optimization", etc.
- **Plans**: Configure Plus/Ultimate plans with their features
- **Durations**: Set pricing for monthly/yearly subscriptions

#### Management Command
```bash
# Set up default subscription plans and features
python manage.py setup_subscription_plans
```

This command creates:
- **Free Plan**: Basic features
- **Plus Plan**: Enhanced features including AI resume conversion
- **Ultimate Plan**: Advanced features with interview preparation

#### Default Features Created
The setup command creates these features:

**Free Features:**
- Basic Resume Creation
- Professional Templates
- Cover Letter Generation

**Plus Features:**
- Resume Saving
- Resume Upload (AI conversion to ATS format)
- ATS Optimization
- All Resume Templates
- Enhanced Cover Letters

**Ultimate Features:**
- Interview Preparation
- Priority Support
- Advanced Analytics

### 4. Dynamic Subscription Dialogs

The subscription dialog system now pulls features directly from the database:

#### API Endpoint
- **URL**: `/subscriptions/api/dialog-data/`
- **Method**: GET
- **Returns**: JSON with Plus/Ultimate plan features

#### Frontend Integration
The dialog automatically loads features from the database:
```javascript
// Features are loaded automatically when the script loads
loadSubscriptionDialogData();

// Fallback to default features if API fails
setDefaultDialogData();
```

#### Consistency Across the App
- **Subscription Dialog**: Uses database features
- **Pricing Page**: Uses database features  
- **Purchase Page**: Uses database features
- **Admin Interface**: Single source of truth

### 5. Integration in Your App

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
6. **Features are now managed centrally through admin**
7. **Subscription dialogs automatically use database features**
8. **Management command runs automatically in entrypoint.sh**

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
- **`views.py`**: API endpoint for dialog data (`get_subscription_dialog_data`)

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
    // This view requires Plus subscription
    // If user doesn't have access, they'll be redirected to subscription page
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
        // Handle access denied
        return JsonResponse({'error': 'Subscription required'})
    
    // Proceed with protected functionality
    pass
```

### Dynamic Dialog Configuration

The dialog content is now loaded from the database via API:

```javascript
// Automatically loads features from database
loadSubscriptionDialogData();

// API endpoint: /subscriptions/api/dialog-data/
// Returns:
{
    "success": true,
    "dialog_data": {
        "plus": {
            "title": "Upgrade to Plus",
            "message": "This feature is available with our Plus plan...",
            "features": ["AI-powered resume conversion", "Save unlimited resumes", ...],
            "upgrade_url": "/subscriptions/pricing/?plan=plus"
        },
        "ultimate": {
            // Similar structure for Ultimate plan
        }
    }
}
```

### Available Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `withSubscriptionCheck(plan, function)` | Decorator that protects a function | Wrapped function |
| `checkSubscriptionAccess(plan)` | Check access and show dialog if needed | Boolean |
| `hasSubscriptionAccess(plan)` | Pure access check without dialog | Boolean |
| `showSubscriptionDialog(plan)` | Show dialog for specific plan | void |
| `closeSubscriptionDialog()` | Close the dialog | void |
| `loadSubscriptionDialogData()` | Load features from database | Promise |

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

**Via Admin Interface (Recommended):**
- Go to `/admin/subscriptions/featurecatalog/`
- Add/edit features for each plan
- Changes automatically appear in dialogs

**Via Code:**
Edit the `setDefaultDialogData()` function in `subscription_dialog.js` as fallback.

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
6. **Feature Management**: Use admin interface to manage features centrally

### Troubleshooting

#### Dialog Not Showing
- Check if `subscription_dialog.js` is loaded
- Verify `window.userSubscriptionPlan` is set
- Check browser console for errors
- Verify API endpoint `/subscriptions/api/dialog-data/` is accessible

#### Function Not Protected
- Ensure `withSubscriptionCheck()` is called correctly
- Check that the original function is passed as second parameter
- Verify the protected function is actually called

#### Backend Decorator Issues
- Import the decorator correctly
- Ensure user is authenticated
- Check subscription model relationships

#### Features Not Loading
- Check if management command ran: `python manage.py setup_subscription_plans`
- Verify features exist in admin interface
- Check API endpoint response in browser console

### Moving to Another App

To move the subscription system to another Django project:

1. Copy the `subscriptions` app folder
2. Include the static files in your new project
3. Update the base template to load `subscription_dialog.js`
4. Set `window.userSubscriptionPlan` in your templates
5. Update dialog URLs to match your new project structure
6. Run `python manage.py setup_subscription_plans` to create default features

The system is designed to be self-contained and portable!