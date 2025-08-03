from django.db import models
from django.conf import settings
from resume_builder.models import Resume

# Create your models here.

class JobApplication(models.Model):
    """
    DASHBOARD JobApplication Model
    
    This model is used for manually created job applications through the dashboard's
    job application generator feature. It's different from job_service.models.JobApplication.
    
    Key Differences from job_service JobApplication:
    - Purpose: Manual job application creation (not tracking applications to scraped jobs)
    - Job Reference: Uses 'job_name' (string) instead of ForeignKey to Job model
    - Cover Letter: Uses ForeignKey to CoverLetter model (not TextField)
    - Resume: Uses ForeignKey to Resume model (same as job_service)
    - Status: Simple processing/completed/failed (not detailed application tracking)
    - Related Name: 'dashboard_job_applications' (to avoid conflicts)
    
    Usage: When users generate job applications through the dashboard interface
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_job_applications')
    cover_letter = models.ForeignKey('coverletter.CoverLetter', on_delete=models.SET_NULL, null=True, blank=True, related_name='job_applications')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_applications')
    job_name = models.CharField(max_length=255)
    email_subject = models.CharField(max_length=200, blank=True, null=True, help_text="AI-generated email subject line")
    created_at = models.DateTimeField(auto_now_add=True)
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
