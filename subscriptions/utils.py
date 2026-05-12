import stripe
import os
from decimal import Decimal
from django.conf import settings
from .models import PlanDuration


def get_stripe_price_info(plan_duration):
    """
    Fetch current price information from Stripe for a given plan duration.
    Returns the price amount and currency from Stripe, not Django.
    """
    if not plan_duration.stripe_price_id:
        return None, None
    
    try:
        # Fetch price from Stripe
        price = stripe.Price.retrieve(plan_duration.stripe_price_id)
        
        # Convert amount from cents to dollars
        amount = Decimal(price.unit_amount) / 100
        currency = price.currency.upper()
        
        return amount, currency
    except stripe.error.StripeError as e:
        print(f"Error fetching Stripe price: {e}")
        # Fallback to Django price and configured billing currency
        fallback_cur = getattr(
            settings, 'STRIPE_BILLING_CURRENCY', 'usd'
        ).upper()
        return plan_duration.price, fallback_cur


def get_plan_durations_with_stripe_prices(plan, request=None):
    """
    Get all durations for a plan with their current Stripe prices.
    Returns a list of durations with added stripe_price and stripe_currency fields.
    """
    durations = []
    
    for duration in plan.durations.filter(is_active=True):
        stripe_amount, stripe_currency = get_stripe_price_info(duration)
        
        # Add Stripe price info to the duration object
        duration.stripe_price = stripe_amount
        duration.stripe_currency = stripe_currency
        duration.has_stripe_price = stripe_amount is not None

        from .pricing_display import attach_price_display

        attach_price_display(duration, request)

        durations.append(duration)

    _DURATION_UI_ORDER = {
        'WEEKLY': 0,
        'MONTHLY': 1,
        'QUARTERLY': 2,
        'SEMI_ANNUAL': 3,
        'YEARLY': 4,
        'ONE_TIME': 5,
    }
    durations.sort(key=lambda d: _DURATION_UI_ORDER.get(d.duration_type, 99))

    return durations


def get_all_plans_with_stripe_prices(request=None):
    """
    Get all active plans with their current Stripe prices.
    Returns a list of plans with durations that have Stripe prices.
    """
    from .models import SubscriptionPlan
    
    plans = []
    
    plans_qs = SubscriptionPlan.objects.filter(is_active=True)
    if not settings.DEBUG:
        plans_qs = plans_qs.exclude(name__in=['Test'])

    for plan in plans_qs.prefetch_related('durations'):
        plan.durations_with_stripe = get_plan_durations_with_stripe_prices(plan, request)
        plans.append(plan)
    
    return plans


def sync_prices_from_stripe():
    """
    Sync all plan duration prices from Stripe to Django.
    This ensures Django prices match Stripe prices.
    """
    updated_count = 0
    
    for duration in PlanDuration.objects.filter(stripe_price_id__isnull=False):
        stripe_amount, currency = get_stripe_price_info(duration)
        
        if stripe_amount and stripe_amount != duration.price:
            duration.price = stripe_amount
            duration.save()
            updated_count += 1
            print(f"Updated {duration.plan.name} {duration.duration_type}: ${duration.price}")
    
    return updated_count


def get_current_pricing_context():
    """
    Get current pricing information for all plans.
    Returns data that can be used in templates.
    """
    pricing_data = {}
    
    for duration in PlanDuration.objects.filter(stripe_price_id__isnull=False):
        stripe_amount, currency = get_stripe_price_info(duration)
        
        if stripe_amount:
            plan_name = duration.plan.name
            if plan_name not in pricing_data:
                pricing_data[plan_name] = {}
            
            pricing_data[plan_name][duration.duration_type.lower()] = {
                'price': stripe_amount,
                'currency': currency,
                'stripe_price_id': duration.stripe_price_id,
                'is_stripe_price': True
            }
    
    return pricing_data 