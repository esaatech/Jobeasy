from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.urls import reverse
from email_utility.services.notification_service import NotificationService
from team.models import Team, TeamMember
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
    member_teams = Team.objects.filter(members__user=user)
    owned_teams = Team.objects.filter(owner=user)
    teams = list(member_teams) + list(owned_teams)
    # Remove duplicates by team id
    unique_teams = {team.id: team for team in teams}.values()
    team_roles = []
    for team in unique_teams:
        if hasattr(team, 'owner') and team.owner == user:
            role = 'Owner'
        else:
            tm = TeamMember.objects.filter(team=team, user=user).first()
            if tm and hasattr(tm, 'get_role_display'):
                role = tm.get_role_display()
            elif tm:
                role = tm.role
            else:
                role = 'Member'
        team_roles.append({'name': team.name, 'role': role})
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
                
                # Handle owned teams
                owned_teams = Team.objects.filter(owner=request.user)
                for team in owned_teams:
                    # Try to find another admin to transfer ownership to
                    new_owner = TeamMember.objects.filter(
                        team=team,
                        role=TeamMember.Roles.ADMIN,
                        is_active=True
                    ).exclude(user=request.user).first()
                    
                    if new_owner:
                        # Transfer ownership
                        team.owner = new_owner.user
                        team.save()
                        new_owner.role = TeamMember.Roles.OWNER
                        new_owner.save()
                    else:
                        # If no admin found, delete the team
                        team.delete()
                
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
    
    # Get the teams owned by the user for display
    owned_teams = Team.objects.filter(owner=request.user)
    return render(request, 'settings/delete_account.html', {
        'active_section': 'security',
        'page_title': 'Delete Account',
        'owned_teams': owned_teams
    })
