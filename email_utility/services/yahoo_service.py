import base64
import json
import logging
import mimetypes
import os
import smtplib
from datetime import timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.utils import timezone

from ..models import YahooAuth
from .gmail_service import normalize_attachment_filename

logger = logging.getLogger(__name__)


class YahooService:
    AUTHORIZE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
    TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
    USERINFO_URL = "https://api.login.yahoo.com/openid/v1/userinfo"
    SMTP_HOST = "smtp.mail.yahoo.com"
    SMTP_PORT = 587
    # Keep Yahoo scopes minimal to avoid invalid_scope errors unless extra permissions are
    # explicitly enabled for the app in Yahoo Developer Console.
    SCOPES = ["openid", "email"]

    def __init__(self, user):
        self.user = user
        self.yahoo_auth = None
        self._load_yahoo_auth()

    def _load_yahoo_auth(self):
        try:
            self.yahoo_auth = YahooAuth.objects.get(user=self.user, is_active=True)
        except YahooAuth.DoesNotExist:
            self.yahoo_auth = None

    @staticmethod
    def _build_basic_auth_header() -> str:
        client_id = os.getenv("YAHOO_CLIENT_ID", "")
        client_secret = os.getenv("YAHOO_CLIENT_SECRET", "")
        token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
        return f"Basic {token}"

    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        params = {
            "client_id": os.getenv("YAHOO_CLIENT_ID"),
            "redirect_uri": os.getenv("YAHOO_REDIRECT_URI"),
            "response_type": "code",
            "scope": " ".join(cls.SCOPES),
            "state": state,
        }
        return f"{cls.AUTHORIZE_URL}?{urlencode(params)}"

    @classmethod
    def exchange_code_for_tokens(cls, code: str) -> Dict[str, Any]:
        payload = urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.getenv("YAHOO_REDIRECT_URI"),
            }
        ).encode("utf-8")
        req = Request(
            cls.TOKEN_URL,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": cls._build_basic_auth_header(),
            },
        )
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        payload = urlencode(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        ).encode("utf-8")
        req = Request(
            cls.TOKEN_URL,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": cls._build_basic_auth_header(),
            },
        )
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    @classmethod
    def fetch_user_info(cls, access_token: str) -> Optional[Dict[str, Any]]:
        req = Request(
            cls.USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            method="GET",
        )
        try:
            with urlopen(req, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.exception("Failed to fetch Yahoo user info: %s", exc)
            return None

    @staticmethod
    def _token_expiry_from_payload(token_payload: Dict[str, Any]):
        expires_in = int(token_payload.get("expires_in", 3600))
        return timezone.now() + timedelta(seconds=max(expires_in - 60, 60))

    def is_authenticated(self) -> bool:
        if not self.yahoo_auth:
            return False
        if self.yahoo_auth.is_token_expired() or self.yahoo_auth.needs_refresh():
            return self._refresh_token()
        return True

    def _refresh_token(self) -> bool:
        try:
            token_payload = self.refresh_access_token(self.yahoo_auth.refresh_token)
            self.yahoo_auth.access_token = token_payload["access_token"]
            if token_payload.get("refresh_token"):
                self.yahoo_auth.refresh_token = token_payload["refresh_token"]
            self.yahoo_auth.token_expiry = self._token_expiry_from_payload(token_payload)
            self.yahoo_auth.save()
            return True
        except Exception as exc:
            logger.exception("Error refreshing Yahoo token for user_id=%s: %s", self.user.pk, exc)
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        attachment_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.is_authenticated():
            return {"success": False, "error": "Yahoo account not connected or token expired."}

        try:
            message = MIMEMultipart()
            message["to"] = to_email
            message["from"] = self.yahoo_auth.yahoo_address
            message["subject"] = subject
            subtype = "html" if "<html>" in body.lower() else "plain"
            message.attach(MIMEText(body, subtype))

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    file_bytes = f.read()
                mime_type, _ = mimetypes.guess_type(attachment_path)
                part = MIMEApplication(file_bytes, _subtype="pdf" if mime_type == "application/pdf" else "octet-stream")
                safe_name = normalize_attachment_filename(attachment_name, attachment_path)
                part.add_header("Content-Disposition", "attachment", filename=safe_name)
                message.attach(part)

            auth_string = f"user={self.yahoo_auth.yahoo_address}\x01auth=Bearer {self.yahoo_auth.access_token}\x01\x01"
            auth_b64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

            with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT, timeout=20) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                code, resp = smtp.docmd("AUTH", "XOAUTH2 " + auth_b64)
                if code != 235:
                    return {"success": False, "error": f"Yahoo SMTP auth failed: {resp.decode('utf-8', errors='ignore')}"}
                smtp.sendmail(self.yahoo_auth.yahoo_address, [to_email], message.as_string())

            return {"success": True, "message_id": None, "thread_id": None}
        except Exception as exc:
            logger.exception("Error sending Yahoo email for user_id=%s: %s", self.user.pk, exc)
            return {"success": False, "error": f"Yahoo send failed: {str(exc)}"}

    def revoke_access(self) -> bool:
        if not self.yahoo_auth:
            return False
        self.yahoo_auth.is_active = False
        self.yahoo_auth.save(update_fields=["is_active", "updated_at"])
        return True


def create_yahoo_auth_from_token_payload(user, token_payload: Dict[str, Any], yahoo_address: str) -> YahooAuth:
    yahoo_auth, created = YahooAuth.objects.get_or_create(
        user=user,
        defaults={
            "access_token": token_payload["access_token"],
            "refresh_token": token_payload.get("refresh_token", ""),
            "token_expiry": YahooService._token_expiry_from_payload(token_payload),
            "yahoo_address": yahoo_address,
            "is_active": True,
        },
    )

    if not created:
        yahoo_auth.access_token = token_payload["access_token"]
        if token_payload.get("refresh_token"):
            yahoo_auth.refresh_token = token_payload["refresh_token"]
        yahoo_auth.token_expiry = YahooService._token_expiry_from_payload(token_payload)
        yahoo_auth.yahoo_address = yahoo_address
        yahoo_auth.is_active = True
        yahoo_auth.save()
    return yahoo_auth
