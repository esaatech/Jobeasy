"""Resolve model id and temperature for Gemini (and future providers)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from .models import AIModel, AIPromptConfiguration


@dataclass(frozen=True)
class GenerationConfig:
    model_id: str
    temperature: float
    ai_model_id: int | None = None
    ai_model_display_name: str = ""


def _clamp_temperature(value: float) -> float:
    return max(0.0, min(2.0, float(value)))


def _settings_fallback_model_id() -> str:
    mid = getattr(settings, "GEMINI_RESUME_JOB_EVAL_MODEL", "gemini-2.5-flash")
    return str(mid).strip() or "gemini-2.5-flash"


def _settings_fallback_temperature() -> float:
    return _clamp_temperature(
        float(getattr(settings, "GEMINI_RESUME_JOB_EVAL_TEMPERATURE", 0.35))
    )


def resolve_ai_model(
    *,
    ai_model_id: int | None = None,
    model_id_override: str | None = None,
) -> AIModel | None:
    from .models import AIModel

    if ai_model_id:
        return AIModel.objects.filter(pk=ai_model_id, is_active=True).first()
    if model_id_override:
        mid = str(model_id_override).strip()
        if mid:
            return AIModel.objects.filter(
                provider=AIModel.Provider.GEMINI,
                model_id=mid,
                is_active=True,
            ).first()
    return None


def resolve_generation_config(
    prompt_config: AIPromptConfiguration | None,
    *,
    ai_model_id: int | None = None,
    temperature: float | None = None,
    model_id_override: str | None = None,
) -> GenerationConfig:
    """
    Precedence: per-run overrides > prompt FK > AIModel.default_temperature > settings/env.
    """
    from .models import AIModel

    override_model = resolve_ai_model(
        ai_model_id=ai_model_id,
        model_id_override=model_id_override,
    )

    pc_model = None
    if prompt_config is not None and getattr(prompt_config, "ai_model_id", None):
        pc_model = getattr(prompt_config, "ai_model", None)
        if pc_model is None or not pc_model.is_active:
            pc_model = AIModel.objects.filter(
                pk=prompt_config.ai_model_id,
                is_active=True,
            ).first()

    ai_model = override_model or pc_model

    if ai_model is not None:
        model_id = ai_model.model_id
        display = ai_model.display_name
        model_pk = ai_model.pk
    else:
        model_id = _settings_fallback_model_id()
        display = model_id
        model_pk = None

    if temperature is not None:
        temp = _clamp_temperature(temperature)
    elif prompt_config is not None and prompt_config.temperature is not None:
        temp = _clamp_temperature(float(prompt_config.temperature))
    elif ai_model is not None and ai_model.default_temperature is not None:
        temp = _clamp_temperature(float(ai_model.default_temperature))
    else:
        temp = _settings_fallback_temperature()

    return GenerationConfig(
        model_id=model_id,
        temperature=temp,
        ai_model_id=model_pk,
        ai_model_display_name=display,
    )
