from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Create your models here.


class AIModel(models.Model):
    """Catalog of provider model ids (e.g. Gemini 2.5 Flash) for prompts and runs."""

    class Provider(models.TextChoices):
        GEMINI = "gemini", "Google Gemini"
        OPENAI = "openai", "OpenAI"
        DEEPSEEK = "deepseek", "DeepSeek"

    provider = models.CharField(
        max_length=32,
        choices=Provider.choices,
        default=Provider.GEMINI,
    )
    model_id = models.CharField(
        max_length=128,
        help_text="API model id (e.g. gemini-2.5-flash).",
    )
    display_name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive models are hidden from admin dropdowns.",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    default_temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Suggested default when a prompt does not set temperature.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "display_name"]
        verbose_name = "AI model"
        verbose_name_plural = "AI models"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "model_id"],
                name="ai_service_aimodel_provider_model_id_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.model_id})"


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
    ai_model = models.ForeignKey(
        AIModel,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="prompt_configurations",
        help_text="Default model for runs using this prompt variant.",
    )
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Sampling temperature for this prompt (0–2). Leave blank to use the model or env default.",
    )
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
            AIPromptConfiguration.objects.filter(
                service=self.service,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


DASHBOARD_DEFAULT_EVAL_PROMPT_SLUG = "default-job-evaluation"


class JobFitGateSettings(models.Model):
    """
    Singleton configuration for dashboard pre-flight job-fit gating.

    One row (pk=1). Edit in admin; seeded by setup_job_fit_gate on deploy.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    is_enabled = models.BooleanField(
        default=True,
        help_text="When off, dashboard skips evaluation and uses the legacy generate flow.",
    )
    green_min_score = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Scores at or above this (with Good/Strong recommendation) auto-proceed.",
    )
    yellow_min_score = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Scores below green_min but at or above this require user confirmation.",
    )
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="job_fit_gate_settings",
        help_text="Evaluator prompt used for dashboard fit checks.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Job fit gate settings"
        verbose_name_plural = "Job fit gate settings"

    def save(self, *args, **kwargs):
        self.id = 1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        state = "on" if self.is_enabled else "off"
        return f"Job fit gate ({state}, green≥{self.green_min_score})"


class ResumeJobEvaluation(models.Model):
    """
    Persisted Gemini evaluation run (production trail + admin playground).

    Each row captures inputs, optional prompt FK, structured JSON output, and status.
    """

    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short label for this run (e.g. “Trend Micro Pro” or “Test resume v2”).",
    )
    description = models.TextField(
        blank=True,
        help_text="What you are testing—resume variant, model comparison, job source, etc.",
    )
    conclusion = models.TextField(
        blank=True,
        help_text="Summary verdict; auto-filled from proceed_reasoning after a successful evaluation.",
    )

    user = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="resume_job_evaluations",
    )
    resume = models.ForeignKey(
        "resume_builder.Resume",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resume_job_evaluations",
    )
    job_application = models.ForeignKey(
        "dashboard.JobApplication",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fit_evaluations",
    )

    job_description = models.TextField()
    resume_text = models.TextField()
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resume_job_evaluations",
    )
    ai_model = models.ForeignKey(
        AIModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resume_job_evaluations",
        help_text="Model catalog row used for this run.",
    )
    gemini_model = models.CharField(
        max_length=128,
        blank=True,
        help_text="Gemini model id used for this run (snapshot).",
    )
    temperature_used = models.FloatField(
        null=True,
        blank=True,
        help_text="Temperature used for this run.",
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
        label = (self.name or "").strip()
        if self.pk is None:
            return label or "Evaluation (new)"
        if label:
            if self.recommendation:
                return f"{label} — {self.recommendation}"
            return label
        no_run_yet = (
            self.evaluation_json is None
            and not (self.raw_response_text or "").strip()
            and not (self.error_message or "").strip()
        )
        if no_run_yet:
            return f"Evaluation {self.pk} [draft] {self.recommendation or ''}".strip()
        status = "ok" if self.succeeded else "fail"
        return f"Evaluation {self.pk} [{status}] {self.recommendation or ''}".strip()


class WhyShouldIApplyPlayground(models.Model):
    """
    Admin playground for "Why should we hire you?" application answers.

    Mirrors ResumeJobEvaluation: test prompt variants with JD + resume inputs
    before wiring dashboard generation.
    """

    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short label for this run (e.g. “Acme PM role test”).",
    )
    description = models.TextField(
        blank=True,
        help_text="What you are testing—prompt version, resume variant, job source, etc.",
    )

    user = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="why_should_i_apply_playgrounds",
    )
    resume = models.ForeignKey(
        "resume_builder.Resume",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="why_should_i_apply_playgrounds",
    )
    job_application = models.ForeignKey(
        "dashboard.JobApplication",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="why_should_i_apply_playgrounds",
    )

    job_description = models.TextField()
    resume_text = models.TextField()
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="why_should_i_apply_playgrounds",
    )
    ai_model = models.ForeignKey(
        AIModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="why_should_i_apply_playgrounds",
        help_text="Model catalog row used for this run.",
    )
    gemini_model = models.CharField(
        max_length=128,
        blank=True,
        help_text="Gemini model id used for this run (snapshot).",
    )
    temperature_used = models.FloatField(
        null=True,
        blank=True,
        help_text="Temperature used for this run.",
    )

    succeeded = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    answer_text = models.TextField(
        blank=True,
        help_text="Generated application answer (plain text, no letter framing).",
    )
    instruction_slug = models.SlugField(
        max_length=80,
        blank=True,
        help_text="Snapshot of prompt_configuration.slug used for versioning.",
    )

    raw_response_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Why should I apply playground"
        verbose_name_plural = "Why should I apply playground"

    def __str__(self) -> str:
        label = (self.name or "").strip()
        if self.pk is None:
            return label or "Playground (new)"
        if label:
            status = "ok" if self.succeeded else "fail" if self.error_message else "draft"
            return f"{label} [{status}]"
        no_run_yet = (
            not (self.answer_text or "").strip()
            and not (self.raw_response_text or "").strip()
            and not (self.error_message or "").strip()
        )
        if no_run_yet:
            return f"Playground {self.pk} [draft]"
        status = "ok" if self.succeeded else "fail"
        return f"Playground {self.pk} [{status}]"


class ProfessionalSummaryPlayground(models.Model):
    """
    Admin playground for AI professional summary generation.

    Mirrors WhyShouldIApplyPlayground: test prompt variants with resume text
    before or alongside dashboard wizard usage.
    """

    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short label for this run (e.g. “Upload v2 summary test”).",
    )
    description = models.TextField(
        blank=True,
        help_text="What you are testing—prompt version, resume variant, model comparison, etc.",
    )

    user = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="professional_summary_playgrounds",
    )
    resume = models.ForeignKey(
        "resume_builder.Resume",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="professional_summary_playgrounds",
    )

    resume_text = models.TextField(
        help_text="Resume content as plain text or structured JSON paste for testing.",
    )
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="professional_summary_playgrounds",
    )
    ai_model = models.ForeignKey(
        AIModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="professional_summary_playgrounds",
        help_text="Model catalog row used for this run.",
    )
    openai_model = models.CharField(
        max_length=128,
        blank=True,
        help_text="OpenAI model id used for this run (snapshot).",
    )
    temperature_used = models.FloatField(
        null=True,
        blank=True,
        help_text="Temperature used for this run.",
    )

    succeeded = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    summary_text = models.TextField(
        blank=True,
        help_text="Generated professional summary.",
    )
    instruction_slug = models.SlugField(
        max_length=80,
        blank=True,
        help_text="Snapshot of prompt_configuration.slug used for versioning.",
    )

    raw_response_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Professional summary playground"
        verbose_name_plural = "Professional summary playground"

    def __str__(self) -> str:
        label = (self.name or "").strip()
        if self.pk is None:
            return label or "Summary playground (new)"
        if label:
            status = "ok" if self.succeeded else "fail" if self.error_message else "draft"
            return f"{label} [{status}]"
        no_run_yet = (
            not (self.summary_text or "").strip()
            and not (self.raw_response_text or "").strip()
            and not (self.error_message or "").strip()
        )
        if no_run_yet:
            return f"Summary playground {self.pk} [draft]"
        status = "ok" if self.succeeded else "fail"
        return f"Summary playground {self.pk} [{status}]"


class WhyShouldIApplyAnswer(models.Model):
    """User-facing persisted answer for a dashboard job application."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="why_should_i_apply_answers",
    )
    content = models.TextField(
        blank=True,
        help_text="Plain application answer (no greeting or sign-off).",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    error_message = models.TextField(blank=True)
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="why_should_i_apply_answers",
    )
    instruction_slug = models.SlugField(max_length=80, blank=True)
    gemini_model = models.CharField(max_length=128, blank=True)
    temperature_used = models.FloatField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Why should I apply answer"
        verbose_name_plural = "Why should I apply answers"

    def __str__(self) -> str:
        label = (self.content or "").strip()[:60]
        if label:
            return f"Answer ({self.get_status_display()}): {label}…"
        return f"Answer ({self.get_status_display()})"


