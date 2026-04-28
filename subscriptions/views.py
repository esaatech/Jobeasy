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
import os
print('DEBUG: STRIPE_SECRET_KEY at runtime:', os.getenv('MYAPP_STRIPE_SECRET_KEY'))
stripe.api_key = os.getenv('MYAPP_STRIPE_SECRET_KEY')  # Use MYAPP_ prefix for live mode
from .utils import get_all_plans_with_stripe_prices, get_stripe_price_info
from email_utility.services.notification_service import NotificationService

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
        queryset = SubscriptionPlan.objects.filter(is_active=True)
        if not settings.DEBUG:
            queryset = queryset.exclude(name__in=['Test', 'Ultimate'])
        return queryset.prefetch_related(
            'durations',
            'features'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        
        # Add plan ID to context
        context['plan_id'] = plan.id
        
        # Get active durations with Stripe prices for this plan
        from .utils import get_plan_durations_with_stripe_prices

        context['durations'] = get_plan_durations_with_stripe_prices(plan, self.request)
        context['billing_currency'] = getattr(
            settings, 'STRIPE_BILLING_CURRENCY', 'mxn'
        ).upper()
        if context['durations']:
            sc = getattr(context['durations'][0], 'stripe_currency', None)
            if sc:
                context['billing_currency'] = sc.upper()
        
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
        stripe_public_key = os.getenv('MYAPP_STRIPE_PUBLISHABLE_KEY')
        if not stripe_public_key:
            # Log warning but don't crash the page
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('MYAPP_STRIPE_PUBLISHABLE_KEY is not configured in environment variables')
        
        context['STRIPE_PUBLIC_KEY'] = stripe_public_key
        
        # Add return_url if provided
        context['return_url'] = self.request.GET.get('return_url')
        
        return context

@login_required
def process_payment(request, plan_id, duration_id):
    """Handle the payment processing and subscription creation."""
    print("DEBUG: process_payment started")
    
    if request.method != 'POST':
        print("DEBUG: Invalid request method")
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        print("DEBUG: Parsing request data")
        # Get data from request
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        save_card = data.get('save_card', True)  # Default to True for subscriptions
        frontend_stripe_price_id = data.get('stripe_price_id')  # Get from frontend

        print(f"DEBUG: payment_method_id: {payment_method_id}")
        print(f"DEBUG: save_card: {save_card}")
        print(f"DEBUG: frontend_stripe_price_id: {frontend_stripe_price_id}")

        # For subscriptions, we always need to save the card for renewals
        if not save_card:
            print("DEBUG: Card must be saved for subscriptions")
            return JsonResponse({
                'success': False,
                'error': 'Card must be saved for subscription renewals.'
            }, status=400)

        print("DEBUG: Getting plan and duration")
        # Get plan and duration first
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        if plan.name in ['Test', 'Ultimate'] and not settings.DEBUG:
            return JsonResponse({
                'success': False,
                'error': 'This plan is not available in production.'
            }, status=403)
        duration = get_object_or_404(PlanDuration, id=duration_id, plan=plan, is_active=True)

        print(f"DEBUG: Plan: {plan.name}, Duration: {duration.duration_type}")
        print(f"DEBUG: Duration stripe_price_id: {duration.stripe_price_id}")

        # Validate that we have a Stripe Price ID
        if not duration.stripe_price_id:
            print("DEBUG: No stripe_price_id found")
            return JsonResponse({
                'success': False,
                'error': 'Pricing configuration error. Please contact support.'
            }, status=400)

        # Validate that frontend and backend Price IDs match
        if frontend_stripe_price_id and frontend_stripe_price_id != duration.stripe_price_id:
            print(f"DEBUG: Price mismatch - frontend: {frontend_stripe_price_id}, backend: {duration.stripe_price_id}")
            return JsonResponse({
                'success': False,
                'error': 'Price mismatch detected. Please refresh the page and try again.'
            }, status=400)

        print("DEBUG: Creating pending subscription")
        # Create pending subscription
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            plan_duration=duration,
            status='PENDING'
        )
        print(f"DEBUG: Created subscription ID: {subscription.id}")

        # Now we can build the success URL with the subscription ID
        success_url = request.build_absolute_uri(
            reverse('subscriptions:checkout_success', args=[subscription.id])
        )
        print(f"DEBUG: Success URL: {success_url}")

        print("DEBUG: Getting or creating stripe profile")
        # Get or create stripe profile
        stripe_profile, created = UserProfile.objects.get_or_create(user=request.user)
        print(f"DEBUG: Stripe profile - created: {created}, customer_id: {stripe_profile.stripe_customer_id}")

        # Create or get Stripe customer
        if not stripe_profile.stripe_customer_id:
            print("DEBUG: Creating new Stripe customer")
            customer = stripe.Customer.create(
                email=request.user.email,
                payment_method=payment_method_id if save_card else None,
                metadata={'user_id': request.user.id}
            )
            stripe_profile.stripe_customer_id = customer.id
            stripe_profile.save()
            print(f"DEBUG: Created Stripe customer: {customer.id}")
        else:
            print("DEBUG: Retrieving existing Stripe customer")
            customer = stripe.Customer.retrieve(stripe_profile.stripe_customer_id)
            if save_card:
                print("DEBUG: Attaching payment method to customer")
                stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
            print(f"DEBUG: Retrieved Stripe customer: {customer.id}")

        print("DEBUG: Creating Stripe subscription")
        # Create Stripe Subscription for recurring billing
        try:
            # Create a Stripe Subscription for recurring billing
            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': duration.stripe_price_id}],  # Use Price ID for recurring billing
                payment_behavior='default_incomplete',  # Don't charge until payment is confirmed
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'subscription_id': subscription.id,
                    'plan_id': plan.id,
                    'duration_id': duration.id,
                    'stripe_price_id': duration.stripe_price_id
                }
            )
            
            print(f"DEBUG: Stripe subscription created: {stripe_subscription.id}")
            print(f"DEBUG: Subscription status: {stripe_subscription.status}")
            
            # For incomplete subscriptions, we need to handle the payment confirmation
            if stripe_subscription.status == 'incomplete':
                print("DEBUG: Subscription is incomplete, checking for payment intent")
                
                # Check if there's a payment intent on the latest invoice
                if hasattr(stripe_subscription.latest_invoice, 'payment_intent') and stripe_subscription.latest_invoice.payment_intent:
                    payment_intent = stripe_subscription.latest_invoice.payment_intent
                    print(f"DEBUG: Found payment intent: {payment_intent.id}, status: {payment_intent.status}")
                else:
                    print("DEBUG: No payment intent found, creating one")
                    # Create a payment intent for the subscription
                    payment_intent = stripe.PaymentIntent.create(
                        amount=stripe_subscription.latest_invoice.amount_due,
                        currency=stripe_subscription.latest_invoice.currency,
                        customer=customer.id,
                        payment_method=payment_method_id,
                        confirm=True,
                        return_url=success_url,
                        metadata={
                            'subscription_id': subscription.id,
                            'stripe_subscription_id': stripe_subscription.id
                        }
                    )
                    print(f"DEBUG: Created payment intent: {payment_intent.id}, status: {payment_intent.status}")
            elif stripe_subscription.status == 'active':
                # Subscription is already active (payment was successful)
                payment_intent = None
                print("DEBUG: Subscription is already active - payment was successful")
                
                # Update our subscription with Stripe subscription details
                subscription.status = 'ACTIVE'
                subscription.stripe_subscription_id = stripe_subscription.id
                subscription.stripe_invoice_id = stripe_subscription.latest_invoice.id
                subscription.invoice_url = stripe_subscription.latest_invoice.hosted_invoice_url
                
                # Handle subscription period data safely
                try:
                    if hasattr(stripe_subscription, 'current_period_start') and stripe_subscription.current_period_start:
                        subscription.current_period_start = timezone.datetime.fromtimestamp(
                            stripe_subscription.current_period_start, tz=timezone.utc
                        )
                        print(f"DEBUG: Set current_period_start: {subscription.current_period_start}")
                    else:
                        subscription.current_period_start = timezone.now()
                        print("DEBUG: Using current time for period start")
                    
                    if hasattr(stripe_subscription, 'current_period_end') and stripe_subscription.current_period_end:
                        subscription.current_period_end = timezone.datetime.fromtimestamp(
                            stripe_subscription.current_period_end, tz=timezone.utc
                        )
                        print(f"DEBUG: Set current_period_end: {subscription.current_period_end}")
                    else:
                        # Calculate period end based on duration
                        if duration.duration_type == 'MONTHLY':
                            subscription.current_period_end = subscription.current_period_start + timezone.timedelta(days=30)
                        else:  # YEARLY
                            subscription.current_period_end = subscription.current_period_start + timezone.timedelta(days=365)
                        print(f"DEBUG: Calculated current_period_end: {subscription.current_period_end}")
                        
                except Exception as period_error:
                    print(f"DEBUG: Error setting period data: {period_error}")
                    # Use fallback period calculation
                    subscription.current_period_start = timezone.now()
                    if duration.duration_type == 'MONTHLY':
                        subscription.current_period_end = timezone.now() + timezone.timedelta(days=30)
                    else:  # YEARLY
                        subscription.current_period_end = timezone.now() + timezone.timedelta(days=365)
                    print("DEBUG: Used fallback period calculation")
                
                subscription.save()
                print("DEBUG: Subscription updated and saved for active status")

                # Send subscription confirmation email
                try:
                    NotificationService.send_subscription_confirmation(subscription)
                    print("DEBUG: Subscription confirmation email sent successfully")
                except Exception as e:
                    print(f"DEBUG: Failed to send subscription confirmation email: {str(e)}")
                    # Don't fail the payment if email fails

                return JsonResponse({
                    'success': True,
                    'subscription_id': subscription.id,
                    'redirect_url': success_url
                })
            else:
                # Subscription is already active
                payment_intent = None
                print("DEBUG: Subscription is already active")
        except stripe.error.InvalidRequestError as e:
            print(f"DEBUG: InvalidRequestError: {e}")
            # If Price ID approach fails, fallback to manual amount
            stripe_amount, currency = get_stripe_price_info(duration)
            if not stripe_amount:
                print("DEBUG: Could not get stripe amount")
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to fetch current pricing. Please try again.'
                }, status=400)
            
            print(f"DEBUG: Fallback - amount: {stripe_amount}, currency: {currency}")
            # Fallback: Create subscription with manual amount
            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    'price_data': {
                        'unit_amount': int(stripe_amount * 100),
                        'currency': currency.lower(),
                        'recurring': {
                            'interval': 'month' if duration.duration_type == 'MONTHLY' else 'year'
                        },
                        'product': 'prod_SegXaYLN4lwmr7'  # Your product ID
                    }
                }],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'subscription_id': subscription.id,
                    'plan_id': plan.id,
                    'duration_id': duration.id,
                    'stripe_price_id': duration.stripe_price_id
                }
            )
            
            # Handle fallback subscription the same way
            if stripe_subscription.status == 'incomplete':
                if hasattr(stripe_subscription.latest_invoice, 'payment_intent') and stripe_subscription.latest_invoice.payment_intent:
                    payment_intent = stripe_subscription.latest_invoice.payment_intent
                else:
                    payment_intent = stripe.PaymentIntent.create(
                        amount=stripe_subscription.latest_invoice.amount_due,
                        currency=stripe_subscription.latest_invoice.currency,
                        customer=customer.id,
                        payment_method=payment_method_id,
                        confirm=True,
                        return_url=success_url,
                        metadata={
                            'subscription_id': subscription.id,
                            'stripe_subscription_id': stripe_subscription.id
                        }
                    )
            else:
                payment_intent = None
            
            print(f"DEBUG: Fallback subscription created {stripe_subscription.id}, payment_intent status: {payment_intent.status if payment_intent else 'None'}")

        print("DEBUG: Handling payment states")
        # Handle different payment states
        if payment_intent and payment_intent.status == 'succeeded':
            print("DEBUG: Payment succeeded")
            
            # Update our subscription with Stripe subscription details
            subscription.status = 'ACTIVE'
            subscription.stripe_subscription_id = stripe_subscription.id  # Save Stripe subscription ID
            subscription.stripe_payment_intent = payment_intent.id
            subscription.stripe_invoice_id = stripe_subscription.latest_invoice.id
            subscription.invoice_url = stripe_subscription.latest_invoice.hosted_invoice_url
            
            # Handle subscription period data safely
            try:
                if hasattr(stripe_subscription, 'current_period_start') and stripe_subscription.current_period_start:
                    subscription.current_period_start = timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_start, tz=timezone.utc
                    )
                    print(f"DEBUG: Set current_period_start: {subscription.current_period_start}")
                else:
                    # If no period start, use current time
                    subscription.current_period_start = timezone.now()
                    print("DEBUG: Using current time for period start")
                
                if hasattr(stripe_subscription, 'current_period_end') and stripe_subscription.current_period_end:
                    subscription.current_period_end = timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end, tz=timezone.utc
                    )
                    print(f"DEBUG: Set current_period_end: {subscription.current_period_end}")
                else:
                    # Calculate period end based on duration
                    if duration.duration_type == 'MONTHLY':
                        subscription.current_period_end = subscription.current_period_start + timezone.timedelta(days=30)
                    else:  # YEARLY
                        subscription.current_period_end = subscription.current_period_start + timezone.timedelta(days=365)
                    print(f"DEBUG: Calculated current_period_end: {subscription.current_period_end}")
                    
            except Exception as period_error:
                print(f"DEBUG: Error setting period data: {period_error}")
                # Use fallback period calculation
                subscription.current_period_start = timezone.now()
                if duration.duration_type == 'MONTHLY':
                    subscription.current_period_end = timezone.now() + timezone.timedelta(days=30)
                else:  # YEARLY
                    subscription.current_period_end = timezone.now() + timezone.timedelta(days=365)
                print("DEBUG: Used fallback period calculation")
            
            subscription.save()
            print("DEBUG: Subscription updated and saved")

            # Send subscription confirmation email
            try:
                NotificationService.send_subscription_confirmation(subscription)
                print("DEBUG: Subscription confirmation email sent successfully")
            except Exception as e:
                print(f"DEBUG: Failed to send subscription confirmation email: {str(e)}")
                # Don't fail the payment if email fails

            return JsonResponse({
                'success': True,
                'subscription_id': subscription.id,
                'redirect_url': success_url
            })

        elif payment_intent and payment_intent.status == 'requires_action':
            print("DEBUG: Payment requires action")
            # Handle 3D Secure or other authentication
            return JsonResponse({
                'success': False,
                'requires_action': True,
                'payment_intent_client_secret': payment_intent.client_secret
            })

        elif payment_intent and payment_intent.status == 'requires_payment_method':
            print("DEBUG: Payment method declined")
            # Payment method was declined
            subscription.status = 'CANCELLED'
            subscription.save()
            
            return JsonResponse({
                'success': False,
                'error': 'Payment method was declined. Please try a different card.'
            }, status=400)

        else:
            print(f"DEBUG: Payment failed - status: {payment_intent.status if payment_intent else 'None'}")
            # Payment failed or unknown status
            subscription.status = 'CANCELLED'
            subscription.save()
            
            error_message = f'Payment failed: {payment_intent.status if payment_intent else "No payment intent"}'
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)

    except stripe.error.CardError as e:
        print(f"DEBUG: CardError: {e}")
        # Card was declined
        return JsonResponse({
            'success': False,
            'error': f'Card error: {e.error.message}'
        }, status=400)
    except stripe.error.InvalidRequestError as e:
        print(f"DEBUG: InvalidRequestError: {e}")
        # Invalid parameters were supplied to Stripe's API
        return JsonResponse({
            'success': False,
            'error': f'Invalid request: {e.error.message}'
        }, status=400)
    except stripe.error.AuthenticationError as e:
        print(f"DEBUG: AuthenticationError: {e}")
        # Authentication with Stripe's API failed
        return JsonResponse({
            'success': False,
            'error': f'Authentication error: {e.error.message}'
        }, status=400)
    except stripe.error.APIConnectionError as e:
        print(f"DEBUG: APIConnectionError: {e}")
        # Network communication with Stripe failed
        return JsonResponse({
            'success': False,
            'error': f'Network error: {e.error.message}'
        }, status=400)
    except stripe.error.StripeError as e:
        print(f"DEBUG: StripeError: {e}")
        # Generic error, something else happened
        return JsonResponse({
            'success': False,
            'error': f'Stripe error: {e.error.message}'
        }, status=400)
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        # Something else happened, completely unrelated to Stripe
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)

