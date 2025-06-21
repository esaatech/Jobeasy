from django_mailbox.models import Mailbox
from ..base import EmailProvider
import imaplib

class GmailProvider(EmailProvider):
    def __init__(self, config=None):
        self.mailbox = None
        self.config = config
        
    def test_credentials(self, email, password):
        """Test Gmail credentials before saving"""
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(email, password)
            imap.logout()
            return True, None
        except imaplib.IMAP4.error:
            return False, "Invalid Gmail credentials. Please ensure you are using an App Password if 2-factor authentication is enabled."
        except Exception as e:
            return False, f"Connection error: {str(e)}"
            
    def connect(self):
        """Connect to Gmail using user's credentials from database"""
        if not self.config:
            raise ValueError("Email configuration is required")

        try:
            email = self.config.email
            password = self.config.credentials.get('password')
            
            if not email or not password:
                raise ValueError("Email or password missing from configuration")

            self.mailbox = Mailbox.objects.get_or_create(
                name=f'Gmail-{self.config.user.username}',
                uri=f'imap+ssl://{email}:{password}@imap.gmail.com',
                defaults={'active': True}
            )[0]
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Gmail: {str(e)}")
            
    def get_messages(self, limit=10):
        """Get recent messages"""
        if not self.mailbox:
            self.connect()
        return self.mailbox.messages.all().order_by('-processed')[:limit]
    
    def send_message(self, to, subject, body):
        """Send email through Gmail"""
        # Implement sending logic here
        pass 