"""Thin product wrapper — delegates to ai_service.title_family platform runner."""

from __future__ import annotations

from ai_service.title_family import generate_title_family
from utils.resume_text import build_resume_text_for_evaluation


def generate_title_family_from_resume(resume) -> dict[str, list[str]]:
    """
    Suggest primary / related / exclude titles from a resume via the AI platform.

    Raises ValueError when the platform returns success=False.
    """
    resume_text = build_resume_text_for_evaluation(resume)
    if not resume_text.strip():
        raise ValueError("Resume has no usable text to analyze.")

    result = generate_title_family(resume_text)
    if not result.get("success"):
        raise ValueError(result.get("error") or "Title family generation failed.")

    return {
        "primary_titles": list(result.get("primary_titles") or []),
        "related_titles": list(result.get("related_titles") or []),
        "exclude_titles": list(result.get("exclude_titles") or []),
    }
