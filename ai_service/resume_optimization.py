"""
Resume optimization for dashboard job applications.

Uses the **provider on the prompt's linked AIModel** (Gemini structured JSON,
OpenAI / DeepSeek JSON chat). Two services:

- ``resume_optimization`` — tailoring without email subject
- ``resume_optimization_with_email_subject`` — includes ``email_subject`` in JSON

Seed defaults with::

    python manage.py setup_ai_models
    python manage.py setup_resume_optimization
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError
from pydantic import ValidationError

from .deepseek_client import get_deepseek_client
from .gemini_client import gemini_generate_structured_sync
from .gemini_schema import ResumeOptimizationPayload
from .generation_config import resolve_for_prompt_config
from .models import AIModel, AIService, AIPromptConfiguration, ResumeOptimizationPlayground
from .open_ai import client
from .prompt_formatting import coerce_skill_list
from .json_repair import loads_json_lenient
from .resume_optimization_validate import validate_and_merge_payload

logger = logging.getLogger(__name__)

RESUME_OPT_MAX_OUTPUT_TOKENS = 16384
RESUME_OPT_COMPACT_SUFFIX = (
    "\n\nOUTPUT SIZE (strict): At most 5 bullets per experience entry; "
    "max 200 characters per bullet. In description use plain text only — "
    "one bullet per line, newline-separated, no HTML tags, no double-quote "
    "characters inside bullets (use apostrophes instead)."
)

RESUME_OPTIMIZATION_SERVICE_SLUG = "resume_optimization"
RESUME_OPTIMIZATION_WITH_EMAIL_SERVICE_SLUG = "resume_optimization_with_email_subject"
RESUME_OPTIMIZATION_SERVICE_SLUGS = frozenset(
    {RESUME_OPTIMIZATION_SERVICE_SLUG, RESUME_OPTIMIZATION_WITH_EMAIL_SERVICE_SLUG}
)


def parse_pending_generation_result(raw: str | None) -> dict[str, Any] | None:
    """Parse ``pending_generation_result`` POST JSON from admin Save."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("success") is not True:
        return None
    if not data.get("optimized_summary") and not data.get("experience"):
        return None
    return data


def resolve_prompt_config(prompt_config_pk: int | None) -> AIPromptConfiguration | None:
    if not prompt_config_pk:
        return None
    return (
        AIPromptConfiguration.objects.filter(
            pk=prompt_config_pk,
            is_active=True,
            service__slug__in=RESUME_OPTIMIZATION_SERVICE_SLUGS,
            service__is_active=True,
        )
        .select_related("service", "ai_model")
        .first()
    )


