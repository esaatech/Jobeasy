import os
import json
import logging
import tempfile
import secrets
from datetime import datetime
from urllib.parse import urlencode, urlparse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.urls import reverse
from django.utils import timezone

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from .models import GmailAuth, EmailHistory, SMTPAccount
from .services.gmail_service import GmailService, create_gmail_auth_from_credentials
from .services.smtp_service import SMTPService
from .services.yahoo_service import YahooService, create_yahoo_auth_from_token_payload
from resume_builder.models import Resume
from coverletter.models import CoverLetter

logger = logging.getLogger(__name__)


def _resolve_post_oauth_redirect(request, return_url: str) -> str:
    """
    Resolve session 'next' after OAuth. Allow same-site paths, Django URL names,
    and absolute URLs only when they target this host (avoid open redirects).
    """
    if return_url.startswith("/") and not return_url.startswith("//"):
        return return_url
    if return_url.startswith(("http://", "https://")):
        parsed = urlparse(return_url)
        if parsed.netloc == request.get_host():
            return return_url
        logger.warning(
            "Rejected OAuth redirect to another host: %s",
            parsed.netloc,
        )
        return "dashboard:dashboard"
    return return_url


def _clear_gmail_oauth_session(request):
    """Clean up transient OAuth session keys."""
    request.session.pop("gmail_oauth_state", None)
    request.session.pop("gmail_oauth_code_verifier", None)


def _clear_yahoo_oauth_session(request):
    """Clean up transient Yahoo OAuth session keys."""
    request.session.pop("yahoo_oauth_state", None)


def _get_connected_sender_accounts(user):
    """Return all connected sender accounts for compose/send UX."""
    accounts = []

    gmail_service = GmailService(user)
    if gmail_service.is_authenticated():
        accounts.append(
            {
                "id": "gmail_oauth",
                "provider": "gmail",
                "email": gmail_service.gmail_auth.gmail_address,
                "label": f"Gmail ({gmail_service.gmail_auth.gmail_address})",
                "is_default": False,
            }
        )

    smtp_accounts = SMTPAccount.objects.filter(
        user=user,
        is_active=True,
    ).order_by("-is_default", "-updated_at")
    for account in smtp_accounts:
        accounts.append(
            {
                "id": f"smtp_{account.id}",
                "provider": account.provider,
                "email": account.email_address,
                "label": f"{account.get_provider_display()} ({account.email_address})",
                "is_default": account.is_default,
            }
        )

    if accounts and not any(a.get("is_default") for a in accounts):
        accounts[0]["is_default"] = True

    return accounts


def _resolve_sender_for_request(user, sender_account_id: str):
    """Resolve and validate sender account selected by user."""
    sender_account_id = (sender_account_id or "").strip()
    connected_accounts = _get_connected_sender_accounts(user)
    if not connected_accounts:
        return None, "No connected email account found. Connect Gmail, Yahoo, or Outlook first."

    account_map = {a["id"]: a for a in connected_accounts}
    selected = account_map.get(sender_account_id) if sender_account_id else None
    if sender_account_id and not selected:
        logger.warning("Unsupported sender account selection user_id=%s sender_id=%s", user.pk, sender_account_id)
        return None, "Selected sender is no longer available. Please choose a connected account."
    if not selected:
        selected = next((a for a in connected_accounts if a.get("is_default")), connected_accounts[0])

    return selected, None


def gmail_authorize(request):
    """Start Gmail OAuth2 authorization flow"""
    try:
        # Store the next URL to redirect back after OAuth
        next_url = request.GET.get('next', 'dashboard:dashboard')
        request.session['gmail_redirect_after_auth'] = next_url
        
        # Create OAuth2 flow with updated scopes
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                }
            },
            autogenerate_code_verifier=True,
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/gmail.send'
            ]
        )
        
        # Set the redirect URI
        flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session for security
        request.session['gmail_oauth_state'] = state
        if getattr(flow, "code_verifier", None):
            request.session["gmail_oauth_code_verifier"] = flow.code_verifier
        else:
            logger.warning("Gmail OAuth flow generated without PKCE code_verifier")
        
        return redirect(authorization_url)
        
    except Exception as e:
        messages.error(request, f"Error starting Gmail authorization: {str(e)}")
        return redirect('dashboard:dashboard')


