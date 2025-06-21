from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, JsonResponse
from .services.mailbox_service import MailboxService
from .models import UserEmailConfiguration
from django_mailbox.models import Message
from django.utils import timezone
import email
from email.utils import parsedate_to_datetime
from imaplib import IMAP4, IMAP4_SSL
import traceback
from django.core import serializers
from email.message import EmailMessage
from email.header import decode_header
import base64
from email_utility.services.gmail_provider import GmailProvider
# Create your views here.

@login_required
def mailbox_view(request):
    """Main mailbox view showing messages from selected folder"""
    try:
        # Get user's email configuration
        email_config = get_object_or_404(
            UserEmailConfiguration, 
            user=request.user, 
            is_active=True
        )
        
        # Initialize mailbox service
        mailbox_service = MailboxService(email_config)
        
        # Get parameters
        folder = request.GET.get('folder', 'inbox')
        page = int(request.GET.get('page', 1))
        
        # Get messages for the folder
        message_data = mailbox_service.get_messages(
            folder=folder,
            page=page
        )
        
        # Get available folders
        folders = mailbox_service.get_folders()
        
        context = {
            'messages': message_data['messages'],
            'current_folder': folder,
            'folders': folders,
            'pagination': {
                'current_page': message_data['current_page'],
                'total_pages': message_data['total_pages'],
                'has_next': message_data['has_next'],
                'has_previous': message_data['has_previous']
            },
            'email_config': email_config
        }
        
        # If HTMX request, return only the message list partial
        if request.headers.get('HX-Request'):
            return render(request, 'email_utility/mailbox/_message_list.html', context)
            
        return render(request, 'email_utility/mailbox/inbox.html', context)
        
    except Exception as e:
        if request.headers.get('HX-Request'):
            return HttpResponse(
                f'<div class="text-red-500 p-4">Error loading messages: {str(e)}</div>'
            )
        raise

def get_email_body(email_message):
    """Extract email body from email message"""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode()
            elif part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode()
    else:
        return email_message.get_payload(decode=True).decode()

@login_required
def message_detail(request, message_id):
    try:
        messages = Message.objects.filter(
            id=message_id,
            mailbox__user_config__email_config__user=request.user
        ).select_related('mailbox')
        
        if not messages:
            return HttpResponse(
                '<div class="p-4 text-red-500">Message not found</div>'
            )
            
        message = messages[0]
        email_object = message.get_email_object()
        
        # New approach for subject decoding
        subject = message.subject
        if subject and '=?' in subject:
            try:
                # Try to decode the entire subject as a MIME header
                decoded_subject = email_object.get('subject', '')
                if decoded_subject:
                    subject = str(decoded_subject)
            except Exception:
                # Fallback to original subject if decoding fails
                pass
        
        # Get the content
        content = message.get_body()
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                content = content.decode('iso-8859-1')
        
        # Clean up the content
        content = content.replace('\r\n', '\n')
            
        context = {
            'message': message,
            'email_content': content,
            'from_address': message.from_address,
            'to_addresses': message.to_addresses,
            'subject': subject,
            'date': message.processed,
        }
            
        if request.headers.get('HX-Request'):
            return render(request, 'email_utility/mailbox/_message_detail.html', context)
            
        return render(request, 'email_utility/mailbox/message_detail.html', context)
        
    except Exception as e:
        print(f"Error Type: {type(e)}")
        print(f"Error Message: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        if request.headers.get('HX-Request'):
            return HttpResponse(
                f'<div class="p-4 text-red-500">Error loading message: {str(e)}</div>'
            )
        raise

@login_required
def sync_mailbox(request):
    """Manually trigger mailbox sync"""
    if request.method != 'POST':
        return HttpResponse('Method not allowed', status=405)
        
    try:
        email_config = get_object_or_404(
            UserEmailConfiguration, 
            user=request.user, 
            is_active=True
        )
        
        mailbox_service = MailboxService(email_config)
        messages_created = mailbox_service.sync_recent_messages(limit=5)
        
        if messages_created >= 0:
            return HttpResponse(
                f'<div class="text-green-500 p-4">Synced {messages_created} new messages!</div>'
            )
        else:
            return HttpResponse(
                '<div class="text-red-500 p-4">Failed to sync mailbox</div>'
            )
            
    except Exception as e:
        return HttpResponse(
            f'<div class="text-red-500 p-4">Error: {str(e)}</div>'
        )



import bleach

def sanitize_email_html(html_content):
    # Define allowed tags, including styles and other necessary tags
    allowed_tags = bleach.sanitizer.ALLOWED_TAGS + [
        'html', 'head', 'meta', 'title', 'style', 'body',
        'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot',
        'div', 'span', 'img', 'a', 'p', 'br', 'ul', 'ol', 'li',
        'strong', 'em', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]

    # Define allowed attributes, including styles
    allowed_attributes = {
        '*': ['class', 'id', 'style', 'align', 'valign', 'bgcolor'],
        'img': ['src', 'alt', 'width', 'height', 'style'],
        'a': ['href', 'title', 'style'],
        'table': ['width', 'height', 'cellpadding', 'cellspacing', 'border', 'style'],
        'td': ['width', 'height', 'colspan', 'rowspan', 'style'],
        'th': ['width', 'height', 'colspan', 'rowspan', 'style'],
    }

    # Define allowed CSS properties
    allowed_styles = [
        'color', 'background-color', 'width', 'height', 'text-align',
        'border', 'border-collapse', 'margin', 'padding',
        'font-size', 'font-family', 'line-height', 'float',
        'display', 'position', 'top', 'left', 'right', 'bottom',
        'max-width', 'min-width', 'max-height', 'min-height',
        'text-decoration', 'font-weight', 'font-style'
    ]

    # Clean the HTML content
    cleaned_html = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        styles=allowed_styles,
        strip=True,             # Remove disallowed tags completely
        strip_comments=False    # Keep comments if necessary
    )

    return cleaned_html


