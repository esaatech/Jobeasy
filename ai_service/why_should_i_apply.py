"""
Why-should-I-apply generation — application-field answer (not a cover letter).

Uses the **provider on the prompt's linked AIModel** (Gemini, OpenAI, or DeepSeek
plain-text completion). Prompt text is loaded from DB: ``AIService`` slug
``why_should_i_apply`` and its ``AIPromptConfiguration`` rows. Seed defaults with::

    python manage.py setup_ai_models
    python manage.py setup_why_should_i_apply
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError

from .deepseek_client import get_deepseek_client
from .gemini_client import gemini_generate_text_sync
from .generation_config import resolve_for_prompt_config
from .models import AIModel, AIService, AIPromptConfiguration, WhyShouldIApplyPlayground
from .open_ai import client

logger = logging.getLogger(__name__)

WHY_SHOULD_I_APPLY_SERVICE_SLUG = "why_should_i_apply"


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
    if not isinstance(data.get("answer_text"), str):
        return None
    return data


def resolve_prompt_config(prompt_config_pk: int | None) -> AIPromptConfiguration | None:
    if not prompt_config_pk:
        return None
    return (
        AIPromptConfiguration.objects.filter(
            pk=prompt_config_pk,
            is_active=True,
            service__slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG,
            service__is_active=True,
        )
        .select_related("service", "ai_model")
        .first()
    )


def get_default_prompt_config() -> AIPromptConfiguration | None:
    svc = AIService.objects.filter(
        slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG, is_active=True
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


def build_user_prompt(job_description: str, resume_text: str) -> str:
    jd = job_description.strip() or "(empty job description)"
    rs = resume_text.strip() or "(empty resume)"
    return (
        f"Write a 'Why should we hire you?' application answer using the inputs below.\n\n"
        f"JOB DESCRIPTION:\n---\n{jd}\n---\n\n"
        f"CANDIDATE RESUME:\n---\n{rs}\n---"
    )


def _meta_from_config(
    cfg: AIPromptConfiguration, gen, *, provider: str
) -> dict[str, Any]:
    return {
        "prompt_config_id": cfg.pk,
        "instruction_slug": cfg.slug,
        "provider": provider,
        "model_id": gen.model_id,
        "gemini_model": gen.model_id if provider == AIModel.Provider.GEMINI else "",
        "openai_model": gen.model_id if provider == AIModel.Provider.OPENAI else "",
        "deepseek_model": gen.model_id if provider == AIModel.Provider.DEEPSEEK else "",
        "ai_model_id": gen.ai_model_id,
        "temperature": gen.temperature,
    }


def _generate_with_gemini(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[str, str | None]:
    raw = gemini_generate_text_sync(
        system_instruction=system_instruction,
        prompt=user_block,
        model_id=gen.model_id,
        temperature=gen.temperature,
    )
    answer = (raw or "").strip()
    if not answer:
        raise ValueError("Model returned empty text.")
    return answer, raw


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
    )
    raw = (chat_resp.choices[0].message.content or "").strip()
    if not raw:
        raise ValueError("Model returned empty text.")
    return raw, raw


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
    )
    raw = (chat_resp.choices[0].message.content or "").strip()
    if not raw:
        raise ValueError("Model returned empty text.")
    return raw, raw


def generate_why_should_i_apply(
    job_description: str,
    resume_text: str,
    *,
    prompt_config: AIPromptConfiguration | None = None,
    ai_model_id: int | None = None,
    temperature: float | None = None,
    gemini_model: str | None = None,
    model_id_override: str | None = None,
) -> dict[str, Any]:
    """Run generation. Returns dict with keys: success, answer_text, error, raw_text, metadata."""

    cfg = prompt_config or get_default_prompt_config()
    if cfg is None:
        return {
            "success": False,
            "answer_text": "",
            "error": (
                "No prompt configuration found for slug "
                f"'{WHY_SHOULD_I_APPLY_SERVICE_SLUG}'. "
                "Run: python manage.py setup_why_should_i_apply"
            ),
            "raw_text": None,
            "prompt_config_id": None,
            "instruction_slug": None,
        }

    override = model_id_override or gemini_model
    gen, provider = resolve_for_prompt_config(
        cfg,
        ai_model_id=ai_model_id,
        temperature=temperature,
        model_id_override=override,
    )

    system_instruction = cfg.system_prompt.strip()
    user_block = build_user_prompt(job_description, resume_text)
    base_meta = _meta_from_config(cfg, gen, provider=provider)

    raw: str | None = None
    try:
        if provider == AIModel.Provider.GEMINI:
            answer, raw = _generate_with_gemini(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        elif provider == AIModel.Provider.DEEPSEEK:
            answer, raw = _generate_with_deepseek(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        else:
            answer, raw = _generate_with_openai(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
    except (OpenAIError, Exception) as exc:
        logger.exception("why_should_i_apply: %s call failed", provider)
        return {
            "success": False,
            "answer_text": "",
            "error": str(exc),
            "raw_text": raw,
            **base_meta,
        }

    return {
        "success": True,
        "answer_text": answer,
        "error": None,
        "raw_text": raw,
        **base_meta,
    }


def persist_why_should_i_apply_result(
    pk: object,
    *,
    result: dict[str, Any],
    prompt_config: AIPromptConfiguration | None,
    fallback_gemini_model_id: str,
) -> None:
    """Persist fields on ``WhyShouldIApplyPlayground`` after generation returns."""
    pc = prompt_config
    model_mid = str(
        result.get("model_id")
        or result.get("gemini_model")
        or result.get("openai_model")
        or result.get("deepseek_model")
        or fallback_gemini_model_id
    )[:128]
    raw_text = result.get("raw_text") or ""
    if raw_text:
        raw_text = raw_text[:262144]

    answer = ""
    if result.get("success"):
        answer = str(result.get("answer_text") or "").strip()[:65535]

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

    WhyShouldIApplyPlayground.objects.filter(pk=pk).update(
        succeeded=result["success"],
        error_message=str(result.get("error") or "")[:8000],
        answer_text=answer,
        raw_response_text=raw_text,
        instruction_slug=slug_snap,
        gemini_model=model_mid,
        ai_model_id=ai_model_pk,
        temperature_used=temp_used,
        prompt_config_id=result.get("prompt_config_id") or (pc.pk if pc else None),
    )