def gmail_callback(request):
    """Handle Gmail OAuth2 callback with login support"""
    try:
        oauth_error = request.GET.get("error")
        oauth_error_description = request.GET.get("error_description", "")
        if oauth_error:
            logger.warning(
                "Gmail OAuth returned error=%s description=%s",
                oauth_error,
                oauth_error_description[:500] if oauth_error_description else "",
            )
            readable = oauth_error.replace("_", " ").strip()
            extra = (
                f" ({oauth_error_description})"
                if oauth_error_description
                else ""
            )
            messages.error(
                request,
                f"Google sign-in was not completed: {readable}.{extra}",
            )
            return redirect("dashboard:dashboard")

        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code:
            logger.warning("Gmail OAuth callback missing code parameter")
            messages.error(
                request,
                "Missing authorization from Google. Start the Gmail connection again.",
            )
            return redirect("dashboard:dashboard")

        session_state = request.session.get("gmail_oauth_state")
        if state != session_state:
            logger.warning(
                "Gmail OAuth state mismatch (session may have expired or cookies not sent)"
            )
            messages.error(
                request,
                "Your sign-in session expired. Please try connecting Gmail again.",
            )
            return redirect("dashboard:dashboard")

        session_code_verifier = request.session.get("gmail_oauth_code_verifier")
        if not session_code_verifier:
            logger.warning(
                "Missing PKCE code_verifier in session during Gmail callback (state validated=%s)",
                bool(session_state),
            )
            _clear_gmail_oauth_session(request)
            messages.error(
                request,
                "Your Gmail authorization session expired before token exchange. Please try again.",
            )
            return redirect("dashboard:dashboard")

        logger.info("Gmail OAuth callback received valid code and state")

        # Create flow and exchange code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                }
            },
            autogenerate_code_verifier=True,
            scopes=[
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/gmail.send'
            ]
        )
        
        flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        flow.code_verifier = session_code_verifier

        # Exchange authorization code for credentials
        try:
            flow.fetch_token(code=code)
        except Exception as token_error:
            error_text = str(token_error)
            error_lower = error_text.lower()
            logger.exception("Gmail OAuth token exchange failed: %s", error_text)
            _clear_gmail_oauth_session(request)

            if "missing code verifier" in error_lower:
                messages.error(
                    request,
                    "Google token exchange failed (missing PKCE verifier). Start Gmail connection again from the app.",
                )
                return redirect("dashboard:dashboard")

            if "scope has changed" in error_lower:
                messages.error(
                    request,
                    "Google returned different scopes than requested. Ensure your account is a Google OAuth test user, and that GOOGLE_REDIRECT_URI/client settings match Google Cloud exactly.",
                )
                return redirect("dashboard:dashboard")

            messages.error(request, f"Error completing Gmail authorization: {error_text}")
            return redirect("dashboard:dashboard")

        credentials = flow.credentials
        granted_scopes = sorted(getattr(credentials, "scopes", []) or [])
        logger.info(
            "Gmail OAuth token exchange succeeded; granted_scopes=%s",
            granted_scopes,
        )
        _clear_gmail_oauth_session(request)

        # Get user's profile information
        gmail_service = GmailService(request.user if request.user.is_authenticated else None)
        user_info = gmail_service.verify_user_identity(credentials)
        
        if not user_info or not user_info.get('email'):
            messages.error(request, "Could not retrieve user information from Google")
            return redirect('dashboard:dashboard')
        
        gmail_address = user_info['email']
        user_name = user_info.get('name', '')
        
        # Check if user is already logged in
        if request.user.is_authenticated:
            # Existing user - just connect Gmail
            user = request.user
            gmail_service.user = user
            gmail_service.gmail_auth = create_gmail_auth_from_credentials(
                user, credentials, gmail_address
            )
            messages.success(request, f"Gmail connected successfully! You can now send emails from {gmail_address}")
        else:
            # New user - create account and log them in
            # Check if user with this email already exists
            try:
                user = User.objects.get(email=gmail_address)
                messages.info(request, f"Welcome back! Logged in as {user.username}")
            except User.MultipleObjectsReturned:
                # Legacy data may contain duplicate emails; pick the oldest account deterministically.
                user = User.objects.filter(email=gmail_address).order_by("id").first()
                logger.warning(
                    "Multiple users found for gmail email=%s; selected user_id=%s",
                    gmail_address,
                    getattr(user, "id", None),
                )
                messages.info(request, f"Welcome back! Logged in as {user.username}")
            except User.DoesNotExist:
                # Create new user
                username = gmail_address.split('@')[0]  # Use email prefix as username
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=gmail_address,
                    first_name=user_name.split()[0] if user_name else '',
                    last_name=' '.join(user_name.split()[1:]) if user_name and len(user_name.split()) > 1 else ''
                )
                messages.success(request, f"Account created successfully! Welcome to JobEas, {user_name or username}")
            
            # Log the user in
            login(request, user)
            
            # Create GmailAuth for the user
            gmail_service.user = user
            gmail_service.gmail_auth = create_gmail_auth_from_credentials(
                user, credentials, gmail_address
            )
        
        return_url = request.session.get("gmail_redirect_after_auth", "dashboard:dashboard")
        if "gmail_redirect_after_auth" in request.session:
            del request.session["gmail_redirect_after_auth"]

        target = _resolve_post_oauth_redirect(request, return_url)
        logger.info(
            "Gmail OAuth complete; redirecting user_id=%s to %s",
            getattr(request.user, "pk", None),
            target,
        )
        return redirect(target)

    except Exception as e:
        logger.exception("Error completing Gmail authorization: %s", e)
        _clear_gmail_oauth_session(request)
        messages.error(request, f"Error completing Gmail authorization: {str(e)}")
        return redirect('dashboard:dashboard')


