"""Validation and merging for structured JSON fields on Resume (references, rated skills)."""

from __future__ import annotations

import re
from html import unescape
from typing import Any, Dict, List, Optional

from django.utils.html import escape


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


def _strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def extract_project_bullets_from_html(html: str) -> List[str]:
    """
    Parse CKEditor / template HTML under additional.projects into plain bullet lines.
    Used so job optimization can reorder projects and write back HTML.
    """
    if not html:
        return []
    s = str(html).strip()
    if not s:
        return []
    items = re.findall(r"<li[^>]*>(.*?)</li>", s, flags=re.I | re.S)
    if items:
        out: List[str] = []
        for x in items:
            t = _strip_html_tags(unescape(x)).strip()
            if t:
                out.append(t)
        return out
    paras = re.findall(r"<p[^>]*>(.*?)</p>", s, flags=re.I | re.S)
    if paras:
        out = []
        for x in paras:
            t = _strip_html_tags(unescape(x)).strip()
            if t:
                out.append(t)
        return out
    plain = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    plain = _strip_html_tags(unescape(plain))
    return [ln.strip() for ln in plain.splitlines() if ln.strip()]


def bullets_to_projects_html(bullets: List[str]) -> str:
    """Build minimal list HTML for resume templates (additional.projects|safe)."""
    if not bullets:
        return ""
    parts: List[str] = []
    for b in bullets:
        text = str(b).strip()
        if not text:
            continue
        parts.append(f"<li>{escape(text)}</li>")
    if not parts:
        return ""
    return "<ul>" + "".join(parts) + "</ul>"


_BULLET_PREFIX_RE = re.compile(r"^[\s•●▪◦‣⁃\-–—*]+")
_NUMBERED_PREFIX_RE = re.compile(r"^\s*\d+[\.\)]\s+")


def plain_text_to_bullet_lines(text: str) -> List[str]:
    """Split AI or plain-text experience copy into bullet lines."""
    s = (text or "").strip()
    if not s:
        return []
    if re.search(r"<li[\s>]", s, re.I):
        return extract_project_bullets_from_html(s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = _strip_html_tags(unescape(s))
    lines: List[str] = []
    for raw in s.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = _BULLET_PREFIX_RE.sub("", line)
        line = _NUMBERED_PREFIX_RE.sub("", line).strip()
        if line:
            lines.append(line)
    if lines:
        return lines
    # Single paragraph: treat as one bullet (templates need at least one <li>)
    return [s] if s else []


def normalize_experience_description(
    description: str,
    *,
    fallback_html: str = "",
) -> str:
    """
    Ensure experience ``description`` is ``<ul><li>…</li></ul>`` for resume templates.

    Preserves list rendering when the model returns plain text or markdown-style bullets.
    """
    bullets = plain_text_to_bullet_lines(description)
    if bullets:
        return bullets_to_projects_html(bullets)
    fallback = (fallback_html or "").strip()
    if fallback and re.search(r"<li[\s>]", fallback, re.I):
        return fallback
    if fallback:
        return normalize_experience_description(fallback)
    return ""


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
