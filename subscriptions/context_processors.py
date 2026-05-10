from django.conf import settings

from .models import UserSubscription, SubscriptionPlan

def subscription_context(request):
    """
    Context processor to make user's current subscription available globally.
    """
    debug = settings.DEBUG
    context = {
        'show_ultimate_upgrade_promo': debug,
        # Automated job-service flow (start application, in-progress card): local/dev only
        'show_job_service_automation_ui': debug,
    }
    
    if request.user.is_authenticated:
        # Get user's current subscription (active)
        current_subscription = UserSubscription.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).select_related('plan', 'plan_duration').first()
        
        if not current_subscription:
            # If user has no active subscription, they're on the Free plan
            free_plan = SubscriptionPlan.objects.filter(name='Free', is_active=True).first()
            if free_plan:
                # Create a virtual current subscription for Free plan users
                current_subscription = type('obj', (object,), {
                    'plan': free_plan,
                    'plan_duration': None,
                    'status': 'ACTIVE'
                })()
        
        context['current_subscription'] = current_subscription
    else:
        context['current_subscription'] = None
    
    return context 