@login_required
def checkout_success(request, subscription_id):
    """Handle successful checkout and subscription activation."""
    try:
        subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
        
        # Get return URL from subscription metadata or use default
        return_url = request.GET.get('return_url') or reverse('subscriptions:pricing')
        
        context = {
            'subscription': subscription,
            'return_url': return_url,
        }
        
        return render(request, 'subscriptions/success.html', context)
        
    except Exception as e:
        # Log the error and show a generic success page
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in checkout_success: {str(e)}')
        
        return render(request, 'subscriptions/success.html', {
            'subscription': None,
            'return_url': reverse('subscriptions:pricing'),
            'error': 'There was an issue processing your subscription, but your payment was successful. Please contact support.'
        })

def pricing(request):
    # Get plans with real-time Stripe prices
    plans = get_all_plans_with_stripe_prices(request)
    
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

def get_subscription_dialog_data(request):
    """API endpoint to get subscription dialog data for frontend"""
    try:
        # Get Plus and Ultimate plans with their features
        plus_plan = SubscriptionPlan.objects.filter(
            name='Plus', 
            is_active=True
        ).prefetch_related('features').first()
        
        ultimate_plan = None
        if settings.DEBUG:
            ultimate_plan = SubscriptionPlan.objects.filter(
                name='Ultimate',
                is_active=True
            ).prefetch_related('features').first()
        
        dialog_data = {}
        
        if plus_plan:
            dialog_data['plus'] = {
                'title': f"Upgrade to {plus_plan.name}",
                'message': f"This feature is available with our {plus_plan.name} plan. Upgrade to unlock premium features and enhance your experience.",
                'features': list(plus_plan.features.filter(is_active=True).values_list('name', flat=True)),
                'upgrade_url': f"/subscriptions/pricing/?plan={plus_plan.name.lower()}"
            }
        
        if ultimate_plan:
            dialog_data['ultimate'] = {
                'title': f"Upgrade to {ultimate_plan.name}",
                'message': f"Advanced features and AI-powered tools are available with our {ultimate_plan.name} plan. Get the best tools for your success.",
                'features': list(ultimate_plan.features.filter(is_active=True).values_list('name', flat=True)),
                'upgrade_url': f"/subscriptions/pricing/?plan={ultimate_plan.name.lower()}"
            }
        
        return JsonResponse({
            'success': True,
            'dialog_data': dialog_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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
