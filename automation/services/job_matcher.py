"""Match scraped jobs to Ultimate users and create MatchedTask rows."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from django.db.models import F, Q
from django.utils import timezone

from automation.models import MatchedTask, UltimateAutomationProfile
from automation.services.eligibility import is_ultimate_subscriber
from job_service.models import Job, JobApplication

logger = logging.getLogger(__name__)

# Level markers: a job must not introduce these unless the matched user title has them.
_SENIORITY_PATTERNS = (
    (re.compile(r'\bstaff\s*\+\b'), 'staff+'),
    (re.compile(r'\bstaff\b'), 'staff'),
    (re.compile(r'\bprincipal\b'), 'principal'),
    (re.compile(r'\bdistinguished\b'), 'distinguished'),
    (re.compile(r'\bfellow\b'), 'fellow'),
    (re.compile(r'\bdirector\b'), 'director'),
    (re.compile(r'\bvp\b|\bvice\s+president\b'), 'vp'),
    (re.compile(r'\bhead\b'), 'head'),
    (re.compile(r'\bchief\b'), 'chief'),
    (re.compile(r'\blead\b'), 'lead'),
    (re.compile(r'\bsenior\b|\bsr\.?\b'), 'senior'),
    (re.compile(r'\bjunior\b|\bjr\.?\b'), 'junior'),
    (re.compile(r'\bmid[-\s]?level\b|\bmid\b'), 'mid'),
    (re.compile(r'\bentry[-\s]?level\b'), 'entry'),
)


@dataclass
class MatchUserResult:
    user_id: int
    username: str
    created: int = 0
    skipped_cap: bool = False
    skipped_ineligible: bool = False
    reason: str = ''
    created_tasks: list = field(default_factory=list)


@dataclass
class MatchCycleResult:
    users_considered: int = 0
    users_matched: int = 0
    tasks_created: int = 0
    per_user: list[MatchUserResult] = field(default_factory=list)
    created_tasks: list = field(default_factory=list)


def profile_is_match_ready(profile: UltimateAutomationProfile) -> tuple[bool, str]:
    if not profile.auto_apply_enabled:
        return False, 'auto_apply_disabled'
    if not profile.setup_completed and not profile.title_family_confirmed:
        return False, 'setup_incomplete'
    if not profile.title_family:
        return False, 'no_titles'
    if not is_ultimate_subscriber(profile.user):
        return False, 'not_ultimate'
    return True, ''


def seniority_tokens(title: str) -> frozenset[str]:
    text = (title or '').lower()
    found: set[str] = set()
    for pattern, label in _SENIORITY_PATTERNS:
        if pattern.search(text):
            found.add(label)
    # staff+ implies staff for comparison when user asked for staff+
    if 'staff+' in found:
        found.add('staff')
    return frozenset(found)


def _phrase_in_title(phrase: str, title_lower: str) -> bool:
    """True when phrase appears as whole words (not a loose substring)."""
    cleaned = (phrase or '').strip().lower()
    if not cleaned:
        return False
    pattern = r'(?<!\w)' + re.escape(cleaned).replace(r'\ ', r'\s+') + r'(?!\w)'
    return re.search(pattern, title_lower) is not None


def title_target_matches_job(target: str, job_title: str) -> bool:
    """
    Match one user title preference against a job title.

    - Phrase must appear with word boundaries.
    - Job must not add seniority the preference does not have
      (e.g. \"Software Engineer\" must not match \"Staff Software Engineer\").
    """
    title_lower = (job_title or '').lower()
    target_clean = (target or '').strip()
    if not target_clean or not title_lower:
        return False
    if not _phrase_in_title(target_clean, title_lower):
        return False
    extra = seniority_tokens(title_lower) - seniority_tokens(target_clean)
    return not extra


def title_matches(job: Job, profile: UltimateAutomationProfile) -> bool:
    title_lower = (job.title or '').lower()
    if not title_lower:
        return False

    for excluded in profile.exclude_titles or []:
        cleaned = (excluded or '').strip().lower()
        if cleaned and _phrase_in_title(cleaned, title_lower):
            return False

    return any(
        title_target_matches_job(target, job.title)
        for target in profile.title_family
        if target
    )


def work_arrangement_matches(job: Job, profile: UltimateAutomationProfile) -> bool:
    preferred = {
        (value or '').strip().lower()
        for value in (profile.work_arrangements or [])
        if (value or '').strip()
    }
    if not preferred:
        return True

    arrangement = (job.work_arrangement or 'unknown').lower()
    if arrangement == 'unknown':
        return False
    return arrangement in preferred


def _location_needles(profile: UltimateAutomationProfile) -> list[str]:
    needles: list[str] = []
    city = (profile.city or '').strip().lower()
    if city:
        needles.append(city)

    for entry in profile.preferred_countries or []:
        if isinstance(entry, dict):
            name = (entry.get('name') or '').strip().lower()
            code = (entry.get('cca2') or '').strip().lower()
            if name:
                needles.append(name)
            if code:
                needles.append(code)
            for state in entry.get('states') or []:
                state_name = str(state).strip().lower()
                if state_name:
                    needles.append(state_name)
        elif isinstance(entry, str) and entry.strip():
            needles.append(entry.strip().lower())

    # De-dupe preserving order
    seen = set()
    unique: list[str] = []
    for needle in needles:
        if needle not in seen:
            seen.add(needle)
            unique.append(needle)
    return unique


def location_matches(job: Job, profile: UltimateAutomationProfile) -> bool:
    """
    Geo match against preferred countries / city.

    Remote jobs that the user already accepted via work_arrangement skip geo
    when no city/country prefs are set, or when the location text still contains
    a preferred region (e.g. "Remote - Canada").
    """
    needles = _location_needles(profile)
    if not needles:
        return True

    location_lower = (job.location or '').lower()
    if any(needle in location_lower for needle in needles):
        return True

    # Fully remote with no location string to check — allow if remote preferred.
    preferred = {
        (value or '').strip().lower()
        for value in (profile.work_arrangements or [])
        if (value or '').strip()
    }
    if job.work_arrangement == 'remote' and 'remote' in preferred:
        # Prefer region overlap when location mentions a country; if blank/Remote only,
        # still accept so remote-only boards are usable.
        if not location_lower or location_lower in {'remote', 'unspecified'}:
            return True
        # Location has extra text that didn't match needles — reject (wrong region).
        return False

    return False


def job_matches_user(job: Job, profile: UltimateAutomationProfile) -> bool:
    if not job.is_active or not job.application_url:
        return False
    if not title_matches(job, profile):
        return False
    if not work_arrangement_matches(job, profile):
        return False
    if not location_matches(job, profile):
        return False
    return True


def today_task_count(user) -> int:
    today = timezone.localdate()
    return MatchedTask.objects.filter(
        user=user,
        created_at__date=today,
        status__in=[
            MatchedTask.STATUS_MATCHED,
            MatchedTask.STATUS_FIT_PAUSED,
            MatchedTask.STATUS_READY,
            MatchedTask.STATUS_APPLIED,
        ],
    ).count()


def candidate_jobs_queryset():
    return (
        Job.objects.filter(is_active=True)
        .exclude(application_url='')
        .select_related('source')
        .order_by(F('posted_date').desc(nulls_last=True), '-created_at')
    )


def match_jobs_for_profile(
    profile: UltimateAutomationProfile,
    *,
    dry_run: bool = False,
) -> MatchUserResult:
    ready, reason = profile_is_match_ready(profile)
    result = MatchUserResult(
        user_id=profile.user_id,
        username=getattr(profile.user, 'username', str(profile.user_id)),
    )
    if not ready:
        result.skipped_ineligible = True
        result.reason = reason
        return result

    remaining = profile.max_applications_per_day - today_task_count(profile.user)
    if remaining <= 0:
        result.skipped_cap = True
        result.reason = 'daily_cap'
        return result

    existing_task_job_ids = set(
        MatchedTask.objects.filter(user=profile.user).values_list('job_id', flat=True)
    )
    existing_app_job_ids = set(
        JobApplication.objects.filter(user=profile.user).values_list('job_id', flat=True)
    )
    skip_ids = existing_task_job_ids | existing_app_job_ids

    created = 0
    created_tasks: list[MatchedTask] = []
    for job in candidate_jobs_queryset().iterator(chunk_size=200):
        if created >= remaining:
            break
        if job.pk in skip_ids:
            continue
        if not job_matches_user(job, profile):
            continue

        if dry_run:
            created += 1
            continue

        task, was_created = MatchedTask.objects.get_or_create(
            user=profile.user,
            job=job,
            defaults={
                'application_url': job.application_url,
                'status': MatchedTask.STATUS_MATCHED,
            },
        )
        if was_created:
            created += 1
            skip_ids.add(job.pk)
            created_tasks.append(task)

    result.created = created
    result.created_tasks = created_tasks
    return result


def run_match_cycle(
    *,
    user_id: int | None = None,
    user_ids: list[int] | None = None,
    dry_run: bool = False,
) -> MatchCycleResult:
    profiles = (
        UltimateAutomationProfile.objects.select_related('user', 'default_resume')
        .order_by('id')
    )
    if user_ids is not None:
        profiles = profiles.filter(user_id__in=user_ids)
    elif user_id is not None:
        profiles = profiles.filter(user_id=user_id)

    cycle = MatchCycleResult()
    for profile in profiles:
        cycle.users_considered += 1
        user_result = match_jobs_for_profile(profile, dry_run=dry_run)
        cycle.per_user.append(user_result)
        cycle.tasks_created += user_result.created
        cycle.created_tasks.extend(user_result.created_tasks)
        if user_result.created:
            cycle.users_matched += 1
            logger.info(
                'Matched %s task(s) for user %s',
                user_result.created,
                user_result.username,
            )
    return cycle


def ultimate_subscriber_user_ids() -> list[int]:
    """ACTIVE Ultimate or Test subscribers (deduped)."""
    from django.contrib.auth import get_user_model
    from subscriptions.models import UserSubscription

    User = get_user_model()
    now = timezone.now()
    qs = (
        UserSubscription.objects.filter(
            status='ACTIVE',
            plan__name__iexact='Ultimate',
            start_date__lte=now,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gt=now))
        .values_list('user_id', flat=True)
    )
    test_qs = (
        UserSubscription.objects.filter(
            status='ACTIVE',
            plan__name__iexact='Test',
            start_date__lte=now,
        )
        .filter(Q(end_date__isnull=True) | Q(end_date__gt=now))
        .values_list('user_id', flat=True)
    )
    ids = sorted(set(qs) | set(test_qs))
    # Keep only existing users
    return list(User.objects.filter(pk__in=ids).order_by('id').values_list('id', flat=True))
