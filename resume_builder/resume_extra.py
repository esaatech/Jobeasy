"""Validation and merging for structured JSON fields on Resume (references, rated skills)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def coerce_references_list(raw: Any, *, limit: int = 12) -> List[Dict[str, str]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, str]] = []
    for item in raw[:limit]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": str(item.get("name", "") or "")[:140],
                "affiliation": str(item.get("affiliation", "") or "")[:240],
                "email": str(item.get("email", "") or "")[:140],
                "phone": str(item.get("phone", "") or "")[:48],
            }
        )
        if all(not v.strip() for v in out[-1].values()):
            out.pop()
    return out


def coerce_rated_skills(raw: Any, *, limit: int = 16) -> List[Dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw[:limit]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or "").strip()
        if not name:
            continue
        level = item.get("level", 7)
        try:
            lvl = int(level)
        except (TypeError, ValueError):
            lvl = 7
        lvl = max(1, min(10, lvl))
        out.append({"name": name[:120], "level": lvl})
    return out


def merge_additional_payload(
    previous: Optional[Dict[str, Any]], payload: Dict[str, Any]
) -> Dict[str, Any]:
    base = dict(previous or {})
    if "certifications" in payload:
        base["certifications"] = payload.get("certifications") or ""
    if "projects" in payload:
        base["projects"] = payload.get("projects") or ""
    if "references" in payload:
        base["references"] = coerce_references_list(payload.get("references"))
    return base


def merge_skills_payload(
    previous: Optional[Dict[str, Any]],
    *,
    technical: List[str],
    soft: List[str],
    languages: List[str],
    rated_raw: Optional[Any] = ...,
) -> Dict[str, Any]:
    prev = dict(previous or {})
    out = {
        **prev,
        "technical": technical,
        "soft": soft,
        "languages": languages,
    }
    if rated_raw is not ...:
        out["rated"] = coerce_rated_skills(rated_raw)
    else:
        out["rated"] = prev.get("rated", [])
    return out
