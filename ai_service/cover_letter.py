"""
Cover letter generation — user-facing letters and admin playground.

Uses the **provider on the prompt's linked AIModel** (Gemini, OpenAI, or DeepSeek).
Prompt text comes from two ``AIService`` slugs (letter-only vs with email subject) and
their ``AIPromptConfiguration`` version rows.

Seed defaults with::

    python manage.py setup_ai_models
    python manage.py setup_cover_letter
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError

from .deepseek_client import get_deepseek_client
from .gemini_client import gemini_generate_text_sync
from .generation_config import resolve_for_prompt_config
from .models import AIModel, AIService, AIPromptConfiguration, CoverLetterPlayground
from .open_ai import client

logger = logging.getLogger(__name__)

COVER_LETTER_SERVICE_SLUG = "cover_letter"
COVER_LETTER_WITH_EMAIL_SUBJECT_SERVICE_SLUG = "cover_letter_with_email_subject"
COVER_LETTER_SERVICE_SLUGS = frozenset(
    {COVER_LETTER_SERVICE_SLUG, COVER_LETTER_WITH_EMAIL_SUBJECT_SERVICE_SLUG}
)

# Legacy prompt slugs on the old single-service setup (setup_cover_letter migrates these).
LEGACY_EMAIL_SUBJECT_PROMPT_SLUGS = frozenset({"with-email-subject", "with_email_subject"})
LEGACY_LETTER_ONLY_PROMPT_SLUGS = frozenset({"letter-only", "default"})


def prompt_includes_email_subject(cfg: AIPromptConfiguration) -> bool:
    """True when the prompt belongs to the dashboard cover-letter service."""
    return (cfg.service.slug or "").strip() == COVER_LETTER_WITH_EMAIL_SUBJECT_SERVICE_SLUG


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
    if not isinstance(data.get("cover_letter"), str):
        return None
    return data


def resolve_prompt_config(prompt_config_pk: int | None) -> AIPromptConfiguration | None:
    if not prompt_config_pk:
        return None
    return (
        AIPromptConfiguration.objects.filter(
            pk=prompt_config_pk,
            is_active=True,
            service__slug__in=COVER_LETTER_SERVICE_SLUGS,
            service__is_active=True,
        )
        .select_related("service", "ai_model")
        .first()
    )


def resolve_prompt_config_by_slug(
    slug: str, *, service_slug: str | None = None
) -> AIPromptConfiguration | None:
    slug = (slug or "").strip()
    if not slug:
        return None
    filters: dict[str, Any] = {
        "slug": slug,
        "is_active": True,
        "service__is_active": True,
    }
    if service_slug:
        filters["service__slug"] = service_slug
    else:
        filters["service__slug__in"] = COVER_LETTER_SERVICE_SLUGS
    return (
        AIPromptConfiguration.objects.filter(**filters)
        .select_related("service", "ai_model")
        .first()
    )


def get_default_prompt_config(
    service_slug: str = COVER_LETTER_SERVICE_SLUG,
) -> AIPromptConfiguration | None:
    svc = AIService.objects.filter(slug=service_slug, is_active=True).first()
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


def build_user_prompt(
    job_description: str,
    resume_text: str,
    *,
    applicant_name: str | None = None,
    include_email_subject: bool = False,
) -> str:
    jd = job_description.strip() or "(empty job description)"
    rs = resume_text.strip() or "(empty resume)"

    name_instruction = ""
    display_name = (applicant_name or "").strip()
    if not display_name:
        name_instruction = (
            "IMPORTANT: No applicant name was provided. Extract the candidate's full name "
            "from the resume text and use it after 'Sincerely,'.\n"
        )
        display_name = "[EXTRACT_NAME_FROM_RESUME]"

    email_hint = ""
    if include_email_subject:
        email_hint = (
            "Include EMAIL_SUBJECT per the system instructions. "
            "Make the subject specific to the role (not generic 'Job Application').\n"
        )

    return (
        "Create a professional cover letter from the inputs below.\n\n"
        f"JOB POSTING:\n---\n{jd}\n---\n\n"
        f"RESUME:\n---\n{rs}\n---\n\n"
        f"{name_instruction}"
        "The cover letter must start with 'Dear Hiring Manager,' and end with "
        f"'Sincerely,' followed by '{display_name}' on the next line. "
        "Keep to about one page. Do not include dates or addresses.\n"
        f"{email_hint}"
    )


def parse_ai_response(response_content: str, include_email_subject: bool) -> dict[str, str]:
    """Parse TITLE / EMAIL_SUBJECT / COVER_LETTER sections from model output."""
    result: dict[str, str] = {}

    if response_content.startswith("```"):
        response_content = (
            response_content.split("```", 2)[1]
            if "```" in response_content
            else response_content
        )

    lines = response_content.split("\n")
    current_section: str | None = None
    section_content: list[str] = []

    def flush_section() -> None:
        nonlocal current_section, section_content
        if current_section and section_content:
            result[current_section] = "\n".join(section_content).strip()
        section_content = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("**") or line.startswith("*"):
            continue

        if line.upper().startswith("TITLE:"):
            flush_section()
            current_section = "title"
            title_content = line[6:].strip()
            section_content = [title_content] if title_content else []
            continue

        if line.upper().startswith("EMAIL_SUBJECT:"):
            flush_section()
            current_section = "email_subject"
            subject_content = line[14:].strip()
            section_content = [subject_content] if subject_content else []
            continue

        if line.upper().startswith("COVER_LETTER:"):
            flush_section()
            current_section = "cover_letter"
            letter_content = line[13:].strip()
            section_content = [letter_content] if letter_content else []
            continue

        if current_section:
            section_content.append(line)

    flush_section()

    if not result:
        result["cover_letter"] = response_content.strip()
        result["title"] = "Cover Letter"
        if include_email_subject:
            result["email_subject"] = "Job Application"

    return result


def clean_cover_letter_content(cover_letter_content: str, applicant_name: str) -> str:
    """Clean the cover letter body and ensure a signature line."""
    if not cover_letter_content:
        return ""

    lines = cover_letter_content.split("\n")
    cleaned_lines: list[str] = []
    found_closing = False
    signature_added = False

    for line in lines:
        line = line.strip()
        if line.startswith("#") or line.startswith("**") or line.startswith("*"):
            continue
        if any(
            section in line.lower()
            for section in (
                "experience:",
                "skills:",
                "education:",
                "background:",
                "qualifications:",
                "summary:",
            )
        ):
            break
        if "sincerely," in line.lower():
            found_closing = True
            cleaned_lines.append(line)
            continue
        if found_closing and line and not line.startswith("experience:"):
            cleaned_lines.append(line)
            signature_added = True
            break
        if line:
            cleaned_lines.append(line)

    if found_closing and not signature_added and applicant_name:
        cleaned_lines.append(applicant_name)

    return "\n".join(cleaned_lines)


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


def run_cover_letter_generation(
    job_description: str,
    resume_text: str,
    *,
    prompt_config: AIPromptConfiguration | None = None,
    service_slug: str = COVER_LETTER_SERVICE_SLUG,
    applicant_name: str | None = None,
    ai_model_id: int | None = None,
    temperature: float | None = None,
    model_id_override: str | None = None,
) -> dict[str, Any]:
    """
    Run cover letter generation.

    - **Production** (`coverletter` UI): omit ``prompt_config`` → default on
      ``cover_letter``.
    - **Dashboard** (email subject): use ``generate_cover_letter_from_raw_text``
      with ``include_email_subject=True`` → default on ``cover_letter_with_email_subject``.
    - **Admin playground**: pass selected ``prompt_config`` to test prompt versions.
    """

    cfg = prompt_config or get_default_prompt_config(service_slug)
    if cfg is None:
        return {
            "success": False,
            "cover_letter": "",
            "title": "",
            "email_subject": "",
            "error": (
                "No prompt configuration found for service "
                f"'{service_slug}'. "
                "Run: python manage.py setup_cover_letter"
            ),
            "raw_text": None,
            "prompt_config_id": None,
            "instruction_slug": None,
        }

    include_email = prompt_includes_email_subject(cfg)
    gen, provider = resolve_for_prompt_config(
        cfg,
        ai_model_id=ai_model_id,
        temperature=temperature,
        model_id_override=model_id_override,
    )

    system_instruction = cfg.system_prompt.strip()
    user_block = build_user_prompt(
        job_description,
        resume_text,
        applicant_name=applicant_name,
        include_email_subject=include_email,
    )
    base_meta = _meta_from_config(cfg, gen, provider=provider)

    raw: str | None = None
    try:
        if provider == AIModel.Provider.GEMINI:
            response_content, raw = _generate_with_gemini(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        elif provider == AIModel.Provider.DEEPSEEK:
            response_content, raw = _generate_with_deepseek(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        else:
            response_content, raw = _generate_with_openai(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
    except (OpenAIError, Exception) as exc:
        logger.exception("cover_letter: %s call failed", provider)
        return {
            "success": False,
            "cover_letter": "",
            "title": "",
            "email_subject": "",
            "error": str(exc),
            "raw_text": raw,
            **base_meta,
        }

    parsed = parse_ai_response(response_content, include_email)
    sig_name = (applicant_name or "").strip() or "[EXTRACT_NAME_FROM_RESUME]"
    letter_body = parsed.get("cover_letter", "")
    if letter_body:
        letter_body = clean_cover_letter_content(letter_body, sig_name)

    return {
        "success": True,
        "cover_letter": letter_body,
        "title": parsed.get("title", ""),
        "email_subject": parsed.get("email_subject", ""),
        "error": None,
        "raw_text": raw,
        **base_meta,
    }


def generate_cover_letter_from_raw_text(
    job_posting: str,
    resume_text: str,
    applicant_name: str | None = None,
    include_email_subject: bool = False,
) -> dict[str, Any]:
    """Backward-compatible entry point for coverletter and dashboard views."""
    if include_email_subject:
        service_slug = COVER_LETTER_WITH_EMAIL_SUBJECT_SERVICE_SLUG
        pc = get_default_prompt_config(service_slug)
    else:
        service_slug = COVER_LETTER_SERVICE_SLUG
        pc = None
    return run_cover_letter_generation(
        job_posting,
        resume_text,
        prompt_config=pc,
        service_slug=service_slug,
        applicant_name=applicant_name,
    )


def persist_cover_letter_playground_result(
    pk: object,
    *,
    result: dict[str, Any],
    prompt_config: AIPromptConfiguration | None,
    fallback_model_id: str = "gpt-4o",
) -> None:
    """Persist fields on ``CoverLetterPlayground`` after generation returns."""
    pc = prompt_config
    model_mid = str(
        result.get("model_id")
        or result.get("gemini_model")
        or result.get("openai_model")
        or result.get("deepseek_model")
        or fallback_model_id
    )[:128]
    raw_text = result.get("raw_text") or ""
    if raw_text:
        raw_text = raw_text[:262144]

    letter = ""
    title = ""
    email_subject = ""
    if result.get("success"):
        letter = str(result.get("cover_letter") or "").strip()[:65535]
        title = str(result.get("title") or "").strip()[:512]
        email_subject = str(result.get("email_subject") or "").strip()[:512]

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

    CoverLetterPlayground.objects.filter(pk=pk).update(
        succeeded=result["success"],
        error_message=str(result.get("error") or "")[:8000],
        cover_letter_text=letter,
        title=title,
        email_subject=email_subject,
        raw_response_text=raw_text,
        instruction_slug=slug_snap,
        model_used=model_mid,
        ai_model_id=ai_model_pk,
        temperature_used=temp_used,
        prompt_config_id=result.get("prompt_config_id") or (pc.pk if pc else None),
    )
