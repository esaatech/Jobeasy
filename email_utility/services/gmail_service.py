import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from django.conf import settings
from django.utils import timezone
from ..models import GmailAuth, EmailHistory


class GmailService:
    """Service class for Gmail API operations"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, user):
        self.user = user
        self.gmail_auth = None
        self.service = None
        self._load_gmail_auth()
    
    def _load_gmail_auth(self):
        """Load Gmail authentication for the user"""
        try:
            self.gmail_auth = GmailAuth.objects.get(user=self.user, is_active=True)
        except GmailAuth.DoesNotExist:
            self.gmail_auth = None
    
    def is_authenticated(self) -> bool:
        """Check if user has valid Gmail authentication"""
        if not self.gmail_auth:
            return False
        
        # Check if token is expired and needs refresh
        if self.gmail_auth.needs_refresh():
            return self._refresh_token()
        
        return True
    
    def _refresh_token(self) -> bool:
        """Refresh the access token"""
        try:
            credentials = Credentials(
                token=self.gmail_auth.access_token,
                refresh_token=self.gmail_auth.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
                scopes=self.SCOPES
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            # Update the stored tokens
            self.gmail_auth.access_token = credentials.token
            self.gmail_auth.token_expiry = timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp())
            self.gmail_auth.save()
            
            return True
            
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def _get_gmail_service(self):
        """Get Gmail API service instance"""
        if not self.is_authenticated():
            raise Exception("Gmail not authenticated")
        
        credentials = Credentials(
            token=self.gmail_auth.access_token,
            refresh_token=self.gmail_auth.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            scopes=self.SCOPES
        )
        
        return build('gmail', 'v1', credentials=credentials)
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   attachment_path: Optional[str] = None, 
                   attachment_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email via Gmail API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            attachment_path: Path to attachment file
            attachment_name: Name for the attachment
            
        Returns:
            Dict with success status and message ID or error
        """
        try:
            service = self._get_gmail_service()
            
            # Create message
            message = MIMEMultipart()
            message['to'] = to_email
            message['from'] = self.gmail_auth.gmail_address
            message['subject'] = subject
            
            # Add body
            if '<html>' in body.lower():
                # HTML content
                text_part = MIMEText(body, 'html')
            else:
                # Plain text content
                text_part = MIMEText(body, 'plain')
            
            message.attach(text_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_name or os.path.basename(attachment_path)}'
                )
                message.attach(part)
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the message
            sent_message = service.users().messages().send(
                userId='me', 
                body={'raw': raw_message}
            ).execute()
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId')
            }
            
        except HttpError as error:
            print(f"Gmail API error: {error}")
            return {
                'success': False,
                'error': f"Gmail API error: {error}"
            }
        except Exception as e:
            print(f"Error sending email: {e}")
            return {
                'success': False,
                'error': f"Error sending email: {str(e)}"
            }
    
    def get_user_info(self) -> Optional[Dict[str, str]]:
        """Get user's Gmail profile information"""
        try:
            service = self._get_gmail_service()
            profile = service.users().getProfile(userId='me').execute()
            
            return {
                'email': profile['emailAddress'],
                'name': profile.get('name', ''),
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0)
            }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
    
    def get_user_info_with_credentials(self, credentials: Credentials) -> Optional[Dict[str, str]]:
        """Get user's Gmail profile information using provided credentials"""
        try:
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            
            return {
                'email': profile['emailAddress'],
                'name': profile.get('name', ''),
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0)
            }
        except Exception as e:
            print(f"Error getting user info with credentials: {e}")
            return None
    
    def revoke_access(self) -> bool:
        """Revoke Gmail access for the user"""
        try:
            if self.gmail_auth:
                self.gmail_auth.is_active = False
                self.gmail_auth.save()
                return True
            return False
        except Exception as e:
            print(f"Error revoking access: {e}")
            return False


def create_gmail_auth_from_credentials(user, credentials: Credentials, gmail_address: str) -> GmailAuth:
    """Create GmailAuth instance from OAuth2 credentials"""
    gmail_auth, created = GmailAuth.objects.get_or_create(
        user=user,
        defaults={
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp()),
            'gmail_address': gmail_address,
            'is_active': True
        }
    )
    
    if not created:
        # Update existing record
        gmail_auth.access_token = credentials.token
        gmail_auth.refresh_token = credentials.refresh_token
        gmail_auth.token_expiry = timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp())
        gmail_auth.gmail_address = gmail_address
        gmail_auth.is_active = True
        gmail_auth.save()
    
    return gmail_auth 