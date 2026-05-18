"""
Structured output schemas **for Gemini** (distinct from e.g. ``task_schema`` elsewhere).

Module :mod:`ai_service.gemini_schema` holds Pydantic models and literals you pass as
``response_schema`` or validate after :func:`ai_service.gemini_client.gemini_generate_structured_sync`
/ :meth:`GeminiService.generate` (see ``gemini_service`` / ``gemini_client``).

**Resume vs job evaluation:** ``ResumeJobEvaluationPayload`` is the validated shape persisted
to ``ResumeJobEvaluation.evaluation_json``. System prompts must stay aligned with these models.

New Gemini-returned shapes should live here so OpenAI/Task flows stay separated by filename.

Literals exposed for validators and prompts:

``MatchStatus``, ``RecommendationLabel``, ``ConfidenceLabel``, ``RiskLevelLabel``
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MatchStatus = Literal[
    "met",
    "partially_met",
    "transferable",
    "missing",
    "unclear",
    "unrecoverable",
]

RecommendationLabel = Literal[
    "Strong Fit",
    "Good Fit",
    "Moderate Fit",
    "Weak Fit",
    "Poor Fit",
]

ConfidenceLabel = Literal["High", "Medium", "Low"]
RiskLevelLabel = Literal["Low", "Moderate", "High"]

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


class HardRequirementRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requirement: str
    match_status: MatchStatus
    evidence_quote: str = ""
    notes: str = ""


class TransferableSkillRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    from_skill: str = ""
    adjacent_skill: str = ""
    evidence_quote: str = ""
    notes: str = ""


class DimensionSummaries(BaseModel):
    model_config = ConfigDict(extra="ignore")

    core_competency_match: str = ""
    seniority_match: str = ""
    domain_match: str = ""
    operational_experience_match: str = ""
    optimization_surface_vs_foundational_notes: str = ""
    proceed_reasoning: str = ""


class ResumeJobEvaluationPayload(BaseModel):
    """Validated shape returned by Gemini for resume–job fit and stored as ``evaluation_json``."""

    model_config = ConfigDict(extra="ignore")

    overall_score: int = Field(ge=0, le=100)
    recommendation: RecommendationLabel
    optimization_potential: int = Field(ge=0, le=100)
    confidence: ConfidenceLabel
    strengths: list[str]
    gaps: list[str]
    hard_requirement_analysis: list[HardRequirementRow]
    transferable_skills: list[TransferableSkillRow]
    risk_level: RiskLevelLabel
    dimension_summaries: DimensionSummaries
