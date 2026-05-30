"""Validate AI resume optimization output against source resume data (anti-hallucination)."""

from __future__ import annotations

import re
from typing import Any

from resume_builder.resume_extra import normalize_experience_description

from .gemini_schema import OptimizedExperienceRow, ResumeOptimizationPayload
from .prompt_formatting import coerce_skill_list


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _exp_key(entry: dict) -> tuple[str, str]:
    company = _norm(str(entry.get("company") or ""))
    title = _norm(str(entry.get("title") or entry.get("position") or ""))
    return company, title


def _skill_set(items: list) -> set[str]:
    return {_norm(str(x)) for x in coerce_skill_list(items) if _norm(str(x))}


def _filter_skills_to_source(output: list, source: list) -> list:
    allowed = _skill_set(source)
    kept = []
    for item in coerce_skill_list(output):
        if _norm(str(item)) in allowed:
            kept.append(str(item).strip())
    if not kept:
        return list(coerce_skill_list(source))
    return kept


def _validate_projects(source_bullets: list[str], output_bullets: list) -> list[str]:
    src = [str(b).strip() for b in source_bullets if str(b).strip()]
    out = [str(b).strip() for b in output_bullets if str(b).strip()]
    if not src:
        return []
    if not out:
        return src
    src_norm = {_norm(b): b for b in src}
    out_norms = [_norm(b) for b in out]
    if sorted(out_norms) == sorted(src_norm.keys()):
        return out
    # Allow same multiset with light rewording: each output must map to one source bullet
    used: set[str] = set()
    rebuilt: list[str] = []
    for ob in out:
        on = _norm(ob)
        matched = None
        for sn, orig in src_norm.items():
            if sn in used:
                continue
            if on == sn or on in sn or sn in on:
                matched = orig
                used.add(sn)
                break
        if matched:
            rebuilt.append(ob)
        else:
            return src
    if len(rebuilt) != len(src):
        return src
    return rebuilt


def merge_experience(
    source_experience: list[dict],
    ai_rows: list[OptimizedExperienceRow] | list[dict],
) -> list[dict]:
    """Keep source metadata; apply rewritten descriptions when index and employer/title match."""
    if not source_experience:
        return []
    ai_list = []
    for row in ai_rows or []:
        if isinstance(row, OptimizedExperienceRow):
            ai_list.append(row.model_dump())
        elif isinstance(row, dict):
            ai_list.append(row)

    if len(ai_list) != len(source_experience):
        return [dict(e) for e in source_experience]

    merged: list[dict] = []
    for i, src in enumerate(source_experience):
        base = dict(src) if isinstance(src, dict) else {}
        ai = ai_list[i] if i < len(ai_list) else {}
        if _exp_key(base) != _exp_key(ai):
            merged.append(base)
            continue
        desc = (ai.get("description") or "").strip()
        if desc:
            base["description"] = normalize_experience_description(
                desc,
                fallback_html=str(base.get("description") or ""),
            )
        merged.append(base)
    return merged


def validate_and_merge_payload(
    payload: ResumeOptimizationPayload,
    source: dict[str, Any],
) -> dict[str, Any]:
    """
    Return a flat dict for dashboard ``_optimize_resume_for_job_application``,
    with hallucinated fields corrected against ``source``.
    """
    src_exp = list(source.get("experience") or [])
    src_tech = list(source.get("technical_skills") or [])
    src_soft = list(source.get("soft_skills") or [])
    src_lang = list(source.get("languages") or [])
    src_projects = list(source.get("projects") or [])

    summary = (payload.optimized_summary or "").strip()
    if not summary:
        summary = (source.get("professional_summary") or "").strip()

    merged_exp = merge_experience(src_exp, payload.experience)

    return {
        "title": (payload.resume_title or "").strip() or "Optimized Resume",
        "email_subject": (payload.email_subject or "").strip(),
        "optimized_summary": summary,
        "reordered_technical_skills": _filter_skills_to_source(
            payload.reordered_technical_skills, src_tech
        ),
        "reordered_soft_skills": _filter_skills_to_source(
            payload.reordered_soft_skills, src_soft
        ),
        "reordered_languages": _filter_skills_to_source(
            payload.reordered_languages, src_lang
        ),
        "experience": merged_exp,
        "relevant_experience": merged_exp,
        "reordered_projects": _validate_projects(src_projects, payload.reordered_projects),
        "ats_score": max(0, min(100, int(payload.ats_score or 0))),
        "keyword_matches": [str(k).strip() for k in (payload.keyword_matches or []) if str(k).strip()],
        "improvement_suggestions": [
            str(s).strip() for s in (payload.improvement_suggestions or []) if str(s).strip()
        ],
    }
