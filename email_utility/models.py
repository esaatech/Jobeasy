from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

class EmailLog(models.Model):
    """
    Simple model to log email sending activities
    """
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"
    
    def __str__(self):
        return f"{self.recipient} - {self.subject} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"