class CoverLetterPlayground(models.Model):
    """Admin playground for cover letter generation (prompt + model testing)."""

    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short label for this run (e.g. “Acme SWE cover letter test”).",
    )
    description = models.TextField(
        blank=True,
        help_text="What you are testing—prompt variant, resume source, model comparison, etc.",
    )

    user = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="cover_letter_playgrounds",
    )
    resume = models.ForeignKey(
        "resume_builder.Resume",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cover_letter_playgrounds",
    )

    job_description = models.TextField()
    resume_text = models.TextField()
    prompt_config = models.ForeignKey(
        AIPromptConfiguration,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cover_letter_playgrounds",
    )
    ai_model = models.ForeignKey(
        AIModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cover_letter_playgrounds",
        help_text="Model catalog row used for this run.",
    )
    model_used = models.CharField(
        max_length=128,
        blank=True,
        help_text="Model id snapshot from the last run.",
    )
    temperature_used = models.FloatField(
        null=True,
        blank=True,
        help_text="Temperature used for this run.",
    )

    succeeded = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    title = models.CharField(max_length=512, blank=True)
    email_subject = models.CharField(max_length=512, blank=True)
    cover_letter_text = models.TextField(
        blank=True,
        help_text="Generated cover letter body.",
    )
    instruction_slug = models.SlugField(
        max_length=80,
        blank=True,
        help_text="Snapshot of prompt_configuration.slug used for versioning.",
    )

    raw_response_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cover letter playground"
        verbose_name_plural = "Cover letter playground"

    def __str__(self) -> str:
        label = (self.name or "").strip()
        if self.pk is None:
            return label or "Cover letter playground (new)"
        if label:
            status = "ok" if self.succeeded else "fail" if self.error_message else "draft"
            return f"{label} [{status}]"
        no_run_yet = (
            not (self.cover_letter_text or "").strip()
            and not (self.raw_response_text or "").strip()
            and not (self.error_message or "").strip()
        )
        if no_run_yet:
            return f"Cover letter playground {self.pk} [draft]"
        status = "ok" if self.succeeded else "fail"
        return f"Cover letter playground {self.pk} [{status}]"
