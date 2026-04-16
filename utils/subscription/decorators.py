from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from subscriptions.models import UserSubscription, SubscriptionPlan
from .subscription_dialog import get_plus_upgrade_dialog, get_ultimate_upgrade_dialog


PLAN_HIERARCHY = {
    'Free': 0,
    'Plus': 1,
    'Ultimate': 2,
    # Test should behave like Ultimate in authorization checks.
    'Test': 2,
}

def require_subscription(plan_name='Plus', feature_identifier=None):
    """
    Decorator to require a specific subscription plan for access.
    
    Args:
        plan_name (str): Required plan name ('Plus' or 'Ultimate')
        feature_identifier (str): Optional feature identifier to check
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Get user's active subscription
            active_subscription = UserSubscription.objects.filter(
                user=request.user,
                status='ACTIVE'
            ).select_related('plan').first()
            
            # If no active subscription, user is on Free plan
            if not active_subscription:
                return _handle_no_access(request, plan_name)
            
            # Check if user has the required plan
            user_plan_name = active_subscription.plan.name
            user_plan_level = PLAN_HIERARCHY.get(user_plan_name, 0)
            required_plan_level = PLAN_HIERARCHY.get(plan_name, 1)
            
            if user_plan_level < required_plan_level:
                return _handle_no_access(request, plan_name)
            
            # If feature identifier is provided, check specific feature access
            if feature_identifier:
                if not active_subscription.has_access_to_feature(feature_identifier):
                    return _handle_no_access(request, plan_name)
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator

def require_plus_subscription(feature_identifier=None):
    """Decorator to require Plus subscription."""
    return require_subscription('Plus', feature_identifier)

def require_ultimate_subscription(feature_identifier=None):
    """Decorator to require Ultimate subscription."""
    return require_subscription('Ultimate', feature_identifier)

def _handle_no_access(request, required_plan):
    """Handle cases where user doesn't have required subscription."""
    # For AJAX requests, return JSON response with upgrade dialog
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if required_plan == 'Ultimate':
            dialog_data = get_ultimate_upgrade_dialog()
        else:
            dialog_data = get_plus_upgrade_dialog()
        
        return JsonResponse({
            'success': False,
            'error': 'Subscription required',
            'dialog': dialog_data,
            'redirect_url': reverse('subscriptions:pricing')
        }, status=403)
    
    # For regular requests, redirect to pricing page
    return redirect('subscriptions:pricing')

def check_subscription_access(user, feature_identifier=None, required_plan='Plus'):
    """
    Utility function to check if a user has access to a feature.
    
    Args:
        user: User object
        feature_identifier (str): Optional feature identifier
        required_plan (str): Required plan name
        
    Returns:
        dict: {'has_access': bool, 'current_plan': str, 'required_plan': str}
    """
    if not user.is_authenticated:
        return {
            'has_access': False,
            'current_plan': 'None',
            'required_plan': required_plan
        }
    
    # Get user's active subscription
    active_subscription = UserSubscription.objects.filter(
        user=user,
        status='ACTIVE'
    ).select_related('plan').first()
    
    if not active_subscription:
        return {
            'has_access': False,
            'current_plan': 'Free',
            'required_plan': required_plan
        }
    
    current_plan = active_subscription.plan.name
    current_level = PLAN_HIERARCHY.get(current_plan, 0)
    required_level = PLAN_HIERARCHY.get(required_plan, 1)
    
    has_access = current_level >= required_level
    
    # Check specific feature if provided
    if has_access and feature_identifier:
        has_access = active_subscription.has_access_to_feature(feature_identifier)
    
    return {
        'has_access': has_access,
        'current_plan': current_plan,
        'required_plan': required_plan
    } 