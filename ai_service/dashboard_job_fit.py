"""Dashboard adapter: shared evaluate_resume_against_job + persist + tier."""

from __future__ import annotations

from typing import Any

from django.conf import settings as django_settings
from django.urls import reverse

from .fit_gate import (
    classify_fit_tier,
    evaluation_summary,
    tier_allows_auto_proceed,
    tier_allows_proceed_with_override,
)
from .job_fit_settings import get_job_fit_gate_settings
from .models import ResumeJobEvaluation
from .resume_job_evaluation import (
    evaluate_resume_against_job,
    persist_resume_job_evaluation_result,
)

FIT_REVIEW_TIERS = frozenset({"yellow", "red"})


def _job_name_from_description(job_description: str) -> str:
    text = (job_description or "").strip()
    if len(text) > 50:
        return text[:50] + "..."
    return text or "Job application"


def create_fit_review_job_application(
    *,
    user,
    resume,
    job_description: str,
    eval_row: ResumeJobEvaluation,
) -> "JobApplication":
    """Persist a gated dashboard job application linked to the evaluation."""
    from dashboard.models import JobApplication

    job_app = JobApplication.objects.create(
        user=user,
        job_name=_job_name_from_description(job_description),
        job_description=job_description,
        status="fit_review",
        fit_evaluation=eval_row,
    )
    if eval_row.job_application_id != job_app.pk:
        eval_row.job_application = job_app
        eval_row.save(update_fields=["job_application"])
    return job_app


def run_dashboard_job_fit_evaluation(
    *,
    user,
    resume,
    job_description: str,
    resume_text: str,
) -> dict[str, Any]:
    """
    Run job-fit evaluation for dashboard using gate settings prompt (provider from AIModel).

    Returns a dict suitable for JsonResponse (not including HTTP status).
    """
    gate_settings = get_job_fit_gate_settings()

    if not gate_settings.is_enabled:
        return {
            "success": True,
            "gate_enabled": False,
            "tier": "bypass",
            "auto_proceed": True,
            "evaluation_id": None,
            "evaluation": None,
            "summary": {},
            "message": "Job fit gate is disabled.",
        }

    prompt_config = gate_settings.prompt_config
    if prompt_config is None:
        return {
            "success": False,
            "gate_enabled": True,
            "error": (
                "Job fit gate has no prompt configured. Run setup_job_fit_gate or set "
                "prompt_config in Job fit gate settings."
            ),
        }

    eval_row = ResumeJobEvaluation.objects.create(
        user=user,
        resume=resume,
        job_description=job_description,
        resume_text=resume_text,
        prompt_config=prompt_config,
    )

    result = evaluate_resume_against_job(
        job_description,
        resume_text,
        prompt_config=prompt_config,
    )

    fallback_model = getattr(
        django_settings,
        "GEMINI_RESUME_JOB_EVAL_MODEL",
        "gemini-2.5-flash",
    )
    persist_resume_job_evaluation_result(
        pk=eval_row.pk,
        result=result,
        prompt_config=prompt_config,
        fallback_gemini_model_id=str(
            result.get("model_id") or result.get("gemini_model") or fallback_model
        ),
    )
    eval_row.refresh_from_db()

    if not result.get("success"):
        return {
            "success": False,
            "gate_enabled": True,
            "evaluation_id": eval_row.pk,
            "error": result.get("error") or "Evaluation failed",
            "tier": "red",
            "auto_proceed": False,
        }

    evaluation = result.get("evaluation") or {}
    tier = classify_fit_tier(evaluation, gate_settings)
    summary = evaluation_summary(evaluation)

    payload: dict[str, Any] = {
        "success": True,
        "gate_enabled": True,
        "evaluation_id": eval_row.pk,
        "tier": tier,
        "auto_proceed": tier_allows_auto_proceed(tier),
        "allows_override": tier_allows_proceed_with_override(tier),
        "evaluation": evaluation,
        "summary": summary,
        "overall_score": eval_row.overall_score,
        "recommendation": eval_row.recommendation,
    }

    if tier in FIT_REVIEW_TIERS:
        job_app = create_fit_review_job_application(
            user=user,
            resume=resume,
            job_description=job_description,
            eval_row=eval_row,
        )
        payload["job_id"] = job_app.pk
        payload["status"] = "fit_review"
        payload["job_name"] = job_app.job_name
        payload["created_at"] = job_app.created_at.strftime('%b %d, %Y - %I:%M %p')
        payload["detail_url"] = reverse(
            "dashboard:job_application_detail",
            args=[job_app.pk],
        )

    return payload


def validate_evaluation_for_generate(
    *,
    user,
    evaluation_id: int,
    force_proceed: bool = False,
    resume_id: int | None = None,
    job_description: str | None = None,
) -> tuple[ResumeJobEvaluation | None, str | None]:
    """
    Load evaluation for phase-2 generate. Returns (evaluation, error_message).
    """
    gate_settings = get_job_fit_gate_settings()
    if not gate_settings.is_enabled:
        return None, None

    try:
        ev = ResumeJobEvaluation.objects.get(pk=evaluation_id, user=user)
    except ResumeJobEvaluation.DoesNotExist:
        return None, "Invalid or missing evaluation_id."

    if not ev.succeeded or not ev.evaluation_json:
        return None, "Evaluation did not complete successfully."

    if resume_id is not None and ev.resume_id != resume_id:
        return None, "Evaluation does not match the selected resume."
    if job_description is not None:
        if (ev.job_description or "").strip() != job_description.strip():
            return None, "Evaluation does not match the job description."

    tier = classify_fit_tier(ev.evaluation_json, gate_settings)
    if tier_allows_auto_proceed(tier):
        return ev, None
    if force_proceed and tier_allows_proceed_with_override(tier):
        return ev, None
    if tier == "bypass":
        return ev, None

    return None, (
        f"Job fit check indicates {ev.recommendation or tier} "
        f"(score {ev.overall_score}). Confirm to proceed anyway."
    )