def yahoo_authorize(request):
    """Start Yahoo OAuth2 authorization flow."""
    try:
        next_url = request.GET.get("next", "dashboard:dashboard")
        request.session["yahoo_redirect_after_auth"] = next_url
        state = secrets.token_urlsafe(32)
        request.session["yahoo_oauth_state"] = state
        authorization_url = YahooService.get_authorization_url(state=state)
        return redirect(authorization_url)
    except Exception as exc:
        logger.exception("Error starting Yahoo authorization: %s", exc)
        messages.error(request, f"Error starting Yahoo authorization: {str(exc)}")
        return redirect("dashboard:dashboard")


def yahoo_callback(request):
    """Handle Yahoo OAuth callback with login support."""
    try:
        oauth_error = request.GET.get("error")
        if oauth_error:
            messages.error(request, f"Yahoo sign-in was not completed: {oauth_error.replace('_', ' ')}.")
            return redirect("dashboard:dashboard")

        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code:
            messages.error(request, "Missing authorization from Yahoo. Start the Yahoo connection again.")
            return redirect("dashboard:dashboard")

        session_state = request.session.get("yahoo_oauth_state")
        if state != session_state:
            messages.error(request, "Your Yahoo sign-in session expired. Please try connecting Yahoo again.")
            return redirect("dashboard:dashboard")

        token_payload = YahooService.exchange_code_for_tokens(code=code)
        _clear_yahoo_oauth_session(request)

        access_token = token_payload.get("access_token")
        if not access_token:
            messages.error(request, "Yahoo token exchange failed. Please try again.")
            return redirect("dashboard:dashboard")

        user_info = YahooService.fetch_user_info(access_token=access_token) or {}
        yahoo_address = user_info.get("email")
        user_name = user_info.get("name", "")
        if not yahoo_address:
            messages.error(request, "Could not retrieve your Yahoo email address.")
            return redirect("dashboard:dashboard")

        yahoo_service = YahooService(request.user if request.user.is_authenticated else None)
        if request.user.is_authenticated:
            user = request.user
            yahoo_service.user = user
            yahoo_service.yahoo_auth = create_yahoo_auth_from_token_payload(user, token_payload, yahoo_address)
            messages.success(request, f"Yahoo connected successfully! You can now send emails from {yahoo_address}")
        else:
            try:
                user = User.objects.get(email=yahoo_address)
                messages.info(request, f"Welcome back! Logged in as {user.username}")
            except User.MultipleObjectsReturned:
                user = User.objects.filter(email=yahoo_address).order_by("id").first()
                logger.warning(
                    "Multiple users found for yahoo email=%s; selected user_id=%s",
                    yahoo_address,
                    getattr(user, "id", None),
                )
                messages.info(request, f"Welcome back! Logged in as {user.username}")
            except User.DoesNotExist:
                username = yahoo_address.split("@")[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                user = User.objects.create_user(
                    username=username,
                    email=yahoo_address,
                    first_name=user_name.split()[0] if user_name else "",
                    last_name=" ".join(user_name.split()[1:]) if user_name and len(user_name.split()) > 1 else "",
                )
                messages.success(request, f"Account created successfully! Welcome to JobEas, {user_name or username}")

            login(request, user)
            yahoo_service.user = user
            yahoo_service.yahoo_auth = create_yahoo_auth_from_token_payload(user, token_payload, yahoo_address)

        return_url = request.session.get("yahoo_redirect_after_auth", "dashboard:dashboard")
        if "yahoo_redirect_after_auth" in request.session:
            del request.session["yahoo_redirect_after_auth"]
        target = _resolve_post_oauth_redirect(request, return_url)
        return redirect(target)
    except Exception as exc:
        logger.exception("Error completing Yahoo authorization: %s", exc)
        _clear_yahoo_oauth_session(request)
        messages.error(request, f"Error completing Yahoo authorization: {str(exc)}")
        return redirect("dashboard:dashboard")


@login_required
def email_compose(request, document_type, document_id):
    """Show email composition form"""
    try:
        # Initialize variables
        cover_letter = None
        resume = None
        job_app = None
        
        # Get the document (resume, cover letter, or job application)
        if document_type == 'resume':
            document = get_object_or_404(Resume, id=document_id, user=request.user)
            document_name = document.name
            attachment_type = 'resume'
            email_body = None
            resume = document  # Set resume for context
        elif document_type == 'cover_letter':
            document = get_object_or_404(CoverLetter, id=document_id, user=request.user)
            document_name = document.title
            attachment_type = 'none'  # For display purposes - no attachment
            # Pass plain text to template for user-friendly display
            email_body = document.content
            cover_letter = document  # Set cover_letter for context
        elif document_type == 'job_application':
            # For job applications, handle all scenarios: cover letter only, resume only, or both
            from dashboard.models import JobApplication as DashboardJobApplication
            from job_service.models import JobApplication as JobServiceJobApplication
            
            # Try dashboard JobApplication first
            try:
                job_app = DashboardJobApplication.objects.get(id=document_id, user=request.user)
                cover_letter = job_app.cover_letter
                resume = job_app.resume
                
                # Determine document name and attachment type based on what's available
                if cover_letter and resume:
                    # Both cover letter and resume - keep job application context
                    document_name = f"Application for {job_app.job_name}"
                    attachment_type = 'resume'
                    email_body = cover_letter.content
                    document = job_app  # Use job application as the main document
                elif cover_letter:
                    # Cover letter only
                    document_name = cover_letter.title
                    attachment_type = 'none'
                    email_body = cover_letter.content
                    document = cover_letter
                    document_type = 'cover_letter'  # Update document_type for individual document
                    resume = None
                elif resume:
                    # Resume only
                    document_name = resume.name
                    attachment_type = 'resume'
                    email_body = None
                    document = resume
                    document_type = 'resume'  # Update document_type for individual document
                    cover_letter = None
                else:
                    messages.error(request, "No cover letter or resume found for this job application")
                    return redirect('dashboard:dashboard')
                    
            except DashboardJobApplication.DoesNotExist:
                # Try job service JobApplication
                try:
                    job_app = JobServiceJobApplication.objects.get(id=document_id, user=request.user)
                    # For job service, we can only handle resume since cover letter is text
                    if job_app.resume_used:
                        document_name = job_app.resume_used.name
                        attachment_type = 'resume'
                        email_body = None
                        document = job_app.resume_used
                        document_type = 'resume'  # Update document_type for individual document
                        cover_letter = None
                        resume = job_app.resume_used
                    else:
                        messages.error(request, "No resume found for this job application")
                        return redirect('dashboard:dashboard')
                except JobServiceJobApplication.DoesNotExist:
                    messages.error(request, "Job application not found")
                    return redirect('dashboard:dashboard')
        else:
            messages.error(request, "Invalid document type")
            return redirect('dashboard:dashboard')
        
        sender_accounts = _get_connected_sender_accounts(request.user)
        selected_sender = next((account for account in sender_accounts if account.get("is_default")), None)
        
        # Extract applicant name from resume if available
        applicant_name = None
        if document_type == 'resume' and document and hasattr(document, 'personal_info') and document.personal_info:
            applicant_name = document.personal_info.get('full_name')
        elif resume and resume.personal_info:
            applicant_name = resume.personal_info.get('full_name')
        
        context = {
            'document': document,
            'document_type': document_type,
            'document_name': document_name,
            'attachment_type': attachment_type,
            'is_gmail_connected': any(account["provider"] == "gmail" for account in sender_accounts),
            'gmail_address': selected_sender["email"] if selected_sender else None,
            'sender_accounts': sender_accounts,
            'selected_sender_id': selected_sender["id"] if selected_sender else "",
            'email_body': email_body, # Pass the email_body to the context
            'cover_letter': cover_letter,  # Pass cover letter object if available
            'resume': resume,  # Pass resume object if available
            'job_app': job_app,  # Always pass job_app when we have it
            'applicant_name': applicant_name,  # Pass the applicant name from resume
        }
        
        return render(request, 'email_utility/compose.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading email composition: {str(e)}")
        return redirect('dashboard:dashboard')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def send_email(request):
    """Send email via Gmail API"""
    try:
        data = json.loads(request.body)
        
        recipient_email = data.get('recipient_email')
        subject = data.get('subject')
        message = data.get('message')
        document_type = data.get('document_type')
        document_id = data.get('document_id')
        sender_account_id = data.get('sender_account')
        
        # Validate required fields
        if not all([recipient_email, subject, message, document_type, document_id]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        selected_sender, sender_error = _resolve_sender_for_request(request.user, sender_account_id)
        if sender_error:
            return JsonResponse({
                'success': False,
                'error': sender_error
            }, status=400)
        
        # Get the document
        
        if document_type == 'resume':
            document = get_object_or_404(Resume, id=document_id, user=request.user)
            attachment_name = f"{document.name}.pdf"
            cover_letter = None
            resume = document
        elif document_type == 'cover_letter':
            document = get_object_or_404(CoverLetter, id=document_id, user=request.user)
            attachment_name = None  # No attachment for cover letters
            cover_letter = document
            resume = None
        elif document_type == 'job_application':
            # Handle job application with potential cover letter and resume
            from dashboard.models import JobApplication as DashboardJobApplication
            from job_service.models import JobApplication as JobServiceJobApplication
            
            try:
                job_app = DashboardJobApplication.objects.get(id=document_id, user=request.user)
                cover_letter = job_app.cover_letter
                resume = job_app.resume
                
                if cover_letter and resume:
                    # Both cover letter and resume - use resume for attachment
                    document = resume
                    attachment_name = f"{resume.name}.pdf"
                elif cover_letter:
                    # Cover letter only
                    document = cover_letter
                    attachment_name = None
                    resume = None
                elif resume:
                    # Resume only
                    document = resume
                    attachment_name = f"{resume.name}.pdf"
                    cover_letter = None
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No cover letter or resume found for this job application'
                    }, status=400)
                    
            except DashboardJobApplication.DoesNotExist:
                # Try job service JobApplication
                try:
                    job_app = JobServiceJobApplication.objects.get(id=document_id, user=request.user)
                    if job_app.resume_used:
                        document = job_app.resume_used
                        attachment_name = f"{job_app.resume_used.name}.pdf"
                        cover_letter = None
                        resume = job_app.resume_used
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'No resume found for this job application'
                        }, status=400)
                except JobServiceJobApplication.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Job application not found'
                    }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid document type'
            }, status=400)
        
        # Create email history record
        email_history = EmailHistory.objects.create(
            user=request.user,
            recipient_email=recipient_email,
            subject=subject,
            message=message,
            attachment_type=document_type,
            attachment_id=document_id,
            status='pending'
        )
        
        # Generate PDF attachment
        attachment_path = None
        try:
            if document_type == 'resume' or (document_type == 'job_application' and resume):
                # Generate resume PDF
                from pdf_generator.core.generator import PDFGenerator
                
                # Prepare resume data manually (Resume model doesn't have get_resume_data method)
                resume_data = {
                    'personal_info': document.personal_info or {},
                    'experience': document.experience or [],
                    'education': document.education or [],
                    'skills': document.skills or {},
                    'additional': document.additional or {}
                }

                from resume_builder.resume_display import augment_resume_dict_for_rendering

                resume_data = augment_resume_dict_for_rendering(resume_data, request=request)

                pdf_bytes = PDFGenerator.generate_from_template(
                    f'resume_templates/{document.template_id}.html',
                    {'resume_data': resume_data},
                    options={'format': 'Letter', 'orientation': 'portrait'}
                )
                
                # Save PDF to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(pdf_bytes)
                    attachment_path = temp_file.name
            elif document_type == 'cover_letter':
                # No PDF generation for cover letters - content goes in email body
                pdf_bytes = None
                attachment_path = None
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid document type'
                }, status=400)
        
        except Exception as e:
            email_history.status = 'failed'
            email_history.error_message = f"Error generating PDF: {str(e)}"
            email_history.save()
            return JsonResponse({
                'success': False,
                'error': f'Error generating PDF: {str(e)}'
            }, status=500)
        
        # Send email through selected provider
        try:
            # For cover letters or job applications with cover letter, wrap the content in HTML tags for proper email formatting
            is_html = False
            if document_type == 'cover_letter' or (document_type == 'job_application' and cover_letter):
                # Replace newlines with HTML breaks before using in f-string
                formatted_message = message.replace('\n', '<br>')
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
                    {formatted_message}
                </body>
                </html>
                """
                email_body_to_send = html_body
                is_html = True
            else:
                email_body_to_send = message

            if selected_sender["id"] == "gmail_oauth":
                gmail_service = GmailService(request.user)
                if not gmail_service.is_authenticated():
                    result = {
                        "success": False,
                        "error": "Selected Gmail account is no longer connected. Please reconnect it in Integrations.",
                    }
                else:
                    result = gmail_service.send_email(
                        to_email=recipient_email,
                        subject=subject,
                        body=email_body_to_send,
                        attachment_path=attachment_path,
                        attachment_name=attachment_name
                    )
            else:
                smtp_account_id = int(selected_sender["id"].replace("smtp_", ""))
                smtp_account = SMTPAccount.objects.get(
                    id=smtp_account_id,
                    user=request.user,
                    is_active=True,
                )
                result = SMTPService(smtp_account).send_email(
                    to_email=recipient_email,
                    subject=subject,
                    body=email_body_to_send,
                    attachment_path=attachment_path,
                    attachment_name=attachment_name,
                    is_html=is_html,
                )
            
            if result['success']:
                email_history.status = 'sent'
                email_history.gmail_message_id = result['message_id']
                email_history.save()
                
                response_data = {
                    'success': True,
                    'message': 'Email sent successfully!',
                    'message_id': result['message_id']
                }
            else:
                email_history.status = 'failed'
                email_history.error_message = result['error']
                email_history.save()
                
                response_data = {
                    'success': False,
                    'error': result['error']
                }
            
        except Exception as e:
            email_history.status = 'failed'
            email_history.error_message = str(e)
            email_history.save()
            
            response_data = {
                'success': False,
                'error': f'Error sending email: {str(e)}'
            }
        
        finally:
            # Clean up temporary file
            if attachment_path and os.path.exists(attachment_path):
                os.unlink(attachment_path)
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=500)


@login_required
def email_history(request):
    """View email sending history"""
    emails = EmailHistory.objects.filter(user=request.user).order_by('-sent_at')
    
    context = {
        'emails': emails,
        'page_title': 'Email History',
    }
    
    return render(request, 'email_utility/history.html', context)


@login_required
@require_http_methods(["POST"])
def connect_smtp_account(request):
    provider = (request.POST.get("provider") or "").strip().lower()
    email_address = (request.POST.get("email_address") or "").strip()
    app_password = (request.POST.get("app_password") or "").strip()
    set_default = request.POST.get("is_default") == "on"

    if provider not in {SMTPAccount.PROVIDER_OUTLOOK, SMTPAccount.PROVIDER_YAHOO}:
        error_text = "Unsupported provider. Please select Yahoo or Outlook."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_text}, status=400)
        messages.error(request, error_text)
        return redirect("settings:integrations")

    if not email_address or not app_password:
        error_text = "Email address and app password are required."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_text}, status=400)
        messages.error(request, error_text)
        return redirect("settings:integrations")

    is_valid, error_message = SMTPService.test_credentials(provider, email_address, app_password)
    if not is_valid:
        error_text = error_message or "Could not verify SMTP credentials."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": error_text}, status=400)
        messages.error(request, error_text)
        return redirect("settings:integrations")

    SMTPAccount.objects.update_or_create(
        user=request.user,
        provider=provider,
        email_address=email_address,
        defaults={
            "app_password": app_password,
            "is_active": True,
            "is_default": set_default,
        },
    )

    if set_default:
        SMTPAccount.objects.filter(user=request.user).exclude(
            provider=provider,
            email_address=email_address,
        ).update(is_default=False)

    success_text = f"{provider.title()} account connected successfully."
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "message": success_text})

    messages.success(request, success_text)
    return redirect("settings:integrations")


@login_required
@require_http_methods(["POST"])
def set_default_smtp_account(request, account_id):
    account = get_object_or_404(SMTPAccount, id=account_id, user=request.user)
    SMTPAccount.objects.filter(user=request.user).update(is_default=False)
    account.is_default = True
    account.save(update_fields=["is_default", "updated_at"])
    messages.success(request, f"{account.email_address} set as default sender.")
    return redirect("settings:integrations")


@login_required
@require_http_methods(["POST"])
def disconnect_smtp_account(request, account_id):
    account = get_object_or_404(SMTPAccount, id=account_id, user=request.user)
    account_label = account.email_address
    account.delete()
    messages.success(request, f"{account_label} disconnected successfully.")
    return redirect("settings:integrations")


@login_required
def gmail_settings(request):
    """Gmail connection settings"""
    gmail_service = GmailService(request.user)
    is_connected = gmail_service.is_authenticated()
    
    context = {
        'is_gmail_connected': is_connected,
        'gmail_address': gmail_service.gmail_auth.gmail_address if is_connected else None,
        'page_title': 'Gmail Settings',
    }
    
    return render(request, 'email_utility/settings.html', context)


@login_required
@require_http_methods(["POST"])
def disconnect_gmail(request):
    """Disconnect Gmail account"""
    try:
        gmail_service = GmailService(request.user)
        if gmail_service.revoke_access():
            messages.success(request, "Gmail account disconnected successfully")
        else:
            messages.error(request, "No Gmail account connected")
        
        return redirect('email_utility:gmail_settings')
        
    except Exception as e:
        messages.error(request, f"Error disconnecting Gmail: {str(e)}")
        return redirect('email_utility:gmail_settings')


@login_required
@require_http_methods(["POST"])
def disconnect_yahoo(request):
    """Disconnect Yahoo sending integration only (preserve Yahoo login link)."""
    try:
        yahoo_accounts = SMTPAccount.objects.filter(
            user=request.user,
            provider=SMTPAccount.PROVIDER_YAHOO,
            is_active=True,
        )
        deleted_count = yahoo_accounts.count()
        yahoo_accounts.delete()
        if deleted_count:
            messages.success(request, "Yahoo sending integration disconnected successfully")
        else:
            messages.error(request, "No Yahoo sending integration connected")
        return redirect("settings:integrations")
    except Exception as exc:
        messages.error(request, f"Error disconnecting Yahoo sending integration: {str(exc)}")
        return redirect("settings:integrations")