def parse_resume_data_for_playground(resume_text: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    Parse admin playground resume_text as SOURCE_RESUME JSON.
    Returns (resume_data, error_message).
    """
    text = (resume_text or "").strip()
    if not text:
        return None, "Resume JSON is required."
    if not text.startswith("{"):
        if len(text) < 80:
            return None, (
                "Resume text is too short. Paste SOURCE_RESUME JSON or load a PDF "
                "(at least 80 characters of extracted text)."
            )
        return {
            "professional_summary": "",
            "experience": [],
            "education": [],
            "technical_skills": [],
            "soft_skills": [],
            "languages": [],
            "projects": [],
            "resume_plain_text": text,
        }, None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"Invalid resume JSON: {exc}"
    if not isinstance(data, dict):
        return None, "Resume JSON must be an object."
    resume_data = {
        "professional_summary": data.get("professional_summary") or data.get("summary") or "",
        "experience": data.get("experience") or [],
        "education": data.get("education") or [],
        "technical_skills": data.get("technical_skills") or [],
        "soft_skills": data.get("soft_skills") or [],
        "languages": data.get("languages") or [],
        "projects": data.get("projects") or [],
    }
    if not resume_data["experience"] and not str(resume_data["professional_summary"]).strip():
        return None, "Resume JSON needs at least professional_summary or experience."
    return resume_data, None


def persist_resume_optimization_playground_result(
    pk: object,
    *,
    result: dict[str, Any],
    prompt_config: AIPromptConfiguration | None,
    fallback_model_id: str = "gemini-2.5-flash",
) -> None:
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

    title = email = summary = result_json = ""
    ats: int | None = None
    if result.get("success"):
        title = str(result.get("title") or "").strip()[:512]
        email = str(result.get("email_subject") or "").strip()[:512]
        summary = str(result.get("optimized_summary") or "").strip()[:65535]
        try:
            ats = int(result.get("ats_score")) if result.get("ats_score") is not None else None
        except (TypeError, ValueError):
            ats = None
        try:
            result_json = json.dumps(
                {
                    k: result.get(k)
                    for k in (
                        "title",
                        "email_subject",
                        "optimized_summary",
                        "reordered_technical_skills",
                        "reordered_soft_skills",
                        "reordered_languages",
                        "experience",
                        "reordered_projects",
                        "ats_score",
                        "keyword_matches",
                        "improvement_suggestions",
                    )
                },
                indent=2,
            )[:262144]
        except (TypeError, ValueError):
            result_json = ""

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

    ResumeOptimizationPlayground.objects.filter(pk=pk).update(
        succeeded=result["success"],
        error_message=str(result.get("error") or "")[:8000],
        title=title,
        email_subject=email,
        optimized_summary=summary,
        ats_score=ats,
        result_json=result_json,
        raw_response_text=raw_text,
        instruction_slug=slug_snap,
        model_used=model_mid,
        ai_model_id=ai_model_pk,
        temperature_used=temp_used,
        prompt_config_id=result.get("prompt_config_id") or (pc.pk if pc else None),
    )


def get_default_prompt_config(
    service_slug: str = RESUME_OPTIMIZATION_SERVICE_SLUG,
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


def _slim_experience_for_prompt(experience: list) -> list[dict[str, Any]]:
    """Strip HTML and cap bullets so Gemini JSON stays smaller and valid."""
    from resume_builder.resume_extra import (
        extract_project_bullets_from_html,
        plain_text_to_bullet_lines,
    )

    slim: list[dict[str, Any]] = []
    for exp in experience or []:
        if not isinstance(exp, dict):
            continue
        bullets = extract_project_bullets_from_html(str(exp.get("description") or ""))
        if not bullets:
            bullets = plain_text_to_bullet_lines(str(exp.get("description") or ""))
        bullets = [b.replace('"', "'")[:220] for b in bullets[:6] if b.strip()]
        slim.append(
            {
                "company": exp.get("company") or "",
                "title": exp.get("title") or exp.get("position") or "",
                "start_date": exp.get("start_date") or "",
                "end_date": exp.get("end_date") or "",
                "description": "\n".join(bullets),
            }
        )
    return slim


def build_user_prompt(job_description: str, resume_data: dict[str, Any]) -> str:
    jd = (job_description or "").strip() or "(empty job description)"
    plain = (resume_data.get("resume_plain_text") or "").strip()
    if plain:
        if len(plain) > 12000:
            plain = plain[:12000] + "\n…[truncated for length]"
        return (
            "Tailor this candidate's resume to the job below. Use ONLY facts present in SOURCE_RESUME.\n\n"
            f"JOB DESCRIPTION:\n---\n{jd}\n---\n\n"
            f"SOURCE_RESUME (plain text from PDF or paste):\n---\n{plain}\n---\n\n"
            "Return JSON matching the schema in the system instructions. "
            "Do not invent employers, titles, or skills not supported by this text."
        )
    projects = resume_data.get("projects") or []
    if isinstance(projects, list):
        projects = [str(p).replace('"', "'")[:220] for p in projects[:12] if str(p).strip()]
    payload = {
        "professional_summary": str(resume_data.get("professional_summary") or "")[:2000],
        "experience": _slim_experience_for_prompt(resume_data.get("experience") or []),
        "education": resume_data.get("education") or [],
        "technical_skills": resume_data.get("technical_skills") or [],
        "soft_skills": resume_data.get("soft_skills") or [],
        "languages": resume_data.get("languages") or [],
        "projects": projects,
    }
    return (
        "Tailor this candidate's resume to the job below. Use ONLY facts present in SOURCE_RESUME.\n\n"
        f"JOB DESCRIPTION:\n---\n{jd}\n---\n\n"
        f"SOURCE_RESUME (JSON):\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Return JSON matching the schema in the system instructions."
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


def _parse_payload(raw: str, parsed: Any) -> ResumeOptimizationPayload:
    if isinstance(parsed, ResumeOptimizationPayload):
        return parsed
    if isinstance(parsed, dict):
        return ResumeOptimizationPayload.model_validate(parsed)
    data = loads_json_lenient(raw) if raw else {}
    return ResumeOptimizationPayload.model_validate(data)


def _generate_with_gemini(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[ResumeOptimizationPayload, str | None]:
    last_exc: Exception | None = None
    for attempt, extra in enumerate(("", RESUME_OPT_COMPACT_SUFFIX)):
        try:
            out = gemini_generate_structured_sync(
                system_instruction=system_instruction,
                user_text=user_block + extra,
                response_schema=ResumeOptimizationPayload,
                model_id=gen.model_id,
                temperature=gen.temperature,
                max_output_tokens=RESUME_OPT_MAX_OUTPUT_TOKENS,
            )
            raw = out.get("raw") or ""
            parsed = out.get("parsed")
            payload = _parse_payload(raw, parsed)
            return payload, raw if isinstance(raw, str) else json.dumps(parsed)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            last_exc = exc
            if attempt == 0:
                logger.warning(
                    "resume_optimization: Gemini JSON failed (%s); retrying compact",
                    exc,
                )
                continue
            raise
    if last_exc:
        raise last_exc
    raise ValueError("Gemini resume optimization failed.")


def _generate_with_openai(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[ResumeOptimizationPayload, str | None]:
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
    return _parse_payload(raw, None), raw


def _generate_with_deepseek(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[ResumeOptimizationPayload, str | None]:
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
    return _parse_payload(raw, None), raw


def run_resume_optimization_generation(
    job_description: str,
    resume_data: dict[str, Any],
    *,
    prompt_config: AIPromptConfiguration | None = None,
    service_slug: str = RESUME_OPTIMIZATION_SERVICE_SLUG,
) -> dict[str, Any]:
    cfg = prompt_config or get_default_prompt_config(service_slug)
    if cfg is None:
        return {
            "success": False,
            "error": (
                f"No prompt configuration found for service '{service_slug}'. "
                "Run: python manage.py setup_resume_optimization"
            ),
        }

    gen, provider = resolve_for_prompt_config(cfg)
    system_instruction = cfg.system_prompt.strip()
    user_block = build_user_prompt(job_description, resume_data)
    base_meta = _meta_from_config(cfg, gen, provider=provider)

    raw: str | None = None
    try:
        if provider == AIModel.Provider.GEMINI:
            payload, raw = _generate_with_gemini(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        elif provider == AIModel.Provider.DEEPSEEK:
            payload, raw = _generate_with_deepseek(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        else:
            payload, raw = _generate_with_openai(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
    except (OpenAIError, ValidationError, json.JSONDecodeError, ValueError, Exception) as exc:
        logger.exception("resume_optimization: %s call failed", provider)
        return {
            "success": False,
            "error": str(exc),
            "raw_text": raw,
            **base_meta,
        }

    merged = validate_and_merge_payload(payload, resume_data)
    merged["success"] = True
    merged["error"] = None
    merged["raw_text"] = raw
    merged.update(base_meta)
    logger.info(
        "resume_optimization: ok title=%r ats=%s exp_rows=%s",
        merged.get("title"),
        merged.get("ats_score"),
        len(merged.get("experience") or []),
    )
    return merged


def optimize_resume_for_job(
    job_description: str,
    resume_data: dict,
    include_email_subject: bool = False,
) -> dict[str, Any]:
    """Backward-compatible entry point used by dashboard views."""
    service_slug = (
        RESUME_OPTIMIZATION_WITH_EMAIL_SERVICE_SLUG
        if include_email_subject
        else RESUME_OPTIMIZATION_SERVICE_SLUG
    )
    result = run_resume_optimization_generation(
        job_description,
        resume_data,
        service_slug=service_slug,
    )
    if not result.get("success"):
        return result
    return normalize_optimization_result(result)


def normalize_optimization_result(data: dict) -> dict:
    """
    Map common AI / JSON key aliases onto fields dashboard expects.
    (Kept for compatibility with older parsed shapes.)
    """
    if not data:
        return data
    d = dict(data)

    opt = d.get("optimized_summary")
    has_summary = isinstance(opt, str) and bool(opt.strip())
    if not has_summary:
        for k in (
            "Professional Summary",
            "professional_summary",
            "Summary",
            "summary",
        ):
            v = d.get(k)
            if isinstance(v, str) and v.strip():
                d["optimized_summary"] = v.strip()
                break

    if d.get("reordered_technical_skills") is None:
        skills = (
            d.get("Skills")
            or d.get("skills")
            or d.get("technical_skills")
            or d.get("Technical Skills")
        )
        if isinstance(skills, list) and skills:
            d["reordered_technical_skills"] = coerce_skill_list(skills)

    if d.get("reordered_soft_skills") is None:
        ss = d.get("Soft Skills") or d.get("soft_skills") or d.get("Soft skills")
        if isinstance(ss, list) and ss:
            d["reordered_soft_skills"] = coerce_skill_list(ss)

    if d.get("reordered_languages") is None:
        lang = d.get("Languages") or d.get("languages")
        if isinstance(lang, list) and lang:
            d["reordered_languages"] = coerce_skill_list(lang)

    if not d.get("relevant_experience") and d.get("experience"):
        d["relevant_experience"] = d["experience"]

    if d.get("reordered_projects") is None:
        pr = d.get("Projects") or d.get("projects") or d.get("Selected Projects")
        if isinstance(pr, list):
            d["reordered_projects"] = pr

    title = d.get("title") or d.get("resume_title")
    if title:
        d["title"] = title

    return d
