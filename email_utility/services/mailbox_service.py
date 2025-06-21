from django.core.paginator import Paginator
from django_mailbox.models import Message, Mailbox
from ..models import MailboxConfiguration, UserEmailConfiguration
from typing import Optional, List, Dict, Any
import logging
from django.utils import timezone
import email
from datetime import datetime, timedelta
from imaplib import IMAP4, IMAP4_SSL

logger = logging.getLogger(__name__)

class MailboxService:
    """Service for handling mailbox operations"""
    
    def __init__(self, email_config: UserEmailConfiguration):
        """
        Initialize mailbox service with user's email configuration
        """
        self.email_config = email_config
        self.mailbox_config = self._get_or_create_mailbox_config()
        
    def _get_or_create_mailbox_config(self) -> MailboxConfiguration:
        """Get existing or create new mailbox configuration"""
        try:
            # First try to get existing config
            return MailboxConfiguration.objects.get(
                email_config=self.email_config
            )
        except MailboxConfiguration.DoesNotExist:
            # Create mailbox first
            mailbox = Mailbox.objects.create(
                name=self.email_config.email,
                uri=self._build_uri(self.email_config),
                active=True
            )
            
            # Then create mailbox configuration
            mailbox_config = MailboxConfiguration.objects.create(
                email_config=self.email_config,
                mailbox=mailbox  # Add the mailbox here
            )
            return mailbox_config

    def _build_uri(self, config) -> str:
        """Build the mailbox URI based on provider type and credentials"""
        # Get password from credentials JSON field
        password = config.credentials.get('password')
        
        if not password:
            raise ValueError("Password not found in credentials")
        
        if config.provider_type == 'gmail':
            return f'imap+ssl://{ config.email }:{ password }@imap.gmail.com'
        elif config.provider_type == 'outlook':
            return f'imap+ssl://{ config.email }:{ password }@outlook.office365.com'
        # Add more providers as needed
        return None
    
    def get_messages(self, 
                    folder: str = 'inbox', 
                    page: int = 1, 
                    per_page: int = 25) -> Dict[str, Any]:
        """
        Get messages from specified folder with pagination
        """
        try:
            # Validate folder
            if not self.mailbox_config.is_valid_folder(folder):
                raise ValueError(f"Invalid folder: {folder}")
            
            # Get messages based on folder
            if folder.lower() == 'sent':
                messages = Message.objects.filter(
                    mailbox=self.mailbox_config.mailbox,
                    outgoing=True
                ).order_by('-processed')
            else:
                messages = Message.objects.filter(
                    mailbox=self.mailbox_config.mailbox,
                    outgoing=False
                ).order_by('-processed')
            
            # Paginate results
            paginator = Paginator(messages, per_page)
            page_obj = paginator.get_page(page)
            
            return {
                'messages': page_obj,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            raise
    
    def get_message(self, message_id: int) -> Optional[Message]:
        """
        Get single message details
        """
        try:
            return Message.objects.get(
                id=message_id,
                mailbox=self.mailbox_config.mailbox
            )
        except Message.DoesNotExist:
            logger.warning(f"Message not found: {message_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {str(e)}")
            raise
    
    def get_folders(self) -> Dict[str, str]:
        """
        Get all available folders
        """
        try:
            return self.mailbox_config.folders
        except Exception as e:
            logger.error(f"Error fetching folders: {str(e)}")
            return {}
    
    def sync_messages(self) -> bool:
        """
        Trigger manual sync of messages
        """
        try:
            self.mailbox_config.mailbox.get_connection()
            self.mailbox_config.mailbox.sync()
            self.mailbox_config.last_sync = timezone.now()
            self.mailbox_config.save()
            return True
        except Exception as e:
            logger.error(f"Error syncing messages: {str(e)}")
            return False

    def sync_recent_messages(self, limit=5):
        """
        Sync only the most recent messages
        Args:
            limit: Number of recent messages to fetch
        """
        try:
            mailbox = self.mailbox_config.mailbox
            transport = mailbox.get_connection()
            
            # Get the actual IMAP connection from the transport
            if hasattr(transport, 'server'):
                imap = transport.server
            else:
                # Create IMAP connection based on provider
                if self.email_config.provider_type == 'gmail':
                    imap = IMAP4_SSL('imap.gmail.com')
                    imap.login(self.email_config.email, self.email_config.credentials.get('password'))
            
            print(f"Connecting to mailbox: {mailbox.name}")
            
            # Select INBOX and print status
            status, messages = imap.select('INBOX')
            print(f"INBOX Status: {status}, Message Count: {messages[0].decode()}")
            
            # Search for all messages
            result, data = imap.search(None, 'ALL')
            email_ids = data[0].split()
            print(f"Total emails found: {len(email_ids)}")
            
            # Get the last few messages
            recent_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            print(f"Fetching {len(recent_ids)} recent messages")
            
            messages_created = 0
            for email_id in recent_ids:
                try:
                    # Fetch email data
                    result, data = imap.fetch(email_id, '(RFC822)')
                    if not data or not data[0]:
                        print(f"No data for email ID: {email_id}")
                        continue
                        
                    email_body = data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Get message ID or create one if not present
                    message_id = email_message.get('Message-ID', f'generated-{email_id.decode()}')
                    
                    # Create Message object
                    Message.objects.create(
                        mailbox=mailbox,
                        message_id=message_id,
                        subject=email_message.get('Subject', '(No Subject)'),
                        from_header=email_message.get('From', ''),
                        to_header=email_message.get('To', ''),
                        body=self._get_email_body(email_message),
                        processed=timezone.now()
                    )
                    messages_created += 1
                    print(f"Created message {messages_created}: {email_message.get('Subject', '(No Subject)')}")
                    
                except Exception as e:
                    print(f"Error processing email {email_id}: {str(e)}")
                    continue
            
            # Close the connection
            imap.close()
            imap.logout()
            
            # Update last sync time
            self.mailbox_config.last_sync = timezone.now()
            self.mailbox_config.save()
            
            print(f"Sync complete. Created {messages_created} messages")
            return messages_created
            
        except Exception as e:
            print(f"Error in sync_recent_messages: {str(e)}")
            raise
    
    def _get_email_body(self, email_message):
        """Extract email body from message"""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return email_message.get_payload(decode=True).decode()
        return ""
