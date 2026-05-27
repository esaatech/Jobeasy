"""Dashboard adapter for why-should-I-apply generation on job applications."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from ai_service.models import WhyShouldIApplyAnswer
from ai_service.why_should_i_apply import (
    generate_why_should_i_apply,
    get_default_prompt_config,
    resolve_prompt_config,
)

if TYPE_CHECKING:
    from dashboard.models import JobApplication


def run_why_should_i_apply_for_application(
    job_application: JobApplication,
    *,
    resume_text: str,
) -> tuple[WhyShouldIApplyAnswer | None, str | None]:
    """
    Generate and persist an application answer for a dashboard job application.

    Returns ``(answer, error_message)``. On success ``error_message`` is None.
    """
    jd = (job_application.job_description or "").strip()
    if not jd:
        return None, "This application has no job description."
    if not (resume_text or "").strip():
        return None, "Resume content is required to generate an answer."

    user = job_application.user
    existing = job_application.why_should_i_apply_answer
    if existing and existing.status == "processing":
        return None, "Generation is already in progress."

    answer = existing
    if answer is None:
        answer = WhyShouldIApplyAnswer.objects.create(
            user=user,
            status="processing",
        )
        job_application.why_should_i_apply_answer = answer
        job_application.save(update_fields=["why_should_i_apply_answer"])

    answer.status = "processing"
    answer.error_message = ""
    answer.save(update_fields=["status", "error_message", "updated_at"])

    start = time.time()
    pc = answer.prompt_config or get_default_prompt_config()
    result = generate_why_should_i_apply(jd, resume_text, prompt_config=pc)
    elapsed = time.time() - start

    rpc = resolve_prompt_config(result.get("prompt_config_id"))
    if rpc:
        answer.prompt_config = rpc

    answer.processing_time = elapsed
    answer.gemini_model = str(
        result.get("model_id") or result.get("gemini_model") or ""
    )[:128]
    answer.instruction_slug = str(result.get("instruction_slug") or "")[:80]
    temp = result.get("temperature")
    if temp is not None:
        try:
            answer.temperature_used = float(temp)
        except (TypeError, ValueError):
            answer.temperature_used = None

    if result.get("success"):
        answer.content = str(result.get("answer_text") or "").strip()
        answer.status = "completed"
        answer.error_message = ""
    else:
        answer.status = "failed"
        answer.error_message = str(result.get("error") or "Generation failed.")[:8000]

    answer.save()
    return answer, None if result.get("success") else answer.error_message
