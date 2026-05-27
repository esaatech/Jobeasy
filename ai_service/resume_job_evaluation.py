"""
Resume-to-Job Evaluation Service — pre-flight fit check before optimization / cover letters.

Uses the **provider on the prompt's linked AIModel** (Gemini structured JSON, or
OpenAI / DeepSeek JSON chat). Instruction text is loaded from DB: ``AIService`` slug
``resume_job_evaluation`` and its ``AIPromptConfiguration`` rows. Seed defaults with::

    python manage.py setup_resume_job_evaluation
    python manage.py setup_ai_models
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAIError
from pydantic import ValidationError

from .deepseek_client import get_deepseek_client
from .generation_config import resolve_for_prompt_config
from .gemini_schema import ResumeJobEvaluationPayload
from .gemini_client import gemini_generate_structured_sync
from .models import AIModel, AIService, AIPromptConfiguration, ResumeJobEvaluation
from .open_ai import client

logger = logging.getLogger(__name__)

RESUME_JOB_EVALUATION_SERVICE_SLUG = "resume_job_evaluation"


def parse_pending_evaluation_result(raw: str | None) -> dict[str, Any] | None:
    """Parse ``pending_evaluation_result`` POST JSON from admin Save; None if absent/invalid."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("success") is not True:
        return None
    if not isinstance(data.get("evaluation"), dict):
        return None
    return data


def _parse_temperature_param(raw: str | float | None) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def conclusion_from_evaluation(eval_data: dict[str, Any] | None) -> str:
    """Extract ``proceed_reasoning`` for list/detail labels."""
    if not isinstance(eval_data, dict):
        return ""
    dims = eval_data.get("dimension_summaries")
    if not isinstance(dims, dict):
        return ""
    return str(dims.get("proceed_reasoning") or "").strip()[:8000]


def persist_resume_job_evaluation_result(
    pk: object,
    *,
    result: dict[str, Any],
    prompt_config: AIPromptConfiguration | None,
    fallback_gemini_model_id: str,
) -> None:
    """Persist fields on ``ResumeJobEvaluation`` after ``evaluate_resume_against_job`` returns."""
    pc = prompt_config
    model_mid = str(
        result.get("model_id")
        or result.get("gemini_model")
        or result.get("openai_model")
        or result.get("deepseek_model")
        or fallback_gemini_model_id
    )[:128]
    eval_data = result.get("evaluation") if result.get("success") else None
    raw_text = result.get("raw_text") or ""
    if raw_text:
        raw_text = raw_text[:262144]

    rec = ""
    overall_int = None
    opt_int = None
    if isinstance(eval_data, dict):
        raw_rec = str(eval_data.get("recommendation") or "").strip()
        rec = raw_rec[:128]
        ov = eval_data.get("overall_score")
        op_w = eval_data.get("optimization_potential")
        try:
            overall_int = int(float(ov)) if ov not in (None, "") else None
        except (TypeError, ValueError):
            overall_int = None
        try:
            opt_int = int(float(op_w)) if op_w not in (None, "") else None
        except (TypeError, ValueError):
            opt_int = None
        if overall_int is not None:
            overall_int = max(0, min(100, overall_int))
        if opt_int is not None:
            opt_int = max(0, min(100, opt_int))

    slug_snap = (
        result.get("instruction_slug") or (pc.slug if pc else "") or ""
    )[:80]

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

    update_fields: dict[str, Any] = {
        "succeeded": result["success"],
        "error_message": str(result.get("error") or "")[:8000],
        "evaluation_json": eval_data,
        "raw_response_text": raw_text,
        "recommendation": rec,
        "overall_score": overall_int if result["success"] else None,
        "optimization_potential": opt_int if result["success"] else None,
        "instruction_slug": slug_snap,
        "gemini_model": model_mid,
        "ai_model_id": ai_model_pk,
        "temperature_used": temp_used,
        "prompt_config_id": result.get("prompt_config_id") or (pc.pk if pc else None),
    }
    if result["success"]:
        ai_conclusion = conclusion_from_evaluation(eval_data)
        if ai_conclusion:
            update_fields["conclusion"] = ai_conclusion

    ResumeJobEvaluation.objects.filter(pk=pk).update(**update_fields)


def _summarize_validation_error(exc: ValidationError) -> str:
    bits: list[str] = []
    for err in exc.errors():
        loc = err.get("loc") or ()
        path = ".".join(str(x) for x in loc)
        msg = err.get("msg", "")
        bits.append(f"{path}: {msg}" if path else msg)
    return "; ".join(bits) if bits else str(exc)


