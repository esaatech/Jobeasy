import os
import json
import tempfile
from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from .models import GmailAuth, EmailHistory
from .services.gmail_service import GmailService, create_gmail_auth_from_credentials
from resume_builder.models import Resume
from coverletter.models import CoverLetter


@login_required
def gmail_authorize(request):
    """Start Gmail OAuth2 authorization flow"""
    try:
        # Store the intended destination URL
        next_url = request.GET.get('next')
        if next_url:
            request.session['gmail_redirect_after_auth'] = next_url
        
        # Create OAuth2 flow
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
            scopes=['https://www.googleapis.com/auth/gmail.send']
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
        
        return redirect(authorization_url)
        
    except Exception as e:
        messages.error(request, f"Error starting Gmail authorization: {str(e)}")
        return redirect('dashboard:dashboard')


@login_required
def gmail_callback(request):
    """Handle Gmail OAuth2 callback"""
    try:
        # Get authorization code from request
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        # Verify state matches
        if state != request.session.get('gmail_oauth_state'):
            messages.error(request, "Invalid OAuth state")
            return redirect('dashboard:dashboard')
        
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
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        
        flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user's Gmail address first
        gmail_service = GmailService(request.user)
        user_info = gmail_service.get_user_info_with_credentials(credentials)
        
        if not user_info or not user_info.get('email'):
            messages.error(request, "Could not retrieve Gmail address")
            return redirect('dashboard:dashboard')
        
        gmail_address = user_info['email']
        
        # Create GmailAuth record with the actual email address
        gmail_service.gmail_auth = create_gmail_auth_from_credentials(
            request.user, credentials, gmail_address
        )
        
        messages.success(request, f"Gmail connected successfully! You can now send emails from {gmail_address}")
        
        # Redirect back to the original page or dashboard
        return_url = request.session.get('gmail_redirect_after_auth', 'dashboard:dashboard')
        
        if 'gmail_redirect_after_auth' in request.session:
            del request.session['gmail_redirect_after_auth']
        
        # If it's a relative URL, redirect to it directly
        if return_url.startswith('/'):
            return redirect(return_url)
        else:
            return redirect(return_url)
        
    except Exception as e:
        messages.error(request, f"Error completing Gmail authorization: {str(e)}")
        return redirect('dashboard:dashboard')


@login_required
def email_compose(request, document_type, document_id):
    """Show email composition form"""
    try:
        # Get the document (resume or cover letter)
        if document_type == 'resume':
            document = get_object_or_404(Resume, id=document_id, user=request.user)
            document_name = document.name
            attachment_type = 'resume'
        elif document_type == 'cover_letter':
            document = get_object_or_404(CoverLetter, id=document_id, user=request.user)
            document_name = document.title
            attachment_type = 'cover_letter'
        else:
            messages.error(request, "Invalid document type")
            return redirect('dashboard:dashboard')
        
        # Check Gmail authentication
        gmail_service = GmailService(request.user)
        is_gmail_connected = gmail_service.is_authenticated()
        
        context = {
            'document': document,
            'document_type': document_type,
            'document_name': document_name,
            'attachment_type': attachment_type,
            'is_gmail_connected': is_gmail_connected,
            'gmail_address': gmail_service.gmail_auth.gmail_address if is_gmail_connected else None,
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
        
        # Validate required fields
        if not all([recipient_email, subject, message, document_type, document_id]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Check Gmail authentication
        gmail_service = GmailService(request.user)
        if not gmail_service.is_authenticated():
            return JsonResponse({
                'success': False,
                'error': 'Gmail not connected. Please connect your Gmail account first.'
            }, status=400)
        
        # Get the document
        if document_type == 'resume':
            document = get_object_or_404(Resume, id=document_id, user=request.user)
            attachment_name = f"{document.name}.pdf"
        elif document_type == 'cover_letter':
            document = get_object_or_404(CoverLetter, id=document_id, user=request.user)
            attachment_name = f"{document.title}.pdf"
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
            if document_type == 'resume':
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
                
                pdf_bytes = PDFGenerator.generate_from_template(
                    f'resume_templates/{document.template_id}.html',
                    {'resume_data': resume_data},
                    options={'format': 'Letter', 'orientation': 'portrait'}
                )
            else:
                # Generate cover letter PDF
                from pdf_generator.core.generator import PDFGenerator
                pdf_bytes = PDFGenerator.generate_from_template(
                    'coverletter/cover_letter_pdf.html',
                    {'cover_letter': document.content},
                    options={'format': 'Letter', 'orientation': 'portrait'}
                )
            
            # Save PDF to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_bytes)
                attachment_path = temp_file.name
            
        except Exception as e:
            email_history.status = 'failed'
            email_history.error_message = f"Error generating PDF: {str(e)}"
            email_history.save()
            return JsonResponse({
                'success': False,
                'error': f'Error generating PDF: {str(e)}'
            }, status=500)
        
        # Send email via Gmail API
        try:
            result = gmail_service.send_email(
                to_email=recipient_email,
                subject=subject,
                body=message,
                attachment_path=attachment_path,
                attachment_name=attachment_name
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



