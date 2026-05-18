"""
Backward-compatible import path.

Canonical definitions live in :mod:`ai_service.gemini_schema`; new code should import from there.

``from ai_service.eval_schema import ResumeJobEvaluationPayload`` continues to work.
"""

from .gemini_schema import (
    ConfidenceLabel,
    DimensionSummaries,
    HardRequirementRow,
    MatchStatus,
    RecommendationLabel,
    ResumeJobEvaluationPayload,
    RiskLevelLabel,
    TransferableSkillRow,
)

__all__ = [
    "ConfidenceLabel",
    "DimensionSummaries",
    "HardRequirementRow",
    "MatchStatus",
    "RecommendationLabel",
    "ResumeJobEvaluationPayload",
    "RiskLevelLabel",
    "TransferableSkillRow",
]
