"""
Professional summary generation — resume wizard and admin playground.

Uses the **provider on the prompt's linked AIModel** (OpenAI JSON chat or Gemini
structured JSON). Prompt text comes from ``AIService`` slug ``professional_summary``.

Seed defaults with::

    python manage.py setup_ai_models
    python manage.py setup_professional_summary
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError

from .deepseek_client import OpenAIError, get_deepseek_client
from .gemini_client import gemini_generate_structured_sync
from .gemini_schema import ProfessionalSummaryPayload
from .generation_config import resolve_for_prompt_config
from .models import AIModel, AIService, AIPromptConfiguration, ProfessionalSummaryPlayground
from .open_ai import client

logger = logging.getLogger(__name__)

PROFESSIONAL_SUMMARY_SERVICE_SLUG = "professional_summary"


def parse_pending_generation_result(raw: str | None) -> dict[str, Any] | None:
    """Parse ``pending_generation_result`` POST JSON from admin Save; None if absent/invalid."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("success") is not True:
        return None
    if not isinstance(data.get("summary"), str):
        return None
    return data


def resolve_prompt_config(prompt_config_pk: int | None) -> AIPromptConfiguration | None:
    if not prompt_config_pk:
        return None
    return (
        AIPromptConfiguration.objects.filter(
            pk=prompt_config_pk,
            is_active=True,
            service__slug=PROFESSIONAL_SUMMARY_SERVICE_SLUG,
            service__is_active=True,
        )
        .select_related("service", "ai_model")
        .first()
    )


def get_default_prompt_config() -> AIPromptConfiguration | None:
    """Active prompt with ``is_default=True`` for ``professional_summary`` (one per service)."""
    svc = AIService.objects.filter(
        slug=PROFESSIONAL_SUMMARY_SERVICE_SLUG, is_active=True
    ).first()
    if not svc:
        return None
    pref = (
        svc.prompts.filter(is_default=True, is_active=True)
        .select_related("ai_model")
        .first()
    )
    if pref:
        return pref
    return (
        svc.prompts.filter(is_active=True)
        .select_related("ai_model")
        .order_by("id")
        .first()
    )


def build_user_prompt_from_resume_data(resume_data: dict) -> str:
    return (
        "### RESUME DATA ###\n"
        f"Personal Info: {json.dumps(resume_data.get('personal_info', {}), indent=2)}\n"
        f"Experience: {json.dumps(resume_data.get('experience', []), indent=2)}\n"
        f"Education: {json.dumps(resume_data.get('education', []), indent=2)}\n"
        f"Skills: {json.dumps(resume_data.get('skills', {}), indent=2)}\n"
        f"Additional: {json.dumps(resume_data.get('additional', {}), indent=2)}\n"
        "### TASK ###\n"
        "Write a professional summary for this candidate. "
        'Respond with JSON: { "summary": "..." } only.'
    )


MIN_RESUME_TEXT_CHARS = 80


def build_user_prompt_from_resume_text(resume_text: str) -> str:
    rs = resume_text.strip()
    return (
        "Write a professional summary for this candidate. "
        "The resume content below may be plain text or pasted from a PDF — treat it as "
        "the full source of truth.\n\n"
        f"CANDIDATE RESUME:\n---\n{rs}\n---\n\n"
        'Respond with JSON: { "summary": "..." } only.'
    )


def _meta_from_config(
    cfg: AIPromptConfiguration, gen, *, provider: str
) -> dict[str, Any]:
    return {
        "prompt_config_id": cfg.pk,
        "instruction_slug": cfg.slug,
        "provider": provider,
        "model_id": gen.model_id,
        "openai_model": gen.model_id,
        "gemini_model": gen.model_id if provider == AIModel.Provider.GEMINI else "",
        "deepseek_model": gen.model_id if provider == AIModel.Provider.DEEPSEEK else "",
        "ai_model_id": gen.ai_model_id,
        "temperature": gen.temperature,
    }


def _generate_with_openai(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[str, str | None]:
    chat_resp = client.chat.completions.create(
        model=gen.model_id,
        temperature=gen.temperature,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_block},
        ],
        response_format={"type": "json_object"},
    )
    raw = (chat_resp.choices[0].message.content or "").strip()
    data = json.loads(raw)
    summary = str(data.get("summary", "")).strip()
    if not summary:
        raise ValueError("Model returned empty summary.")
    return summary, raw


def _generate_with_deepseek(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[str, str | None]:
    chat_resp = get_deepseek_client().chat.completions.create(
        model=gen.model_id,
        temperature=gen.temperature,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_block},
        ],
        response_format={"type": "json_object"},
    )
    raw = (chat_resp.choices[0].message.content or "").strip()
    data = json.loads(raw)
    summary = str(data.get("summary", "")).strip()
    if not summary:
        raise ValueError("Model returned empty summary.")
    return summary, raw


