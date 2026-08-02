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
