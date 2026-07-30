"""
Title family generation — Ultimate auto-apply Stage 2 setup + admin playground.

Uses the **provider on the prompt's linked AIModel** (OpenAI / Gemini / DeepSeek).
Prompt text comes from ``AIService`` slug ``title_family``.

Seed defaults with::

    python manage.py setup_ai_models
    python manage.py setup_title_family
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError

from .deepseek_client import OpenAIError, get_deepseek_client
from .gemini_client import gemini_generate_structured_sync
from .gemini_schema import TitleFamilyPayload
from .generation_config import resolve_for_prompt_config
from .models import AIModel, AIService, AIPromptConfiguration, TitleFamilyPlayground
from .open_ai import client

logger = logging.getLogger(__name__)

TITLE_FAMILY_SERVICE_SLUG = "title_family"
MIN_RESUME_TEXT_CHARS = 80


def normalize_title_list(value: Any, *, limit: int = 40) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in value:
        title = str(item or "").strip()
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        out.append(title[:120])
        if len(out) >= limit:
            break
    return out


def normalize_title_family_payload(payload: dict[str, Any] | TitleFamilyPayload) -> dict[str, list[str]]:
    if isinstance(payload, TitleFamilyPayload):
        data = payload.model_dump()
    else:
        data = payload if isinstance(payload, dict) else {}
    return {
        "primary_titles": normalize_title_list(data.get("primary_titles"), limit=10),
        "related_titles": normalize_title_list(data.get("related_titles"), limit=25),
        "exclude_titles": normalize_title_list(data.get("exclude_titles"), limit=25),
    }


def parse_pending_generation_result(raw: str | None) -> dict[str, Any] | None:
    """Parse ``pending_generation_result`` POST JSON from admin Save; None if invalid."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("success") is not True:
        return None
    if not isinstance(data.get("primary_titles"), list):
        return None
    return data


def resolve_prompt_config(prompt_config_pk: int | None) -> AIPromptConfiguration | None:
    if not prompt_config_pk:
        return None
    return (
        AIPromptConfiguration.objects.filter(
            pk=prompt_config_pk,
            is_active=True,
            service__slug=TITLE_FAMILY_SERVICE_SLUG,
            service__is_active=True,
        )
        .select_related("service", "ai_model")
        .first()
    )