def resolve_prompt_config(prompt_config_pk: int | None) -> AIPromptConfiguration | None:
    if not prompt_config_pk:
        return None
    return (
        AIPromptConfiguration.objects.filter(
            pk=prompt_config_pk,
            is_active=True,
            service__slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
            service__is_active=True,
        )
        .select_related("service", "ai_model")
        .first()
    )


def get_default_prompt_config() -> AIPromptConfiguration | None:
    svc = AIService.objects.filter(
        slug=RESUME_JOB_EVALUATION_SERVICE_SLUG, is_active=True
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
    return f"""JOB DESCRIPTION:\n---\n{jd}\n---\n\nCANDIDATE RESUME:\n---\n{rs}\n---"""


def normalize_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    """Light normalization of model output aliases."""
    out = dict(payload)
    aliases = (
        ("Overall Score", "overall_score"),
        ("Recommendation", "recommendation"),
        ("optimization potential", "optimization_potential"),
    )
    for bad_key, canon in aliases:
        if canon not in out and bad_key in out:
            out[canon] = out.get(bad_key)
    return out


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


def _coerce_evaluation_dict(data: Any, raw: str | None) -> dict[str, Any]:
    if isinstance(data, ResumeJobEvaluationPayload):
        return data.model_dump(mode="json")
    if isinstance(data, dict):
        return data
    if raw:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Model structured response missing a JSON object.")


def _validate_evaluation_payload(
    data: dict[str, Any],
    *,
    raw: str | None,
    base_meta: dict[str, Any],
) -> dict[str, Any]:
    try:
        data = normalize_evaluation(data)
        payload = ResumeJobEvaluationPayload.model_validate(data)
    except ValidationError as exc:
        err = _summarize_validation_error(exc)
        logger.warning("resume_job_evaluation: output failed schema validation: %s", err)
        return {
            "success": False,
            "evaluation": None,
            "error": f"Output failed schema validation: {err}",
            "raw_text": raw,
            **base_meta,
        }
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        err = str(exc)
        logger.warning("resume_job_evaluation: parse/validate error: %s", err)
        return {
            "success": False,
            "evaluation": None,
            "error": err,
            "raw_text": raw,
            **base_meta,
        }

    return {
        "success": True,
        "evaluation": payload.model_dump(mode="json"),
        "error": None,
        "raw_text": raw,
        **base_meta,
    }


def _generate_with_gemini(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[dict[str, Any], str | None]:
    out = gemini_generate_structured_sync(
        system_instruction=system_instruction,
        user_text=user_block,
        model_id=gen.model_id,
        temperature=gen.temperature,
        response_schema=ResumeJobEvaluationPayload,
    )
    raw = out.get("raw")
    if isinstance(raw, str):
        raw_text: str | None = raw
    elif raw is not None:
        raw_text = json.dumps(raw)
    else:
        raw_text = None
    data = _coerce_evaluation_dict(out.get("parsed"), raw_text)
    return data, raw_text


def _generate_with_openai_json(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[dict[str, Any], str | None]:
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
    data = _coerce_evaluation_dict(json.loads(raw) if raw else None, raw or None)
    return data, raw or None


def _generate_with_deepseek_json(
    *,
    system_instruction: str,
    user_block: str,
    gen,
) -> tuple[dict[str, Any], str | None]:
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
    data = _coerce_evaluation_dict(json.loads(raw) if raw else None, raw or None)
    return data, raw or None


def evaluate_resume_against_job(
    job_description: str,
    resume_text: str,
    *,
    prompt_config: AIPromptConfiguration | None = None,
    ai_model_id: int | None = None,
    temperature: float | None = None,
    gemini_model: str | None = None,
    model_id_override: str | None = None,
) -> dict[str, Any]:
    """Run evaluation. Returns a dict with keys: success, evaluation, error, raw_text."""

    cfg = prompt_config or get_default_prompt_config()
    if cfg is None:
        return {
            "success": False,
            "evaluation": None,
            "error": (
                "No prompt configuration found for slug "
                f"'{RESUME_JOB_EVALUATION_SERVICE_SLUG}'. "
                "Run: python manage.py setup_resume_job_evaluation"
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
            data, raw = _generate_with_gemini(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        elif provider == AIModel.Provider.DEEPSEEK:
            data, raw = _generate_with_deepseek_json(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
        else:
            data, raw = _generate_with_openai_json(
                system_instruction=system_instruction,
                user_block=user_block,
                gen=gen,
            )
    except (OpenAIError, json.JSONDecodeError, ValueError, TypeError, Exception) as exc:
        logger.exception("resume_job_evaluation: %s call failed", provider)
        return {
            "success": False,
            "evaluation": None,
            "error": str(exc),
            "raw_text": raw,
            **base_meta,
        }

    return _validate_evaluation_payload(data, raw=raw, base_meta=base_meta)
