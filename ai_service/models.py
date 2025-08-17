from django.db import models

# Create your models here.

class AIService(models.Model):
    """Model for defining AI services that can have configurable prompts."""
    name = models.CharField(max_length=100, unique=True, help_text="Human-readable name for the AI service")
    slug = models.SlugField(max_length=50, unique=True, help_text="Used in code to identify this service (e.g., 'cover_letter', 'resume_optimization')")

    description = models.TextField(blank=True, help_text="Description of what this AI service does")
    is_active = models.BooleanField(default=True, help_text="Whether this service is currently available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "AI Service"
        verbose_name_plural = "AI Services"
    
    def __str__(self):
        return self.name
    
    def get_default_prompt(self):
        """Get the default prompt for this service."""
        return self.prompts.filter(is_default=True, is_active=True).first()


class AIPromptConfiguration(models.Model):
    """Model for managing AI system prompts per service."""
    service = models.ForeignKey(AIService, on_delete=models.CASCADE, related_name='prompts', help_text="The AI service this prompt belongs to")

    name = models.CharField(max_length=100, help_text="Human-readable name for this prompt variant")
    slug = models.SlugField(max_length=50, help_text="Used in code to identify this prompt variant (e.g., 'default', 'with_email_subject')")

    system_prompt = models.TextField(help_text="The system prompt that will be sent to the AI")
    is_active = models.BooleanField(default=True, help_text="Whether this prompt is currently active")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default prompt for this service")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['service', 'slug']
        ordering = ['service', 'name']
        verbose_name = "AI Prompt Configuration"
        verbose_name_plural = "AI Prompt Configurations"
    
    def __str__(self):
        return f"{self.service.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Ensure only one default prompt per service."""
        if self.is_default:
            # Set all other prompts for this service to not default
            AIPromptConfiguration.objects.filter(
                service=self.service,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
