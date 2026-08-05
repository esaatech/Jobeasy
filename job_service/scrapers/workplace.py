"""Heuristics to classify remote / hybrid / onsite from ATS fields and location text."""

from __future__ import annotations

import re

WORK_ARRANGEMENT_REMOTE = 'remote'
WORK_ARRANGEMENT_HYBRID = 'hybrid'
WORK_ARRANGEMENT_ONSITE = 'onsite'
WORK_ARRANGEMENT_UNKNOWN = 'unknown'

VALID_WORK_ARRANGEMENTS = frozenset({
    WORK_ARRANGEMENT_REMOTE,
    WORK_ARRANGEMENT_HYBRID,
    WORK_ARRANGEMENT_ONSITE,
    WORK_ARRANGEMENT_UNKNOWN,
})

_HYBRID_RE = re.compile(
    r'\bhybrid\b|\bpartial(?:ly)?\s+remote\b|\bremote[-\s]?friendly\b',
    re.IGNORECASE,
)
_REMOTE_RE = re.compile(
    r'\bremote\b|\bwork\s+from\s+home\b|\bwfh\b|\banywhere\b|\bdistributed\b',
    re.IGNORECASE,
)
_ONSITE_RE = re.compile(
    r'\bon[-\s]?site\b|\bin[-\s]?office\b|\bin[-\s]?person\b',
    re.IGNORECASE,
)

_STRUCTURED_MAP = {
    'remote': WORK_ARRANGEMENT_REMOTE,
    'fully remote': WORK_ARRANGEMENT_REMOTE,
    'full remote': WORK_ARRANGEMENT_REMOTE,
    'work from home': WORK_ARRANGEMENT_REMOTE,
    'wfh': WORK_ARRANGEMENT_REMOTE,
    'hybrid': WORK_ARRANGEMENT_HYBRID,
    'flexible': WORK_ARRANGEMENT_HYBRID,
    'partially remote': WORK_ARRANGEMENT_HYBRID,
    'onsite': WORK_ARRANGEMENT_ONSITE,
    'on-site': WORK_ARRANGEMENT_ONSITE,
    'on site': WORK_ARRANGEMENT_ONSITE,
    'office': WORK_ARRANGEMENT_ONSITE,
    'in-office': WORK_ARRANGEMENT_ONSITE,
    'in office': WORK_ARRANGEMENT_ONSITE,
    'in-person': WORK_ARRANGEMENT_ONSITE,
}


def classify_from_text(*parts: str | None) -> str:
    """Classify workplace mode from free-text location / tags / labels."""
    blob = ' '.join(p for p in parts if p).strip()
    if not blob:
        return WORK_ARRANGEMENT_UNKNOWN

    if _HYBRID_RE.search(blob):
        return WORK_ARRANGEMENT_HYBRID
    if _REMOTE_RE.search(blob):
        return WORK_ARRANGEMENT_REMOTE
    if _ONSITE_RE.search(blob):
        return WORK_ARRANGEMENT_ONSITE

    # Non-empty location without remote/hybrid markers → treat as on-site.
    if blob.lower() not in {'unspecified', 'n/a', 'na', 'none', 'tbd'}:
        return WORK_ARRANGEMENT_ONSITE

    return WORK_ARRANGEMENT_UNKNOWN


def classify_from_structured(value: str | None) -> str | None:
    """Map a structured ATS workplace label; return None if unrecognized."""
    if not value:
        return None
    mapped = _STRUCTURED_MAP.get(value.strip().lower())
    return mapped


def classify_ashby(*, is_remote: bool | None, workplace_type: str | None, location: str) -> str:
    structured = classify_from_structured(workplace_type)
    if structured:
        return structured
    if is_remote is True:
        return WORK_ARRANGEMENT_REMOTE
    if is_remote is False and location and location.lower() not in {
        'unspecified', 'remote', 'n/a', 'na',
    }:
        return WORK_ARRANGEMENT_ONSITE
    return classify_from_text(location, workplace_type)
