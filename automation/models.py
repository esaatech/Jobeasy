from django.conf import settings
from django.db import models
from django.utils import timezone


class UltimateAutomationProfile(models.Model):
    """
    Ultimate-plan auto-apply settings for a user.

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
        help_text='User must confirm title family before enabling',
    )
    title_family_confirmed = models.BooleanField(default=False)
    title_family_confirmed_at = models.DateTimeField(null=True, blank=True)
    max_applications_per_day = models.PositiveIntegerField(default=10)
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
