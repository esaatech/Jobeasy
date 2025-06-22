from django.db import models
from django.conf import settings

# Create your models here.

class JobApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_job_applications')
    job_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    resume_link = models.URLField(blank=True, null=True)
    cover_letter_link = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed')
        ],
        default='processing'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dashboard Job Application'
        verbose_name_plural = 'Dashboard Job Applications'

    def __str__(self):
        return f"{self.job_name} - {self.user.username} ({self.created_at.strftime('%Y-%m-%d')})"
