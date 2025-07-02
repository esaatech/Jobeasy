from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.urls import reverse
from email_utility.services.notification_service import NotificationService
from django.db import transaction

# Create your views here.

@login_required
def settings_dashboard(request):
    context = {
        'active_section': 'dashboard',
        'page_title': 'Settings Dashboard'
    }
    return render(request, 'settings/dashboard.html', context)

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
    return render(request, 'settings/profile.html', context)

@login_required
def notification_settings(request):
    context = {
        'active_section': 'notifications',
        'page_title': 'Notification Preferences'
    }
    return render(request, 'settings/notifications.html', context)

@login_required
def integration_settings(request):
    context = {
        'active_section': 'integrations',
        'page_title': 'Platform Integrations'
    }
    return render(request, 'settings/integrations.html', context)

@login_required
def billing_settings(request):
    context = {
        'active_section': 'billing',
        'page_title': 'Billing & Subscription'
    }
    return render(request, 'settings/billing.html', context)

@login_required
def security_settings(request):
    context = {
        'active_section': 'security',
        'page_title': 'Security Settings'
    }
    return render(request, 'settings/security.html', context)

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
