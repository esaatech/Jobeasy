"""Helpers for completing operator MatchedTask actions."""

from __future__ import annotations

from automation.models import MatchedTask
from job_service.models import JobApplication


def complete_matched_task(task: MatchedTask, *, notes: str = '') -> MatchedTask:
    """Mark task applied and ensure a job_service.JobApplication exists."""
    task.mark_applied(notes=notes)

    resume = task.resume_for_apply
    if resume is None:
        profile = getattr(task.user, 'ultimate_automation_profile', None)
        if profile is not None:
            resume = profile.default_resume

    JobApplication.objects.get_or_create(
        user=task.user,
        job=task.job,
        defaults={
            'status': 'applied',
            'notes': notes or 'Marked applied via Ultimate MatchedTask queue',
            'resume_used': resume,
        },
    )
    return task


def skip_matched_task(
    task: MatchedTask,
    *,
    reason: str = 'other',
    notes: str = '',
) -> MatchedTask:
    task.mark_skipped(reason=reason, notes=notes)
    return task


# Backwards-compatible aliases
complete_apply_task = complete_matched_task
skip_apply_task = skip_matched_task
