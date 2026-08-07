"""Helpers for completing operator ApplyTask actions."""

from __future__ import annotations

from automation.models import ApplyTask
from job_service.models import JobApplication


def complete_apply_task(task: ApplyTask, *, notes: str = '') -> ApplyTask:
    """Mark task applied and ensure a job_service.JobApplication exists."""
    task.mark_applied(notes=notes)

    resume = None
    profile = getattr(task.user, 'ultimate_automation_profile', None)
    if profile is not None:
        resume = profile.default_resume

    JobApplication.objects.get_or_create(
        user=task.user,
        job=task.job,
        defaults={
            'status': 'applied',
            'notes': notes or 'Marked applied via Ultimate ApplyTask queue',
            'resume_used': resume,
        },
    )
    return task


def skip_apply_task(
    task: ApplyTask,
    *,
    reason: str = 'other',
    notes: str = '',
) -> ApplyTask:
    task.mark_skipped(reason=reason, notes=notes)
    return task
