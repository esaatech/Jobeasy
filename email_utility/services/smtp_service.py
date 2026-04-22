import logging
import smtplib
from typing import Dict, Any, Optional

from django.core.mail import EmailMessage, get_connection

from ..models import SMTPAccount

logger = logging.getLogger(__name__)


class SMTPService:
    """SMTP sender for user-connected provider accounts."""

    SMTP_CONFIG = {
        SMTPAccount.PROVIDER_GMAIL: {"host": "smtp.gmail.com", "port": 587},
        SMTPAccount.PROVIDER_OUTLOOK: {"host": "smtp.office365.com", "port": 587},
        SMTPAccount.PROVIDER_YAHOO: {"host": "smtp.mail.yahoo.com", "port": 587},
    }

    def __init__(self, smtp_account: SMTPAccount):
        self.smtp_account = smtp_account

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        attachment_name: Optional[str] = None,
        is_html: bool = False,
    ) -> Dict[str, Any]:
        provider_cfg = self.SMTP_CONFIG.get(self.smtp_account.provider)
        if not provider_cfg:
            return {"success": False, "error": "Unsupported SMTP provider"}

        try:
            connection = get_connection(
                host=provider_cfg["host"],
                port=provider_cfg["port"],
                username=self.smtp_account.email_address,
                password=self.smtp_account.app_password,
                use_tls=True,
            )
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=self.smtp_account.email_address,
                to=[to_email],
                connection=connection,
            )
            if is_html:
                email.content_subtype = "html"

            if attachment_path:
                email.attach_file(attachment_path, mimetype="application/pdf")
                if attachment_name:
                    # Django uses file basename for display; this retains user intent where possible.
                    email.extra_headers = {"X-Attachment-Name": attachment_name}

            email.send(fail_silently=False)
            return {"success": True, "message_id": None, "thread_id": None}
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Authentication failed. Please verify your app password and reconnect this account.",
            }
        except Exception as exc:
            logger.exception("Error sending email via SMTP account_id=%s: %s", self.smtp_account.id, exc)
            return {"success": False, "error": f"SMTP error: {str(exc)}"}
