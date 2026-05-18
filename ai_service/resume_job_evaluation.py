"""
Resume-to-Job Evaluation Service — pre-flight fit check before optimization / cover letters.

Uses **Google Gemini** via ``google-genai`` (bundled with ``google-adk``).

Instruction text is loaded from DB: ``AIService`` slug ``resume_job_evaluation`` and its
``AIPromptConfiguration`` rows. Seed defaults with::

    python manage.py setup_resume_job_evaluation
    python manage.py setup_ai_models
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from .generation_config import GenerationConfig, resolve_generation_config
from .gemini_schema import ResumeJobEvaluationPayload
from .gemini_client import gemini_generate_structured_sync
from .models import AIService, AIPromptConfiguration, ResumeJobEvaluation

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
    gemini_mid = str(result.get("gemini_model") or fallback_gemini_model_id)[:128]
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
        "gemini_model": gemini_mid,
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


def _meta_from_config(cfg: AIPromptConfiguration, gen: GenerationConfig) -> dict[str, Any]:
    return {
        "prompt_config_id": cfg.pk,
        "instruction_slug": cfg.slug,
        "gemini_model": gen.model_id,
        "ai_model_id": gen.ai_model_id,
        "temperature": gen.temperature,
    }


def evaluate_resume_against_job(
    job_description: str,
    resume_text: str,
    *,
    prompt_config: AIPromptConfiguration | None = None,
    ai_model_id: int | None = None,
    temperature: float | None = None,
    gemini_model: str | None = None,
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

    gen = resolve_generation_config(
        cfg,
        ai_model_id=ai_model_id,
        temperature=temperature,
        model_id_override=gemini_model,
    )

    system_instruction = cfg.system_prompt.strip()
    user_block = build_user_prompt(job_description, resume_text)

    raw: str | None = None
    base_meta = _meta_from_config(cfg, gen)

    try:
        out = gemini_generate_structured_sync(
            system_instruction=system_instruction,
            user_text=user_block,
            model_id=gen.model_id,
            temperature=gen.temperature,
            response_schema=ResumeJobEvaluationPayload,
        )
        raw = out["raw"]
        data = out.get("parsed")
        if not isinstance(data, dict):
            raise ValueError("Model structured response missing a JSON object.")

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
    except (ValueError, TypeError) as exc:
        err = str(exc)
        logger.warning("resume_job_evaluation: parse/validate error: %s", err)
        return {
            "success": False,
            "evaluation": None,
            "error": err,
            "raw_text": raw,
            **base_meta,
        }
    except Exception as exc:
        logger.exception("resume_job_evaluation: Gemini call failed")
        return {
            "success": False,
            "evaluation": None,
            "error": str(exc),
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
