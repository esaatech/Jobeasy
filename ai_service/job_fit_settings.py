"""Singleton job-fit gate configuration for the dashboard."""

from __future__ import annotations

from django.db import transaction

from .models import JobFitGateSettings

SINGLETON_PK = 1

DEFAULT_GREEN_MIN_SCORE = 70
DEFAULT_YELLOW_MIN_SCORE = 50


def get_job_fit_gate_settings() -> JobFitGateSettings:
    """Return the singleton gate settings row (creates defaults if missing)."""
    settings, _created = JobFitGateSettings.objects.select_related(
        "prompt_config",
        "prompt_config__ai_model",
    ).get_or_create(
        pk=SINGLETON_PK,
        defaults={
            "is_enabled": True,
            "green_min_score": DEFAULT_GREEN_MIN_SCORE,
            "yellow_min_score": DEFAULT_YELLOW_MIN_SCORE,
        },
    )
    return settings


@transaction.atomic
def ensure_job_fit_gate_settings(
    *,
    prompt_config_id: int | None = None,
) -> JobFitGateSettings:
    """Idempotent setup helper used by management command."""
    defaults: dict = {
        "is_enabled": True,
        "green_min_score": DEFAULT_GREEN_MIN_SCORE,
        "yellow_min_score": DEFAULT_YELLOW_MIN_SCORE,
    }
    if prompt_config_id is not None:
        defaults["prompt_config_id"] = prompt_config_id

    settings, created = JobFitGateSettings.objects.get_or_create(
        pk=SINGLETON_PK,
        defaults=defaults,
    )
    if not created and prompt_config_id and settings.prompt_config_id is None:
        settings.prompt_config_id = prompt_config_id
        settings.save(update_fields=["prompt_config_id", "updated_at"])
    return settings
