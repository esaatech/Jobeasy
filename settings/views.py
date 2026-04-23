from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, logout, update_session_auth_hash
from django.urls import reverse
from email_utility.services.notification_service import NotificationService
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.utils import timezone
import os
import stripe

# Create your views here.
stripe.api_key = os.getenv('MYAPP_STRIPE_SECRET_KEY')


def _get_or_create_stripe_customer_for_user(user):
    from subscriptions.models import UserProfile

    stripe_profile, _ = UserProfile.objects.get_or_create(user=user)
    if not stripe_profile.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={'user_id': user.id}
        )
        stripe_profile.stripe_customer_id = customer.id
        stripe_profile.save(update_fields=['stripe_customer_id'])
    return stripe_profile.stripe_customer_id

@login_required
def settings_root(request):
    # Redirect root settings to profile
    return HttpResponseRedirect(reverse('settings:profile'))

@login_required
def profile_settings(request):
    user = request.user
    # Team functionality removed
    team_roles = []
    context = {
        'active_section': 'profile',
        'page_title': 'Profile Settings',
        'user': user,
        'teams': team_roles,
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/profile_content.html', context)
    
    return render(request, 'settings/settings.html', context)

@login_required
def notification_settings(request):
    context = {
        'active_section': 'notifications',
        'page_title': 'Notification Preferences'
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/notifications_content.html', context)
    
    return render(request, 'settings/settings.html', context)

@login_required
def integration_settings(request):
    # Get Gmail connection status
    from email_utility.services.gmail_service import GmailService
    from email_utility.services.yahoo_service import YahooService
    from email_utility.models import SMTPAccount
    gmail_service = GmailService(request.user)
    gmail_connected = gmail_service.is_authenticated()
    gmail_address = gmail_service.gmail_auth.gmail_address if gmail_connected else None
    yahoo_service = YahooService(request.user)
    yahoo_connected = yahoo_service.is_authenticated()
    yahoo_address = yahoo_service.yahoo_auth.yahoo_address if yahoo_connected else None
    yahoo_sending_account = SMTPAccount.objects.filter(
        user=request.user,
        is_active=True,
        provider=SMTPAccount.PROVIDER_YAHOO,
    ).order_by('-updated_at').first()
    outlook_smtp_accounts = SMTPAccount.objects.filter(
        user=request.user,
        is_active=True,
        provider=SMTPAccount.PROVIDER_OUTLOOK,
    ).order_by('-is_default', '-updated_at')
    
    context = {
        'active_section': 'integrations',
        'page_title': 'Platform Integrations',
        'gmail_connected': gmail_connected,
        'gmail_address': gmail_address,
        'yahoo_connected': yahoo_connected,
        'yahoo_address': yahoo_address,
        'yahoo_sending_connected': bool(yahoo_sending_account),
        'yahoo_sending_account': yahoo_sending_account,
        'smtp_accounts': outlook_smtp_accounts,
        'has_connected_email': gmail_connected or bool(yahoo_sending_account) or outlook_smtp_accounts.exists(),
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/integrations_content.html', context)
    
    return render(request, 'settings/settings.html', context)


@login_required
def gmail_settings(request):
    # Get Gmail connection status
    from email_utility.services.gmail_service import GmailService
    gmail_service = GmailService(request.user)
    gmail_connected = gmail_service.is_authenticated()
    gmail_address = gmail_service.gmail_auth.gmail_address if gmail_connected else None
    
    context = {
        'active_section': 'integrations',
        'page_title': 'Gmail Settings',
        'gmail_connected': gmail_connected,
        'gmail_address': gmail_address,
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/gmail_settings_content.html', context)
    
    return render(request, 'settings/settings.html', context)

@login_required
def billing_settings(request):
    # Get user's current subscription (active)
    from subscriptions.models import UserSubscription, SubscriptionPlan
    current_subscription = None
    if request.user.is_authenticated:
        current_subscription = UserSubscription.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).select_related('plan', 'plan_duration').first()
        if not current_subscription:
            free_plan = SubscriptionPlan.objects.filter(name='Free', is_active=True).first()
            if free_plan:
                current_subscription = type('obj', (object,), {
                    'plan': free_plan,
                    'plan_duration': None,
                    'status': 'ACTIVE'
                })()
    has_payment_method = False
    default_payment_method = None
    payment_method_error = None
    billing_invoices = []
    auto_renewal_enabled = None
    can_manage_subscription = False
    billing_history_error = None

    # Load saved payment method data from Stripe when available.
    try:
        from subscriptions.models import UserProfile

        stripe_profile = UserProfile.objects.filter(user=request.user).first()
        if stripe_profile and stripe_profile.stripe_customer_id and stripe.api_key:
            customer = stripe.Customer.retrieve(stripe_profile.stripe_customer_id)
            default_payment_method_id = None

            if getattr(customer, 'invoice_settings', None):
                default_payment_method_id = customer.invoice_settings.get('default_payment_method')

            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_profile.stripe_customer_id,
                type='card',
                limit=10
            ).data

            selected_payment_method = None
            if default_payment_method_id:
                selected_payment_method = next(
                    (pm for pm in payment_methods if pm.id == default_payment_method_id),
                    None
                )
                if not selected_payment_method:
                    selected_payment_method = stripe.PaymentMethod.retrieve(default_payment_method_id)
            elif payment_methods:
                selected_payment_method = payment_methods[0]

            if selected_payment_method and getattr(selected_payment_method, 'card', None):
                has_payment_method = True
                brand = (selected_payment_method.card.brand or 'card').title()
                default_payment_method = {
                    'brand': brand,
                    'last4': selected_payment_method.card.last4,
                    'exp_month': selected_payment_method.card.exp_month,
                    'exp_year': selected_payment_method.card.exp_year,
                }

            # Billing history from Stripe invoices.
            invoices = stripe.Invoice.list(customer=stripe_profile.stripe_customer_id, limit=10).data
            for invoice in invoices:
                billing_invoices.append({
                    'number': invoice.number or invoice.id,
                    'status': (invoice.status or 'unknown').replace('_', ' ').title(),
                    'amount_paid': (invoice.amount_paid or 0) / 100,
                    'currency': (invoice.currency or 'usd').upper(),
                    'hosted_invoice_url': invoice.hosted_invoice_url,
                    'invoice_pdf': invoice.invoice_pdf,
                    'created': timezone.datetime.fromtimestamp(invoice.created, tz=timezone.utc)
                    if getattr(invoice, 'created', None) else None,
                })
    except stripe.error.StripeError:
        payment_method_error = 'Unable to load payment method details from Stripe right now.'
        billing_history_error = 'Unable to load billing history from Stripe right now.'
    except Exception:
        payment_method_error = 'Unable to load payment method details right now.'
        billing_history_error = 'Unable to load billing history right now.'

    # Auto-renewal state for active paid subscriptions.
    try:
        stripe_subscription_id = getattr(current_subscription, 'stripe_subscription_id', None)
        if stripe_subscription_id and stripe.api_key:
            can_manage_subscription = True
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            auto_renewal_enabled = not bool(getattr(stripe_subscription, 'cancel_at_period_end', False))
    except stripe.error.StripeError:
        can_manage_subscription = False
    except Exception:
        can_manage_subscription = False

    context = {
        'active_section': 'billing',
        'page_title': 'Billing & Subscription',
        'current_subscription': current_subscription,
        'has_payment_method': has_payment_method,
        'default_payment_method': default_payment_method,
        'payment_method_error': payment_method_error,
        'billing_invoices': billing_invoices,
        'billing_history_error': billing_history_error,
        'auto_renewal_enabled': auto_renewal_enabled,
        'can_manage_subscription': can_manage_subscription,
    }
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/billing_content.html', context)
    return render(request, 'settings/settings.html', context)

@login_required
def add_payment_method(request):
    """
    Redirect user to Stripe Billing Portal so they can add/update payment methods.
    """
    if not stripe.api_key:
        messages.error(request, 'Stripe is not configured. Please contact support.')
        return redirect('settings:billing')

    try:
        stripe_customer_id = _get_or_create_stripe_customer_for_user(request.user)

        return_url = request.build_absolute_uri(reverse('settings:billing'))
        portal_session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )

        return redirect(portal_session.url)
    except stripe.error.StripeError as exc:
        messages.error(request, f'Unable to open billing portal: {exc.user_message or str(exc)}')
        return redirect('settings:billing')
    except Exception:
        messages.error(request, 'Unable to open billing portal right now. Please try again.')
        return redirect('settings:billing')


@login_required
def download_invoices(request):
    """
    Redirect to Stripe Billing Portal invoice history/download section.
    """
    return add_payment_method(request)


@login_required
@require_POST
def update_auto_renewal(request):
    from subscriptions.models import UserSubscription

    if not stripe.api_key:
        messages.error(request, 'Stripe is not configured. Please contact support.')
        return redirect('settings:billing')

    subscription = UserSubscription.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).exclude(stripe_subscription_id__isnull=True).exclude(stripe_subscription_id='').first()

    if not subscription:
        messages.error(request, 'No active Stripe subscription found for this account.')
        return redirect('settings:billing')

    enable_auto_renewal = request.POST.get('auto_renewal') == 'on'

    try:
        stripe_subscription = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=not enable_auto_renewal,
        )
        if not enable_auto_renewal and getattr(stripe_subscription, 'current_period_end', None):
            subscription.end_date = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            )
            subscription.save(update_fields=['end_date', 'updated_at'])
        elif enable_auto_renewal and subscription.end_date:
            subscription.end_date = None
            subscription.save(update_fields=['end_date', 'updated_at'])

        messages.success(
            request,
            'Auto-renewal enabled.' if enable_auto_renewal else 'Auto-renewal disabled. Subscription will end at period close.'
        )
    except stripe.error.StripeError as exc:
        messages.error(request, f'Unable to update auto-renewal: {exc.user_message or str(exc)}')
    except Exception:
        messages.error(request, 'Unable to update auto-renewal right now. Please try again.')

    return redirect('settings:billing')


