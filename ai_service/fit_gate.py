"""Dashboard job-fit tier rules (reads JobFitGateSettings + evaluation payload)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .models import JobFitGateSettings

FitTier = Literal["bypass", "green", "yellow", "red"]

GREEN_RECOMMENDATIONS = frozenset({"Strong Fit", "Good Fit"})
YELLOW_RECOMMENDATIONS = frozenset({"Moderate Fit", "Weak Fit"})
RED_RECOMMENDATIONS = frozenset({"Poor Fit"})


def _score_tier(score: int | None, settings: JobFitGateSettings) -> FitTier:
    if score is None:
        return "yellow"
    if score >= settings.green_min_score:
        return "green"
    if score >= settings.yellow_min_score:
        return "yellow"
    return "red"


def _recommendation_tier(recommendation: str) -> FitTier:
    rec = (recommendation or "").strip()
    if rec in GREEN_RECOMMENDATIONS:
        return "green"
    if rec in YELLOW_RECOMMENDATIONS:
        return "yellow"
    if rec in RED_RECOMMENDATIONS:
        return "red"
    return "yellow"


def _stricter(a: FitTier, b: FitTier) -> FitTier:
    order = {"bypass": 0, "green": 1, "yellow": 2, "red": 3}
    return a if order[a] >= order[b] else b


def classify_fit_tier(
    evaluation: dict[str, Any] | None,
    settings: JobFitGateSettings,
) -> FitTier:
    """
    Classify fit for dashboard routing. Uses the stricter of score-based and
    recommendation-based tiers when both apply.
    """
    if not settings.is_enabled:
        return "bypass"
    if not isinstance(evaluation, dict):
        return "red"

    score = evaluation.get("overall_score")
    try:
        score_int = int(score) if score is not None else None
    except (TypeError, ValueError):
        score_int = None

    by_score = _score_tier(score_int, settings)
    by_rec = _recommendation_tier(str(evaluation.get("recommendation") or ""))
    tier = _stricter(by_score, by_rec)

    # Poor Fit must not auto-proceed on score alone
    rec = str(evaluation.get("recommendation") or "").strip()
    if rec in RED_RECOMMENDATIONS:
        return "red"
    if rec in GREEN_RECOMMENDATIONS and score_int is not None and score_int < settings.green_min_score:
        return "yellow"
    return tier


def tier_allows_auto_proceed(tier: FitTier) -> bool:
    return tier == "green"


def tier_allows_proceed_with_override(tier: FitTier) -> bool:
    return tier in ("yellow", "red")


def evaluation_summary(evaluation: dict[str, Any] | None) -> dict[str, Any]:
    """User-facing subset for dashboard JSON."""
    if not isinstance(evaluation, dict):
        return {}
    dims = evaluation.get("dimension_summaries")
    proceed = ""
    if isinstance(dims, dict):
        proceed = str(dims.get("proceed_reasoning") or "").strip()
    gaps = evaluation.get("gaps")
    strengths = evaluation.get("strengths")
    return {
        "overall_score": evaluation.get("overall_score"),
        "recommendation": evaluation.get("recommendation"),
        "confidence": evaluation.get("confidence"),
        "risk_level": evaluation.get("risk_level"),
        "optimization_potential": evaluation.get("optimization_potential"),
        "proceed_reasoning": proceed,
        "gaps": gaps if isinstance(gaps, list) else [],
        "strengths": strengths if isinstance(strengths, list) else [],
    }