def _generate_with_gemini(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[str, str | None]:
    out = gemini_generate_structured_sync(
        system_instruction=system_instruction,
        user_text=user_block,
        response_schema=ProfessionalSummaryPayload,
        model_id=gen.model_id,
        temperature=gen.temperature,
    )
    raw = out.get("raw") or ""
    parsed = out.get("parsed")
    if isinstance(parsed, ProfessionalSummaryPayload):
        summary = parsed.summary.strip()
    elif isinstance(parsed, dict):
        summary = str(parsed.get("summary", "")).strip()
    else:
        data = json.loads(raw) if raw else {}
        summary = str(data.get("summary", "")).strip()
    if not summary:
        raise ValueError("Model returned empty summary.")
    return summary, raw if isinstance(raw, str) else json.dumps(parsed)


def run_professional_summary_generation(
    *,
    resume_data: dict | None = None,
    resume_text: str | None = None,
    prompt_config: AIPromptConfiguration | None = None,
) -> dict[str, Any]:
    """
    Run summary generation.

    - **Resume wizard** (production): omit ``prompt_config`` → uses the service
      default prompt (``is_default=True`` on one active row).
    - **Admin playground**: pass the selected ``prompt_config`` to test variants.
    """

    cfg = prompt_config or get_default_prompt_config()
    if cfg is None:
        return {
            "success": False,
            "summary": "",
            "error": (
                "No prompt configuration found for slug "
                f"'{PROFESSIONAL_SUMMARY_SERVICE_SLUG}'. "
                "Run: python manage.py setup_professional_summary"
            ),
            "raw_text": None,
            "prompt_config_id": None,
            "instruction_slug": None,
        }

    if resume_text is not None:
        if len(resume_text.strip()) < MIN_RESUME_TEXT_CHARS:
            return {
                "success": False,
                "summary": "",
                "error": (
                    f"Resume text is too short ({len(resume_text.strip())} characters). "
                    f"Paste at least {MIN_RESUME_TEXT_CHARS} characters, load a PDF into "
                    "the resume text field, or attach a PDF when the textarea is empty."
                ),
                "raw_text": None,
                "prompt_config_id": cfg.pk,
                "instruction_slug": cfg.slug,
            }
        user_block = build_user_prompt_from_resume_text(resume_text)
    elif resume_data is not None:
        user_block = build_user_prompt_from_resume_data(resume_data)
    else:
        return {
            "success": False,
            "summary": "",
            "error": "resume_data or resume_text is required.",
            "raw_text": None,
            "prompt_config_id": cfg.pk,
            "instruction_slug": cfg.slug,
        }

    gen, provider = resolve_for_prompt_config(cfg)

    system_instruction = cfg.system_prompt.strip()
    base_meta = _meta_from_config(cfg, gen, provider=provider)

    raw: str | None = None
    try:
        if provider == AIModel.Provider.GEMINI:
            summary, raw = _generate_with_gemini(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        elif provider == AIModel.Provider.DEEPSEEK:
            summary, raw = _generate_with_deepseek(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        else:
            summary, raw = _generate_with_openai(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
    except (OpenAIError, json.JSONDecodeError, ValueError, KeyError, Exception) as exc:
        logger.exception("professional_summary: %s call failed", provider)
        return {
            "success": False,
            "summary": "",
            "error": str(exc),
            "raw_text": raw,
            **base_meta,
        }

    return {
        "success": True,
        "summary": summary,
        "error": None,
        "raw_text": raw,
        **base_meta,
    }


def generate_professional_summary(resume_data: dict) -> dict[str, Any]:
    """Resume wizard — always uses the default Professional Summary prompt."""
    return run_professional_summary_generation(resume_data=resume_data)


def persist_professional_summary_result(
    pk: object,
    *,
    result: dict[str, Any],
    prompt_config: AIPromptConfiguration | None = None,
    fallback_model_id: str = "gpt-4o",
) -> None:
    """Persist fields on ``ProfessionalSummaryPlayground`` after generation returns."""
    pc = prompt_config
    if pc is None and result.get("prompt_config_id"):
        pc = resolve_prompt_config(result.get("prompt_config_id"))
    model_mid = str(
        result.get("model_id") or result.get("openai_model") or fallback_model_id
    )[:128]
    raw_text = result.get("raw_text") or ""
    if raw_text:
        raw_text = raw_text[:262144]

    summary = ""
    if result.get("success"):
        summary = str(result.get("summary") or "").strip()[:65535]

    slug_snap = (result.get("instruction_slug") or (pc.slug if pc else "") or "")[:80]

    temp_used = result.get("temperature")
    if temp_used is not None:
        try:
            temp_used = float(temp_used)
        except (TypeError, ValueError):
            temp_used = None

    ai_model_pk = result.get("ai_model_id")
    if ai_model_pk is not None:
        try:
            ai_model_pk = int(ai_model_pk)
        except (TypeError, ValueError):
            ai_model_pk = None

    ProfessionalSummaryPlayground.objects.filter(pk=pk).update(
        succeeded=result["success"],
        error_message=str(result.get("error") or "")[:8000],
        summary_text=summary,
        raw_response_text=raw_text,
        instruction_slug=slug_snap,
        openai_model=model_mid,
        ai_model_id=ai_model_pk,
        temperature_used=temp_used,
        prompt_config_id=result.get("prompt_config_id") or (pc.pk if pc else None),
    )
