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