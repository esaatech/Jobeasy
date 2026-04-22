from django.db import models
from django.conf import settings
from django.utils import timezone
import os


def resume_pdf_path(instance, filename):
    """Generate a unique path for resume PDF files"""
    # Get file extension
    ext = os.path.splitext(filename)[1]
    # Create a unique filename with timestamp
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f'resumes/{instance.user.id}/resume_{timestamp}{ext}'


class ResumeTemplate(models.Model):
    template_id = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    role_label = models.CharField(max_length=100, blank=True, default="")
    short_label = models.CharField(max_length=120, blank=True, default="")
    features = models.JSONField(default=list, blank=True)
    thumbnail_static = models.CharField(max_length=255, blank=True, default="")
    selection_gradient = models.CharField(max_length=120, blank=True, default="")
    selection_title_class = models.CharField(max_length=120, blank=True, default="")
    featured = models.BooleanField(default=False)
    featured_rank = models.PositiveIntegerField(default=999)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["featured_rank", "name"]

    def __str__(self):
        return f"{self.name} ({self.template_id})"


class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    name = models.CharField(max_length=100, default='My Resume')
    draft = models.BooleanField(default=True)
    pdf_file = models.FileField(
        upload_to=resume_pdf_path,
        null=True,
        blank=True
    )
    template_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
   
    # Content fields with default values
    original_content = models.TextField(default='')
    optimized_content = models.TextField(default='')
    job_description = models.TextField(default='')
    
    # Structured data for created resumes
    personal_info = models.JSONField(default=dict, blank=True)
    experience = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=dict, blank=True)
    additional = models.JSONField(default=dict, blank=True)
    relevant_experience = models.JSONField(default=list, blank=True, null=True)
    
    # Optimization results with default values
    keyword_matches = models.JSONField(default=list)
    improvement_suggestions = models.JSONField(default=list)
    ats_score = models.IntegerField(default=0)
    is_optimized = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = " (Draft)" if self.draft else ""
        return f"{self.name}{status} - {self.user.username}"

    def save(self, *args, **kwargs):
        # If this is an update and there's an existing file, delete it
        if self.pk:
            try:
                old_instance = Resume.objects.get(pk=self.pk)
                if old_instance.pdf_file and self.pdf_file != old_instance.pdf_file:
                    old_instance.pdf_file.delete(save=False)
            except Resume.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete the file when the model instance is deleted
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)
