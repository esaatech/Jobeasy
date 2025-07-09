from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import SubscriptionPlan, PlanDuration, UserSubscription, UserProfile
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
import stripe
import json
import os
from dotenv import load_dotenv
from django.utils import timezone
load_dotenv()
# Initialize Stripe with SECRET key (not publishable key)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')  # Make sure this is the secret key

class PlanPurchaseView(LoginRequiredMixin, DetailView):
    """
    Generic view to display any subscription plan details and handle purchase.
    Can be used by any app that needs subscription functionality.
    """
    template_name = 'subscriptions/purchase.html'
    model = SubscriptionPlan
    context_object_name = 'plan'
    pk_url_kwarg = 'plan_id'

    def get_queryset(self):
        """Ensure we only get active plans with their durations."""
        return SubscriptionPlan.objects.filter(
            is_active=True
        ).prefetch_related(
            'durations',
            'features'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        
        # Add plan ID to context
        context['plan_id'] = plan.id
        
        # Get active durations for this plan
        context['durations'] = plan.durations.filter(is_active=True)
        
        # Separate features into tools and services
        context['tools'] = plan.features.filter(
            type='TOOL',
            is_active=True
        )
        context['services'] = plan.features.filter(
            type='SERVICE',
            is_active=True
        )
        
        # Load Stripe publishable key directly
        stripe_public_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        if not stripe_public_key:
            # Log warning but don't crash the page
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('STRIPE_PUBLISHABLE_KEY is not configured in environment variables')
        
        context['STRIPE_PUBLIC_KEY'] = stripe_public_key
        
        # Add return_url if provided
        context['return_url'] = self.request.GET.get('return_url')
        
        return context

@login_required
def process_payment(request, plan_id, duration_id):
    """Handle the payment processing and subscription creation."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        # Get data from request
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        save_card = data.get('save_card', False)

        # Get plan and duration first
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        duration = get_object_or_404(PlanDuration, id=duration_id, plan=plan, is_active=True)

        # Create pending subscription
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            plan_duration=duration,
            status='PENDING'
        )

        # Now we can build the success URL with the subscription ID
        success_url = request.build_absolute_uri(
            reverse('subscriptions:checkout_success', args=[subscription.id])
        )

        # Get or create stripe profile
        stripe_profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Create or get Stripe customer
        if not stripe_profile.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                payment_method=payment_method_id if save_card else None,
                metadata={'user_id': request.user.id}
            )
            stripe_profile.stripe_customer_id = customer.id
            stripe_profile.save()
        else:
            customer = stripe.Customer.retrieve(stripe_profile.stripe_customer_id)
            if save_card:
                stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)

        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(duration.price * 100),
            currency='usd',
            customer=customer.id,
            payment_method=payment_method_id,
            off_session=False,
            confirm=True,
            return_url=success_url,
            metadata={
                'subscription_id': subscription.id,
                'plan_id': plan.id,
                'duration_id': duration.id
            }
        )

        # Handle different payment states
        if payment_intent.status == 'succeeded':
            # Create invoice for the subscription
            invoice = stripe.Invoice.create(
                customer=customer.id,
                auto_advance=False,
                collection_method='charge_automatically',
                currency='usd',
                pending_invoice_items_behavior='include',
                metadata={
                    'payment_intent_id': payment_intent.id,
                    'subscription_id': subscription.id
                }
            )

            # Add invoice item
            stripe.InvoiceItem.create(
                customer=customer.id,
                invoice=invoice.id,
                amount=int(duration.price * 100),
                currency='usd',
                description=f"Subscription to {plan.name} - {duration.get_duration_type_display()}"
            )

            # Finalize and pay invoice
            finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)
            paid_invoice = stripe.Invoice.pay(invoice.id, paid_out_of_band=True)

            # Update subscription with invoice details
            subscription.status = 'ACTIVE'
            subscription.stripe_payment_intent = payment_intent.id
            subscription.stripe_invoice_id = paid_invoice.id
            subscription.invoice_url = paid_invoice.hosted_invoice_url
            subscription.save()
            
            return JsonResponse({
                'success': True,
                'redirect_url': success_url
            })
        elif payment_intent.status == 'requires_action':
            # 3D Secure authentication needed
            subscription.status = 'PENDING'
            subscription.save()
            return JsonResponse({
                'requires_action': True,
                'payment_intent_client_secret': payment_intent.client_secret,
                'subscription_id': subscription.id
            })
            
        elif payment_intent.status == 'requires_payment_method':
            # The payment failed - request new payment method
            subscription.status = 'FAILED'
            subscription.save()
            return JsonResponse({
                'success': False,
                'error': 'Your card was declined. Please try a different payment method.'
            }, status=400)
            
        elif payment_intent.status == 'processing':
            # Payment is still processing
            subscription.status = 'PENDING'
            subscription.save()
            return JsonResponse({
                'success': False,
                'error': 'Payment is processing. Please wait a moment and refresh the page.'
            }, status=202)  # 202 Accepted
            
        elif payment_intent.status == 'canceled':
            subscription.status = 'CANCELED'
            subscription.save()
            return JsonResponse({
                'success': False,
                'error': 'Payment was canceled. Please try again.'
            }, status=400)
            
        else:
            # Unknown or unexpected status
            subscription.status = 'FAILED'
            subscription.save()
            return JsonResponse({
                'success': False,
                'error': f'Payment status: {payment_intent.status}. Please contact support.'
            }, status=400)

    except stripe.error.CardError as e:
        if 'subscription' in locals():
            subscription.status = 'FAILED'
            subscription.save()
        return JsonResponse({
            'success': False,
            'error': e.user_message
        }, status=400)

    except Exception as e:
        if 'subscription' in locals():
            subscription.status = 'FAILED'
            subscription.save()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def checkout_success(request, subscription_id):
    """Generic success page for subscription checkout."""
    subscription = get_object_or_404(
        UserSubscription.objects.select_related(
            'plan',
            'plan_duration',
            'user'
        ).prefetch_related(
            'plan__features'
        ),
        id=subscription_id,
        user=request.user
    )

    context = {
        'subscription': subscription,
        'plan': subscription.plan,
        'duration': subscription.plan_duration,
        'features': subscription.plan.features.filter(is_active=True),
        'amount': subscription.plan_duration.price,
        'status': subscription.status,
        # Add any return URLs from your specific implementation
        'dashboard_url': reverse('dashboard:dashboard'),  # Change this line
        'invoice_url': reverse('subscriptions:invoice', args=[subscription.id]) if hasattr(subscription, 'invoice') else None,
        'next_billing_date': subscription.created_at + timezone.timedelta(
            days=30 if subscription.plan_duration.duration_type == 'MONTHLY' else 90
        ) if subscription.plan_duration.duration_type in ['MONTHLY', 'QUARTERLY'] else None
    }

    return render(request, 'subscriptions/success.html', context)

# Create your views here.

def test_subscription_dialogs(request):
    """Test view to demonstrate subscription dialogs"""
    from utils.subscription import get_plus_upgrade_dialog, get_ultimate_upgrade_dialog, get_subscription_javascript
    
    context = {
        'plus_dialog': get_plus_upgrade_dialog(),
        'ultimate_dialog': get_ultimate_upgrade_dialog(),
        'subscription_js': get_subscription_javascript(),
    }
    
    return render(request, 'subscriptions/test_dialogs.html', context)

def pricing(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).prefetch_related('features', 'durations')
    
    # Get user's current subscription if logged in
    current_subscription = None
    if request.user.is_authenticated:
        current_subscription = UserSubscription.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).select_related('plan', 'plan_duration').first()
        
        # If user has no active subscription, they're on the Free plan
        if not current_subscription:
            free_plan = SubscriptionPlan.objects.filter(name='Free', is_active=True).first()
            if free_plan:
                # Create a virtual current subscription for Free plan users
                current_subscription = type('obj', (object,), {
                    'plan': free_plan,
                    'plan_duration': None,
                    'status': 'ACTIVE'
                })()
    
    context = {
        'plans': plans,
        'current_subscription': current_subscription,
    }
    return render(request, 'subscriptions/pricing.html', context)

@login_required
def cancel_subscription(request):
    """Cancel a user's subscription."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        # Get the user's active subscription
        subscription = UserSubscription.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).first()
        
        if not subscription:
            return JsonResponse({
                'success': False,
                'error': 'No active subscription found.'
            }, status=404)
        
        # Cancel the subscription
        subscription.status = 'CANCELED'
        subscription.canceled_at = timezone.now()
        subscription.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Subscription canceled successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
