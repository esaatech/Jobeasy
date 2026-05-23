from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from typing import List, Optional
import os

class NotificationService:
    """
    A simplified service for sending internal application emails like:
    - Welcome emails
    - Team invitations
    - Password reset
    - Email verification
    - System notifications
    """
    
    # Global branding variables - change these in one place
    COMPANY_NAME = "Jobeas"
    DEFAULT_FROM_EMAIL_FALLBACK = "noreply@jobeas.com"
    SUPPORT_EMAIL = "support@jobeas.com"
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        from_email: Optional[str] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an HTML email using a template
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Path to the HTML template (without .html extension)
            context: Dictionary of context variables for the template
            from_email: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
            bcc: List of BCC recipients
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            print(f"Attempting to send email:")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Template: {template_name}")
            print(f"Context: {context}")
            
            # Get sender email from settings if not provided
            if not from_email:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', NotificationService.DEFAULT_FROM_EMAIL_FALLBACK)
            print(f"From: {from_email}")
            print(f"Settings DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
            print(f"Environment FROM_EMAIL: {os.environ.get('FROM_EMAIL', 'NOT SET')}")
            
            # Render HTML content
            print(f"Rendering template: {template_name}.html")
            html_content = render_to_string(f"{template_name}.html", context)
            print(f"HTML content length: {len(html_content)}")
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body='',  # Empty body as we're using HTML
                from_email=from_email,
                to=[to_email],
                bcc=bcc
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, "text/html")
            print("Email object created with HTML content attached")
            
            # Send email
            print("Attempting to send email...")
            email.send()
            print("Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    
    @classmethod
    def send_welcome_email(cls, user) -> bool:
        """Send welcome email to new users"""
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        context = {
            'user': user,
            'company_name': cls.COMPANY_NAME,
            'support_email': cls.SUPPORT_EMAIL,
            'dashboard_url': f"{site_url}/dashboard/" if site_url else '/dashboard/',
            'logo_url': f"{site_url}/static/img/logo.png" if site_url else '/static/img/logo.png',
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f"Welcome to {cls.COMPANY_NAME}!",
            template_name="email_utility/emails/welcome",
            context=context
        )
    
    @classmethod
    def send_team_invitation(cls, invitation) -> bool:
        print("......about to ......send_team_invitation............")
        """Send team invitation email"""
        try:
            print("Creating context for invitation email...")
            print(f"Team: {invitation.team}")
            print(f"Inviter: {invitation.invited_by}")
            print(f"Email: {invitation.email}")
            
            context = {
                'team': invitation.team,
                'inviter': invitation.invited_by,
                'accept_url': invitation.get_accept_url(),
                'decline_url': invitation.get_decline_url(),
                'expires_at': invitation.expires_at,
            }
            print("Context created successfully:", context)
            
            print("About to call send_email method...")
            result = cls.send_email(
                to_email=invitation.email,
                subject=f"Invitation to join {invitation.team.name} on {cls.COMPANY_NAME}",
                template_name="team/emails/invitation_body",
                context=context
            )
            print(f"send_email result: {result}")
            return result
            
        except Exception as e:
            print(f"Error in send_team_invitation: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    
    @classmethod
    def send_password_reset(cls, user, reset_url: str) -> bool:
        """Send password reset email"""
        context = {
            'user': user,
            'reset_url': reset_url,
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f"Reset Your {cls.COMPANY_NAME} Password",
            template_name="email_utility/emails/password_reset",
            context=context
        )
    
    @classmethod
    def send_verification_email(cls, user, verify_url: str) -> bool:
        """Send email verification link"""
        context = {
            'user': user,
            'verify_url': verify_url,
        }
        
        return cls.send_email(
            to_email=user.email,
            subject="Verify Your Email Address",
            template_name="email_utility/emails/verify_email",
            context=context
        )
    
    @classmethod
    def send_team_removal_notification(cls, user_email, team_name, removed_by) -> bool:
        """Send notification when a user is removed from a team"""
        context = {
            'team_name': team_name,
            'removed_by': removed_by,
        }
        
        return cls.send_email(
            to_email=user_email,
            subject=f"You have been removed from {team_name}",
            template_name="team/emails/removal_notification",
            context=context
        )
    
    @classmethod
    def send_account_deletion_notification(cls, user_email, user_name) -> bool:
        """Send notification when a user deletes their account"""
        context = {
            'user_name': user_name,
        }
        
        return cls.send_email(
            to_email=user_email,
            subject="Your Account Has Been Deleted",
            template_name="email_utility/account_deletion_notification",
            context=context
        )

    @classmethod
    def send_subscription_confirmation(cls, subscription) -> bool:
        """Send subscription confirmation email"""
        from subscriptions.pricing_display import format_money_amount

        user = subscription.user
        plan = subscription.plan
        duration = subscription.plan_duration

        context = {
            'user': user,
            'subscription': subscription,
            'plan': plan,
            'duration': duration,
            'amount_display': format_money_amount(duration.price, billing_currency),
            'company_name': cls.COMPANY_NAME,
            'support_email': cls.SUPPORT_EMAIL,
            'dashboard_url': f"{settings.SITE_URL}/dashboard/" if hasattr(settings, 'SITE_URL') else '/dashboard/',
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f"Welcome to {plan.name} Plan - {cls.COMPANY_NAME}",
            template_name="subscriptions/emails/subscription_confirmation",
            context=context
        )

    @classmethod
    def send_subscription_renewal_reminder(cls, subscription) -> bool:
        """Send subscription renewal reminder email"""
        user = subscription.user
        plan = subscription.plan
        duration = subscription.plan_duration
        
        context = {
            'user': user,
            'subscription': subscription,
            'plan': plan,
            'duration': duration,
            'company_name': cls.COMPANY_NAME,
            'support_email': cls.SUPPORT_EMAIL,
            'billing_url': f"{settings.SITE_URL}/subscriptions/billing/" if hasattr(settings, 'SITE_URL') else '/subscriptions/billing/',
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f"Your {plan.name} subscription will renew soon - {cls.COMPANY_NAME}",
            template_name="subscriptions/emails/subscription_renewal_reminder",
            context=context
        )

    @classmethod
    def send_subscription_cancelled(cls, subscription) -> bool:
        """Send subscription cancellation confirmation"""
        user = subscription.user
        plan = subscription.plan
        
        context = {
            'user': user,
            'subscription': subscription,
            'plan': plan,
            'company_name': cls.COMPANY_NAME,
            'support_email': cls.SUPPORT_EMAIL,
            'pricing_url': f"{settings.SITE_URL}/subscriptions/pricing/" if hasattr(settings, 'SITE_URL') else '/subscriptions/pricing/',
        }
        
        return cls.send_email(
            to_email=user.email,
            subject=f"Your {plan.name} subscription has been cancelled - {cls.COMPANY_NAME}",
            template_name="subscriptions/emails/subscription_cancelled",
            context=context
        ) 