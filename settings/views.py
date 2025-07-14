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

# Create your views here.

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
    context = {
        'active_section': 'integrations',
        'page_title': 'Platform Integrations'
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/integrations_content.html', context)
    
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
    context = {
        'active_section': 'billing',
        'page_title': 'Billing & Subscription',
        'current_subscription': current_subscription,
    }
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/billing_content.html', context)
    return render(request, 'settings/settings.html', context)

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