def get_default_prompt_config() -> AIPromptConfiguration | None:
    svc = AIService.objects.filter(
        slug=TITLE_FAMILY_SERVICE_SLUG, is_active=True
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


def build_user_prompt_from_resume_text(resume_text: str) -> str:
    rs = resume_text.strip()
    return (
        "Suggest an exhaustive title family for auto-apply Stage 2 matching.\n"
        "Focus on role identity, not tools alone.\n\n"
        f"### RESUME ###\n{rs}\n\n"
        "Respond with JSON only: "
        '{ "primary_titles": [...], "related_titles": [...], "exclude_titles": [...] }'
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


def _empty_family() -> dict[str, list[str]]:
    return {
        "primary_titles": [],
        "related_titles": [],
        "exclude_titles": [],
    }


def _parse_json_family(raw: str) -> dict[str, list[str]]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Model returned non-object JSON.")
    family = normalize_title_family_payload(data)
    if not family["primary_titles"]:
        raise ValueError("Model returned no primary_titles.")
    return family


def _generate_with_openai(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[dict[str, list[str]], str | None]:
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
    return _parse_json_family(raw), raw


def _generate_with_deepseek(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[dict[str, list[str]], str | None]:
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
    return _parse_json_family(raw), raw


def _generate_with_gemini(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[dict[str, list[str]], str | None]:
    out = gemini_generate_structured_sync(
        system_instruction=system_instruction,
        user_text=user_block,
        response_schema=TitleFamilyPayload,
        model_id=gen.model_id,
        temperature=gen.temperature,
    )
    raw = out.get("raw") or ""
    parsed = out.get("parsed")
    if isinstance(parsed, TitleFamilyPayload):
        family = normalize_title_family_payload(parsed)
    elif isinstance(parsed, dict):
        family = normalize_title_family_payload(parsed)
    else:
        family = _parse_json_family(raw if isinstance(raw, str) else "{}")
    if not family["primary_titles"]:
        raise ValueError("Model returned no primary_titles.")
    return family, raw if isinstance(raw, str) else json.dumps(parsed)


def run_title_family_generation(
    *,
    resume_text: str,
    prompt_config: AIPromptConfiguration | None = None,
) -> dict[str, Any]:
    """
    Run title-family generation.

    - **Production / Ultimate setup**: omit ``prompt_config`` → service default.
    - **Admin playground**: pass selected ``prompt_config`` to test variants.
    """
    cfg = prompt_config or get_default_prompt_config()
    empty = _empty_family()
    if cfg is None:
        return {
            "success": False,
            **empty,
            "error": (
                f"No prompt configuration found for slug '{TITLE_FAMILY_SERVICE_SLUG}'. "
                "Run: python manage.py setup_title_family"
            ),
            "raw_text": None,
            "prompt_config_id": None,
            "instruction_slug": None,
        }

    if len((resume_text or "").strip()) < MIN_RESUME_TEXT_CHARS:
        return {
            "success": False,
            **empty,
            "error": (
                f"Resume text is too short ({len((resume_text or '').strip())} characters). "
                f"Paste at least {MIN_RESUME_TEXT_CHARS} characters, load a PDF into "
                "the resume text field, or attach a PDF when the textarea is empty."
            ),
            "raw_text": None,
            "prompt_config_id": cfg.pk,
            "instruction_slug": cfg.slug,
        }

    gen, provider = resolve_for_prompt_config(cfg)
    system_instruction = cfg.system_prompt.strip()
    user_block = build_user_prompt_from_resume_text(resume_text)
    base_meta = _meta_from_config(cfg, gen, provider=provider)

    raw: str | None = None
    try:
        if provider == AIModel.Provider.GEMINI:
            family, raw = _generate_with_gemini(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        elif provider == AIModel.Provider.DEEPSEEK:
            family, raw = _generate_with_deepseek(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        else:
            family, raw = _generate_with_openai(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
    except (OpenAIError, json.JSONDecodeError, ValueError, KeyError, Exception) as exc:
        logger.exception("title_family: %s call failed", provider)
        return {
            "success": False,
            **empty,
            "error": str(exc),
            "raw_text": raw,
            **base_meta,
        }

    return {
        "success": True,
        **family,
        "error": None,
        "raw_text": raw,
        **base_meta,
    }


def generate_title_family(resume_text: str) -> dict[str, Any]:
    """Production helper — always uses the default Title Family prompt."""
    return run_title_family_generation(resume_text=resume_text)


def persist_title_family_result(
    pk: object,
    *,
    result: dict[str, Any],
    prompt_config: AIPromptConfiguration | None = None,
    fallback_model_id: str = "gemini-2.5-flash",
) -> None:
    """Persist fields on ``TitleFamilyPlayground`` after generation returns."""
    pc = prompt_config
    if pc is None and result.get("prompt_config_id"):
        pc = resolve_prompt_config(result.get("prompt_config_id"))

    model_mid = str(
        result.get("model_id") or result.get("openai_model") or fallback_model_id
    )[:128]
    raw_text = result.get("raw_text") or ""
    if raw_text:
        raw_text = raw_text[:262144]

    family = (
        normalize_title_family_payload(result)
        if result.get("success")
        else _empty_family()
    )

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

    TitleFamilyPlayground.objects.filter(pk=pk).update(
        succeeded=bool(result.get("success")),
        error_message=str(result.get("error") or "")[:8000],
        primary_titles=family["primary_titles"],
        related_titles=family["related_titles"],
        exclude_titles=family["exclude_titles"],
        raw_response_text=raw_text,
        instruction_slug=slug_snap,
        model_id_snapshot=model_mid,
        ai_model_id=ai_model_pk,
        temperature_used=temp_used,
        prompt_config_id=result.get("prompt_config_id") or (pc.pk if pc else None),
    )