@login_required
@require_POST
def cancel_subscription(request):
    from subscriptions.models import UserSubscription

    if not stripe.api_key:
        messages.error(request, 'Stripe is not configured. Please contact support.')
        return redirect('settings:billing')

    subscription = UserSubscription.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).exclude(stripe_subscription_id__isnull=True).exclude(stripe_subscription_id='').first()

    if not subscription:
        messages.error(request, 'No active Stripe subscription found for this account.')
        return redirect('settings:billing')

    try:
        stripe_subscription = stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        if getattr(stripe_subscription, 'current_period_end', None):
            subscription.end_date = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            )
            subscription.save(update_fields=['end_date', 'updated_at'])
        messages.success(request, 'Subscription cancellation scheduled for end of current billing period.')
    except stripe.error.StripeError as exc:
        messages.error(request, f'Unable to cancel subscription: {exc.user_message or str(exc)}')
    except Exception:
        messages.error(request, 'Unable to cancel subscription right now. Please try again.')

    return redirect('settings:billing')

@login_required
def security_settings(request):
    context = {
        'active_section': 'security',
        'page_title': 'Security Settings'
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/security_content.html', context)
    
    return render(request, 'settings/settings.html', context)

@login_required
def delete_account(request):
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation')
        password = request.POST.get('password')
        
        # Verify confirmation text
        if confirmation != 'DELETE':
            messages.error(request, 'Please type DELETE to confirm account deletion.')
            return redirect('settings:delete_account')
        
        # Verify password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            messages.error(request, 'Incorrect password. Please try again.')
            return redirect('settings:delete_account')
        
        try:
            with transaction.atomic():
                # Store user info for email
                user_email = request.user.email
                user_name = request.user.get_full_name() or user_email
                # Team functionality removed
                # Delete the user account
                request.user.delete()
                # Only send email after successful deletion
                NotificationService.send_account_deletion_notification(
                    user_email=user_email,
                    user_name=user_name
                )
                # Log the user out
                logout(request)
                messages.success(request, 'Your account has been successfully deleted.')
                return redirect('authentication:login')
        except Exception as e:
            messages.error(request, f'An error occurred while deleting your account: {str(e)}')
            return redirect('settings:delete_account')
    # Team functionality removed
    owned_teams = []
    return render(request, 'settings/delete_account.html', {
        'active_section': 'security',
        'page_title': 'Delete Account',
        'owned_teams': owned_teams
    })

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email']

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user)
        password_form = PasswordChangeForm(user, request.POST)
        try:
            # Validate username/email
            if not form.is_valid():
                # Unique username/email error or other validation
                error_msg = form.errors.as_text().replace('* ', '').replace('\n', '<br>')
                return render(request, 'settings/partials/edit_profile_form.html', {
                    'form': form,
                    'password_form': password_form,
                    'active_section': 'profile',
                    'page_title': 'Edit Profile',
                    'user': user,
                    'alert_error': error_msg,
                })
            # Validate password only if user is changing it
            if request.POST.get('new_password1'):
                if not password_form.is_valid():
                    error_msg = password_form.errors.as_text().replace('* ', '').replace('\n', '<br>')
                    return render(request, 'settings/partials/edit_profile_form.html', {
                        'form': form,
                        'password_form': password_form,
                        'active_section': 'profile',
                        'page_title': 'Edit Profile',
                        'user': user,
                        'alert_error': error_msg,
                    })
            # Save profile
            try:
                form.save()
            except IntegrityError:
                error_msg = 'This username or email is already taken.'
                return render(request, 'settings/partials/edit_profile_form.html', {
                    'form': form,
                    'password_form': password_form,
                    'active_section': 'profile',
                    'page_title': 'Edit Profile',
                    'user': user,
                    'alert_error': error_msg,
                })
            # Save password if changed
            if request.POST.get('new_password1'):
                user = password_form.save()
                update_session_auth_hash(request, user)
            # Success: return updated profile
            context = {
                'active_section': 'profile',
                'page_title': 'Profile Settings',
                'user': user,
                'teams': [],
            }
            return render(request, 'settings/partials/profile_content.html', context)
        except ValidationError as e:
            error_msg = str(e)
            return render(request, 'settings/partials/edit_profile_form.html', {
                'form': form,
                'password_form': password_form,
                'active_section': 'profile',
                'page_title': 'Edit Profile',
                'user': user,
                'alert_error': error_msg,
            })
    else:
        form = EditProfileForm(instance=user)
        password_form = PasswordChangeForm(user)
    context = {
        'form': form,
        'password_form': password_form,
        'active_section': 'profile',
        'page_title': 'Edit Profile',
        'user': user,
    }
    return render(request, 'settings/partials/edit_profile_form.html', context)
