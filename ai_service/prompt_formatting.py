"""Helpers to turn resume-shaped data into safe text for LLM prompts (no str.join on dicts)."""

from __future__ import annotations

import json
from typing import Any, List


def format_items_for_prompt(items: Any) -> str:
    """
    Build comma-separated text from a skill-like list that may contain strings or dicts
    (e.g. {'name': 'Python'} or {'skill': 'Django'}).
    """
    if items is None:
        return ""
    if not isinstance(items, list):
        return str(items)
    parts: List[str] = []
    for x in items:
        if isinstance(x, str):
            parts.append(x)
        elif isinstance(x, dict):
            name = x.get("name") or x.get("skill") or x.get("label") or x.get("title")
            if name:
                parts.append(str(name))
            else:
                parts.append(json.dumps(x, ensure_ascii=False))
        else:
            parts.append(str(x))
    return ", ".join(parts)


def format_bullet_item(item: Any) -> str:
    """Single achievement / bullet line for resume text dumps."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        text = item.get("text") or item.get("description") or item.get("achievement")
        if text:
            return str(text)
        return json.dumps(item, ensure_ascii=False)
    return str(item)


def coerce_skill_list(skills: Any) -> List[str]:
    """Normalize a skill list to plain strings for JSONField storage."""
    if not isinstance(skills, list):
        return []
    out: List[str] = []
    for s in skills:
        if isinstance(s, str):
            out.append(s)
        elif isinstance(s, dict):
            name = s.get("name") or s.get("skill") or s.get("label")
            out.append(str(name) if name else json.dumps(s, ensure_ascii=False))
        else:
            out.append(str(s))
    return out
