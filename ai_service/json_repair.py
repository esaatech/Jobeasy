"""Best-effort repair for truncated or slightly malformed model JSON."""

from __future__ import annotations

import json
import re
from typing import Any


def repair_truncated_json(text: str) -> str:
    """
    Close a dangling string and balance ``]`` / ``}`` when the model hit output limits.
    """
    t = (text or "").strip()
    if not t:
        return t
    if t.count('"') % 2 == 1:
        t += '"'
    t += "]" * max(0, t.count("[") - t.count("]"))
    t += "}" * max(0, t.count("{") - t.count("}"))
    return t


def truncate_json_before_break(text: str, err: json.JSONDecodeError) -> str:
    """Drop content after the parse failure position and close the object."""
    pos = getattr(err, "pos", None)
    if not isinstance(pos, int) or pos <= 0:
        return repair_truncated_json(text)
    head = text[:pos].rstrip()
    head = re.sub(r",\s*$", "", head)
    return repair_truncated_json(head)


def loads_json_lenient(text: str) -> Any:
    """Parse JSON; attempt repair on decode errors."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        for repaired in (
            repair_truncated_json(cleaned),
            truncate_json_before_break(cleaned, exc),
        ):
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                continue
        raise exc
