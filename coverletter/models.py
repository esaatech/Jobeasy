from django.db import models
from django.conf import settings

# Create your models here.

class CoverLetter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cover_letters')
    title = models.CharField(max_length=200, default='Cover Letter')
    content = models.TextField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')
    error_message = models.TextField(blank=True, null=True)
    processing_time = models.FloatField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cover Letter for {self.user.username} created on {self.generated_at.strftime('%Y-%m-%d')}"
