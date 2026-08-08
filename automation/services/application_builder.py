"""Build apply packets for MatchedTask using the dashboard fit + generate path."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from ai_service.cover_letter import generate_cover_letter_from_raw_text
from ai_service.dashboard_job_fit import run_dashboard_job_fit_evaluation
from ai_service.models import WhyShouldIApplyAnswer
from ai_service.why_should_i_apply import (
    generate_why_should_i_apply,
    get_default_prompt_config,
    resolve_prompt_config,
)
from automation.models import MatchedTask, UltimateAutomationProfile
from coverletter.models import CoverLetter
from dashboard.views import _format_resume_content, _optimize_resume_for_job_application
from utils.resume_text import build_resume_text_for_evaluation

logger = logging.getLogger(__name__)


@dataclass
class PacketBuildResult:
    task: MatchedTask
    status: str
    message: str = ''


@dataclass
class ArtifactResult:
    task: MatchedTask
    success: bool
    message: str = ''


def _job_description(task: MatchedTask) -> str:
    text = (task.job.description or '').strip()
    if text:
        return text
    return f'{task.job.title} at {task.job.company}'


def _job_name(task: MatchedTask) -> str:
    return f'{task.job.title} @ {task.job.company}'


def _resolve_default_resume(task: MatchedTask):
    profile = UltimateAutomationProfile.objects.filter(user=task.user).first()
    if profile and profile.default_resume_id:
        return profile.default_resume
    return task.source_resume


def _apply_fit_fields(task: MatchedTask, fit_result: dict) -> None:
    summary = fit_result.get('summary') or {}
    score = fit_result.get('overall_score')
    if score is not None:
        summary = {
            **summary,
            'overall_score': score,
            'recommendation': fit_result.get('recommendation') or summary.get('recommendation'),
        }
    elif summary.get('overall_score') is not None:
        score = summary.get('overall_score')

    task.fit_summary = summary
    task.fit_tier = str(fit_result.get('tier') or '')
    task.fit_score = int(score) if score is not None else None
    if fit_result.get('evaluation_id'):
        task.fit_evaluation_id = fit_result['evaluation_id']


def run_fit_for_matched_task(task: MatchedTask) -> PacketBuildResult:
    """Run dashboard fit gate and persist summary/score/status (no generators)."""
    resume = _resolve_default_resume(task)
    if resume is None:
        task.status = MatchedTask.STATUS_FIT_PAUSED
        note = 'Fit skipped: no default resume on Ultimate profile.'
        task.operator_notes = (task.operator_notes + '\n' if task.operator_notes else '') + note
        task.save(update_fields=['status', 'operator_notes', 'updated_at'])
        return PacketBuildResult(task=task, status=task.status, message='no_resume')

    job_description = _job_description(task)
    task.source_resume = resume

    resume_text = build_resume_text_for_evaluation(resume)
    fit_result = run_dashboard_job_fit_evaluation(
        user=task.user,
        resume=resume,
        job_description=job_description,
        resume_text=resume_text,
        persist_fit_review_application=False,
    )

    if not fit_result.get('success'):
        task.status = MatchedTask.STATUS_FIT_PAUSED
        task.fit_tier = str(fit_result.get('tier') or 'red')
        task.fit_summary = {
            'error': fit_result.get('error') or 'Evaluation failed',
            'recommendation': fit_result.get('recommendation') or 'Evaluation failed',
        }
        task.fit_score = None
        if fit_result.get('evaluation_id'):
            task.fit_evaluation_id = fit_result['evaluation_id']
        task.save(
            update_fields=[
                'status',
                'source_resume',
                'fit_tier',
                'fit_summary',
                'fit_score',
                'fit_evaluation',
                'updated_at',
            ]
        )
        return PacketBuildResult(task=task, status=task.status, message='fit_failed')

    _apply_fit_fields(task, fit_result)
    auto_proceed = bool(fit_result.get('auto_proceed'))
    task.status = (
        MatchedTask.STATUS_READY if auto_proceed else MatchedTask.STATUS_FIT_PAUSED
    )
    task.save(
        update_fields=[
            'status',
            'source_resume',
            'fit_summary',
            'fit_tier',
            'fit_score',
            'fit_evaluation',
            'updated_at',
        ]
    )
    return PacketBuildResult(
        task=task,
        status=task.status,
        message='ready' if auto_proceed else 'fit_paused',
    )


def optimize_resume_for_matched_task(task: MatchedTask) -> ArtifactResult:
    """On-demand optimize (no fit gate). Allowed even when fit is yellow/red."""
    resume = task.source_resume or _resolve_default_resume(task)
    if resume is None:
        return ArtifactResult(task=task, success=False, message='no_resume')

    job_description = _job_description(task)
    job_name = _job_name(task)
    optimized, err, _ = _optimize_resume_for_job_application(
        task.user,
        job_description,
        resume,
        job_name,
        include_email_subject=True,
    )
    if not optimized:
        return ArtifactResult(
            task=task,
            success=False,
            message=err or 'optimize_failed',
        )

    task.source_resume = task.source_resume or resume
    task.optimized_resume = optimized
    task.save(update_fields=['source_resume', 'optimized_resume', 'updated_at'])
    return ArtifactResult(task=task, success=True, message='optimized')


def generate_cover_letter_for_matched_task(task: MatchedTask) -> ArtifactResult:
    """On-demand cover letter (no fit gate)."""
    resume = task.resume_for_apply or _resolve_default_resume(task)
    if resume is None:
        return ArtifactResult(task=task, success=False, message='no_resume')

    job_description = _job_description(task)
    job_name = _job_name(task)
    try:
        applicant_name = (resume.personal_info or {}).get('full_name') or resume.name or 'Applicant'
        resume_content = _format_resume_content(resume)
        cover = CoverLetter.objects.create(
            user=task.user,
            title=f'Cover Letter for {job_name}'[:200],
            job_description=job_description,
            status='processing',
        )
        cl_result = generate_cover_letter_from_raw_text(
            job_description,
            resume_content,
            applicant_name,
            include_email_subject=True,
        )
        if cl_result.get('success'):
            cover.content = cl_result.get('cover_letter') or ''
            if cl_result.get('title'):
                cover.title = str(cl_result['title'])[:200]
            cover.status = 'completed'
            cover.save()
            if not task.source_resume_id:
                task.source_resume = resume
            task.cover_letter = cover
            task.save(update_fields=['source_resume', 'cover_letter', 'updated_at'])
            return ArtifactResult(task=task, success=True, message='cover_letter')

        cover.status = 'failed'
        cover.save(update_fields=['status'])
        return ArtifactResult(
            task=task,
            success=False,
            message=str(cl_result.get('error') or 'cover_letter_failed'),
        )
    except Exception as exc:
        logger.exception('MatchedTask %s cover letter exception', task.pk)
        return ArtifactResult(task=task, success=False, message=str(exc))


def generate_why_hire_for_matched_task(task: MatchedTask) -> ArtifactResult:
    """On-demand why-hire answer (no fit gate)."""
    resume = task.resume_for_apply or _resolve_default_resume(task)
    if resume is None:
        return ArtifactResult(task=task, success=False, message='no_resume')

    job_description = _job_description(task)
    try:
        why_text = build_resume_text_for_evaluation(resume)
        answer = WhyShouldIApplyAnswer.objects.create(
            user=task.user,
            status='processing',
        )
        start = time.time()
        pc = get_default_prompt_config()
        result = generate_why_should_i_apply(job_description, why_text, prompt_config=pc)
        elapsed = time.time() - start
        rpc = resolve_prompt_config(result.get('prompt_config_id'))
        if rpc:
            answer.prompt_config = rpc
        answer.processing_time = elapsed
        answer.gemini_model = str(
            result.get('model_id') or result.get('gemini_model') or ''
        )[:128]
        if result.get('success'):
            answer.content = str(result.get('answer_text') or '').strip()
            answer.status = 'completed'
            answer.save()
            if not task.source_resume_id:
                task.source_resume = resume
            task.why_should_i_apply_answer = answer
            task.save(
                update_fields=['source_resume', 'why_should_i_apply_answer', 'updated_at']
            )
            return ArtifactResult(task=task, success=True, message='why_hire')

        answer.status = 'failed'
        answer.error_message = str(result.get('error') or 'Generation failed.')[:8000]
        answer.save()
        return ArtifactResult(
            task=task,
            success=False,
            message=str(result.get('error') or 'why_hire_failed'),
        )
    except Exception as exc:
        logger.exception('MatchedTask %s why-hire exception', task.pk)
        return ArtifactResult(task=task, success=False, message=str(exc))


def build_packet_for_matched_task(
    task: MatchedTask,
    *,
    optimize_resume: bool = False,
    generate_cover_letter: bool = False,
    generate_why_should_hire: bool = False,
) -> PacketBuildResult:
    """
    Always run fit. Eager-generate checked artifacts only when fit auto-proceeds.
    """
    fit = run_fit_for_matched_task(task)
    if fit.message in ('no_resume', 'fit_failed'):
        return fit

    auto_proceed = fit.message == 'ready'
    if not auto_proceed:
        return fit

    if optimize_resume:
        optimize_resume_for_matched_task(task)
    if generate_cover_letter:
        generate_cover_letter_for_matched_task(task)
    if generate_why_should_hire:
        generate_why_hire_for_matched_task(task)

    task.refresh_from_db()
    return PacketBuildResult(task=task, status=task.status, message='ready')


def build_packets_for_tasks(
    tasks: list[MatchedTask],
    *,
    optimize_resume: bool = False,
    generate_cover_letter: bool = False,
    generate_why_should_hire: bool = False,
) -> list[PacketBuildResult]:
    results = []
    for task in tasks:
        results.append(
            build_packet_for_matched_task(
                task,
                optimize_resume=optimize_resume,
                generate_cover_letter=generate_cover_letter,
                generate_why_should_hire=generate_why_should_hire,
            )
        )
    return results
