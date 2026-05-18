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


class ResumeJobEvaluation(models.Model):
    """
    Persisted Gemini evaluation run (production trail + admin playground).

    Each row captures inputs, optional prompt FK, structured JSON output, and status.
    """

    job_description = models.TextField()
    resume_text = models.TextField()
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resume_job_evaluations",
    )
    gemini_model = models.CharField(
        max_length=128,
        blank=True,
        help_text="Gemini model id used for this run.",
    )

    succeeded = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    overall_score = models.PositiveSmallIntegerField(null=True, blank=True)
    optimization_potential = models.PositiveSmallIntegerField(null=True, blank=True)
    recommendation = models.CharField(max_length=128, blank=True)
    instruction_slug = models.SlugField(
        max_length=80,
        blank=True,
        help_text="Snapshot of prompt_configuration.slug used for versioning.",
    )

    evaluation_json = models.JSONField(null=True, blank=True)
    raw_response_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Resume-job evaluation"
        verbose_name_plural = "Resume-job evaluations"

    def __str__(self) -> str:
        if self.pk is None:
            return "Evaluation (new)"
        no_run_yet = (
            self.evaluation_json is None
            and not (self.raw_response_text or "").strip()
            and not (self.error_message or "").strip()
        )
        if no_run_yet:
            return f"Evaluation {self.pk} [draft] {self.recommendation or ''}".strip()
        status = "ok" if self.succeeded else "fail"
        return f"Evaluation {self.pk} [{status}] {self.recommendation or ''}".strip()
