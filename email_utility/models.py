from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class GmailAuth(models.Model):
    """Store Gmail OAuth2 tokens for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gmail_auth')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    gmail_address = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gmail Authentication"
        verbose_name_plural = "Gmail Authentications"

    def __str__(self):
        return f"{self.user.username} - {self.gmail_address}"

    def is_token_expired(self):
        """Check if the access token has expired"""
        return timezone.now() > self.token_expiry

    def needs_refresh(self):
        """Check if token needs refresh (expires within 5 minutes)"""
        return timezone.now() > (self.token_expiry - timezone.timedelta(minutes=5))


class YahooAuth(models.Model):
    """Store Yahoo OAuth2 tokens for users."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="yahoo_auth")
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    yahoo_address = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Yahoo Authentication"
        verbose_name_plural = "Yahoo Authentications"

    def __str__(self):
        return f"{self.user.username} - {self.yahoo_address}"

    def is_token_expired(self):
        return timezone.now() > self.token_expiry

    def needs_refresh(self):
        return timezone.now() > (self.token_expiry - timezone.timedelta(minutes=5))


class EmailHistory(models.Model):
    """Track email sending history"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]
    
    ATTACHMENT_TYPE_CHOICES = [
        ('resume', 'Resume'),
        ('cover_letter', 'Cover Letter'),
        ('job_application', 'Job Application'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_history')
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    attachment_type = models.CharField(max_length=50, choices=ATTACHMENT_TYPE_CHOICES)
    attachment_id = models.IntegerField()  # ID of resume or cover letter
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gmail_message_id = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Email History"
        verbose_name_plural = "Email History"
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.user.username} -> {self.recipient_email} ({self.status})"


class SMTPAccount(models.Model):
    """Store user-managed SMTP accounts for non-OAuth providers."""

    PROVIDER_GMAIL = "gmail"
    PROVIDER_OUTLOOK = "outlook"
    PROVIDER_YAHOO = "yahoo"
    PROVIDER_CHOICES = [
        (PROVIDER_GMAIL, "Gmail"),
        (PROVIDER_OUTLOOK, "Outlook"),
        (PROVIDER_YAHOO, "Yahoo Mail"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="smtp_accounts")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    email_address = models.EmailField()
    app_password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMTP Account"
        verbose_name_plural = "SMTP Accounts"
        ordering = ["-is_default", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "provider", "email_address"],
                name="unique_user_provider_email_account",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()} ({self.email_address})"