@login_required
def email_setup_step1(request):
    """First step of email setup - provider selection"""
    agent_id=request.GET.get('agent_id', 'NO_AGENT_ID_FOUND')  # Get from HTMX request
    print(f"Agent ID: {agent_id}")
    context = {
        'providers': UserEmailConfiguration.PROVIDER_CHOICES,
        'agent_id': agent_id
    }
    return render(request, 'email_utility/partials/email_step1.html', context)

@login_required
def get_existing_emails(request):
    """Fetch existing email configurations for user"""
    agent_id = request.GET.get('agent_id')
    email_configs = UserEmailConfiguration.objects.filter(
        user=request.user,
        is_active=True
    )
    return render(request, 'email_utility/partials/existing_emails.html', {
        'email_configs': email_configs,
        'agent_id': agent_id
    })


@login_required
def email_setup_step2(request, provider_id):
    """Second step of email setup - credentials"""
    # Get provider info from model choices
    provider_dict = dict(UserEmailConfiguration.PROVIDER_CHOICES)
    
    if provider_id not in provider_dict:
        return HttpResponse(
            '<div class="p-4 text-center text-red-600">'
            '<p>Invalid email provider selected.</p>'
            '</div>'
        )

    # Create provider context with additional info
    provider = {
        'id': provider_id,
        'name': provider_dict[provider_id],
        'requires_app_password': provider_id == 'gmail',  # Special handling for Gmail
        'app_password_url': {
            'gmail': 'https://myaccount.google.com/apppasswords',
            'outlook': 'https://account.live.com/proofs/AppPassword',
            'yahoo': 'https://login.yahoo.com/account/security',
        }.get(provider_id),
        'setup_instructions': {
            'gmail': [
                'Enable 2-Factor Authentication in your Google Account',
                'Generate an App Password from Google Account Settings',
                'Use your email and the generated App Password here'
            ],
            'outlook': [
                'Use your Outlook email address',
                'Use your regular Outlook password or generate an app password'
            ],
            'yahoo': [
                'Enable 2-Factor Authentication in Yahoo Account Security',
                'Generate an App Password from Account Security',
                'Use your email and the generated App Password here'
            ],
        }.get(provider_id, ['Enter your email address', 'Enter your password'])
    }
    agent_id=request.GET.get('agent_id')  # Get from HTMX request
    print(f"Agent ID etp2: {agent_id}")
    
    return render(request, 'email_utility/partials/email_step2.html', {'provider': provider, 'agent_id': agent_id})



@login_required
def email_setup_task_select(request):
    """Handle selection of existing email and show task selection"""
    if request.method == 'POST':
        email_config_id = request.POST.get('email_selection')
        agent_id = request.POST.get('agent_id')
        
        email_config = get_object_or_404(
            UserEmailConfiguration,
            id=email_config_id,
            user=request.user
        )
        
        return render(request, 'email_utility/partials/email_task_select.html', {
            'email_config': email_config,
            'agent_id': agent_id,
            'task_types': AgentEmailConfiguration.TaskTypes.choices
        })

@login_required
def save_email_configuration(request):
    """Handle email configuration creation/validation"""
    if request.method == 'POST':
        provider_type = request.POST.get('provider')
        email = request.POST.get('email')
        password = request.POST.get('password')
        agent_id = request.POST.get('agent_id')
        
        try:
            # Validate provider
            valid_providers = [choice[0] for choice in UserEmailConfiguration.PROVIDER_CHOICES]
            if provider_type not in valid_providers:
                return HttpResponse(
                    '<div class="p-4 text-center text-red-600">'
                    '<p>Invalid provider selected.</p>'
                    '</div>'
                )
            
            # Validate credentials
            if provider_type == 'gmail':
                provider = GmailProvider()
                is_valid, error_message = provider.test_credentials(email, password)
                if not is_valid:
                    return HttpResponse(
                        '<div class="p-4 text-center text-red-600">'
                        f'<p>{error_message}</p>'
                        '</div>'
                    )

            # Check existing email
            if UserEmailConfiguration.objects.filter(user=request.user, email=email).exists():
                return HttpResponse(
                    '<div class="p-4 text-center text-red-600">'
                    '<p>Email already configured</p>'
                    '</div>'
                )

            # Create configuration
            config = UserEmailConfiguration.objects.create(
                user=request.user,
                provider_type=provider_type,
                email=email,
                credentials={'password': password},
                is_active=True
            )

            # Instead of JSON response, render task selection
            return render(request, 'email_utility/partials/email_task_select.html', {
                'email_config': config,
                'agent_id': agent_id,
                'task_types': AgentEmailConfiguration.TaskTypes.choices
            })

        except Exception as e:
            return HttpResponse(
                '<div class="p-4 text-center text-red-600">'
                f'<p>Error: {str(e)}</p>'
                '</div>'
            )



