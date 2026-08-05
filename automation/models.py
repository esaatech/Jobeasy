from django.conf import settings
from django.db import models
from django.utils import timezone

# Free (pre-Ultimate) AI title-family generates per user. Manual edits are unlimited.
FREE_TITLE_FAMILY_AI_GENERATIONS = 2


class UltimateAutomationProfile(models.Model):
    """
    Auto-apply settings for a user (draft before Ultimate; active after).

    Stage 2 matching uses title family fields only (primary + related).
    exclude_titles is an optional hard reject list. Skills / JD quality
    are evaluated later by the AI fit gate (Stage 3).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ultimate_automation_profile',
    )
    primary_titles = models.JSONField(
        default=list,
        blank=True,
        help_text='Core target roles, e.g. ["Backend Engineer", "Software Engineer"]',
    )
    related_titles = models.JSONField(
        default=list,
        blank=True,
        help_text='Adjacent synonyms / related roles for Stage 2 soft match',
    )
    exclude_titles = models.JSONField(
        default=list,
        blank=True,
        help_text='Roles to never match, e.g. ["Data Scientist", "Engineering Manager"]',
    )
    default_resume = models.ForeignKey(
        'resume_builder.Resume',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ultimate_automation_profiles',
    )
    auto_apply_enabled = models.BooleanField(
        default=False,
        help_text='Requires Ultimate + confirmed title family',
    )
    title_family_confirmed = models.BooleanField(default=False)
    title_family_confirmed_at = models.DateTimeField(null=True, blank=True)
    title_family_ai_generations = models.PositiveIntegerField(
        default=0,
        help_text='Successful AI suggest-from-resume calls (free users capped)',
    )
    max_applications_per_day = models.PositiveIntegerField(default=10)

    # Job search preferences (wizard step 2 — mirrors job_service intake)
    SEARCH_PURPOSE_CHOICES = [
        ('career_growth', 'Career Growth & Advancement'),
        ('better_compensation', 'Better Compensation & Benefits'),
        ('work_life_balance', 'Better Work-Life Balance'),
        ('relocation', 'Relocation to New City/Country'),
        ('travel_opportunity', 'Travel & Work Abroad'),
        ('industry_change', 'Change of Industry'),
        ('company_culture', 'Better Company Culture'),
        ('remote_work', 'Remote Work Opportunities'),
        ('other', 'Other'),
    ]
    search_purpose = models.CharField(
        max_length=50,
        choices=SEARCH_PURPOSE_CHOICES,
        blank=True,
        help_text='Why the user is looking for roles',
    )
    other_purpose = models.TextField(blank=True)
    preferred_countries = models.JSONField(
        default=list,
        blank=True,
        help_text='Selected countries/states, e.g. [{"name":"Canada","cca2":"CA","states":["Ontario"]}]',
    )
    city = models.CharField(max_length=100, blank=True)
    distance_miles = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Preferred commute / search radius in miles',
    )
    work_arrangements = models.JSONField(
        default=list,
        blank=True,
        help_text='Preferred arrangements: remote, hybrid, onsite',
    )

    setup_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ultimate automation profile'
        verbose_name_plural = 'Ultimate automation profiles'

    def __str__(self):
        return f'Ultimate automation for {self.user.username}'

    @property
    def title_family(self) -> list[str]:
        """Titles used for Stage 2 matching (primary + related, deduped)."""
        seen = set()
        family = []
        for title in list(self.primary_titles or []) + list(self.related_titles or []):
            cleaned = (title or '').strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                family.append(cleaned)
        return family

    def mark_title_family_confirmed(self):
        self.title_family_confirmed = True
        self.title_family_confirmed_at = timezone.now()
        self.setup_completed = bool(self.primary_titles)
        self.save(
            update_fields=[
                'title_family_confirmed',
                'title_family_confirmed_at',
                'setup_completed',
                'updated_at',
            ]
        )


class ApplyTask(models.Model):
    """
    Phase 2a operator queue row: a matched job for an Ultimate user.

    Matcher creates status=queued with a snapshot of job.application_url.
    Operators open the URL, apply on the ATS, then mark applied/skipped.
    AI packet fields are deferred to Phase 2b.
    """

    STATUS_QUEUED = 'queued'
    STATUS_APPLIED = 'applied'
    STATUS_SKIPPED = 'skipped'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_APPLIED, 'Applied'),
        (STATUS_SKIPPED, 'Skipped'),
    ]

    SKIP_REASON_CHOICES = [
        ('captcha', 'CAPTCHA'),
        ('login_required', 'Login required'),
        ('job_closed', 'Job closed'),
        ('geo_block', 'Geo blocked'),
        ('email_only', 'Email-only apply'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apply_tasks',
    )
    job = models.ForeignKey(
        'job_service.Job',
        on_delete=models.CASCADE,
        related_name='apply_tasks',
    )
    application_url = models.URLField(
        max_length=500,
        help_text='Snapshot of job.application_url at match time',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_QUEUED,
        db_index=True,
    )
    skip_reason = models.CharField(
        max_length=50,
        choices=SKIP_REASON_CHOICES,
        blank=True,
    )
    operator_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Apply task'
        verbose_name_plural = 'Apply tasks'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'job'],
                name='unique_apply_task_user_job',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.job} [{self.status}]'

    def mark_applied(self, *, notes: str = ''):
        self.status = self.STATUS_APPLIED
        self.applied_at = timezone.now()
        if notes:
            self.operator_notes = notes
        self.save(
            update_fields=['status', 'applied_at', 'operator_notes', 'updated_at']
        )

    def mark_skipped(self, *, reason: str = 'other', notes: str = ''):
        self.status = self.STATUS_SKIPPED
        self.skip_reason = reason or 'other'
        if notes:
            self.operator_notes = notes
        self.save(
            update_fields=['status', 'skip_reason', 'operator_notes', 'updated_at']
        )
