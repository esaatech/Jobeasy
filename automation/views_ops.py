"""Staff operator views for MatchedTask packets."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from automation.models import MatchedTask
from automation.services.apply_tasks import complete_matched_task, skip_matched_task
from automation.services.application_builder import (
    generate_cover_letter_for_matched_task,
    generate_why_hire_for_matched_task,
    optimize_resume_for_matched_task,
    run_fit_for_matched_task,
)

def _ops_url(task_id: int) -> str:
    return reverse('automation:matched_task_ops', args=[task_id])


@staff_member_required
@require_http_methods(['GET', 'POST'])
def matched_task_ops(request, task_id: int):
    task = get_object_or_404(
        MatchedTask.objects.select_related(
            'user',
            'job',
            'source_resume',
            'optimized_resume',
            'cover_letter',
            'why_should_i_apply_answer',
            'fit_evaluation',
        ),
        pk=task_id,
    )

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        if action == 'optimize_resume':
            result = optimize_resume_for_matched_task(task)
            if result.success:
                messages.success(request, 'Resume optimized.')
            else:
                messages.error(request, f'Optimize failed: {result.message}')
        elif action == 'generate_cover_letter':
            result = generate_cover_letter_for_matched_task(task)
            if result.success:
                messages.success(request, 'Cover letter generated.')
            else:
                messages.error(request, f'Cover letter failed: {result.message}')
        elif action == 'generate_why_hire':
            result = generate_why_hire_for_matched_task(task)
            if result.success:
                messages.success(request, 'Why-hire answer generated.')
            else:
                messages.error(request, f'Why-hire failed: {result.message}')
        elif action == 'rerun_fit':
            result = run_fit_for_matched_task(task)
            messages.info(request, f'Fit re-run complete ({result.message}).')
        elif action == 'mark_applied':
            notes = (request.POST.get('notes') or '').strip()
            complete_matched_task(task, notes=notes)
            messages.success(request, 'Marked as applied.')
        elif action == 'mark_skipped':
            reason = (request.POST.get('skip_reason') or 'other').strip()
            notes = (request.POST.get('notes') or '').strip()
            skip_matched_task(task, reason=reason, notes=notes)
            messages.success(request, f'Marked skipped ({reason}).')
        else:
            messages.warning(request, 'Unknown action.')
        return redirect(_ops_url(task.pk))

    summary = task.fit_summary or {}
    resume = task.resume_for_apply
    resume_url = None
    if resume:
        resume_url = reverse('resume_builder:view_resume_by_id', args=[resume.pk])

    display_score = task.fit_score
    if display_score is None:
        display_score = summary.get('overall_score')

    context = {
        'task': task,
        'summary': summary,
        'display_score': display_score,
        'strengths': summary.get('strengths') or [],
        'gaps': summary.get('gaps') or [],
        'resume_url': resume_url,
        'admin_list_url': reverse('admin:automation_matchedtask_changelist'),
        'skip_reasons': MatchedTask.SKIP_REASON_CHOICES,
    }
    return render(request, 'automation/ops/matched_task_detail.html', context)
