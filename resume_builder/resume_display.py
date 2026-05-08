"""Augment resume dict snapshots for HTML/PDF rendering (display-only fields)."""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from django.http import HttpRequest

from .profile_photo_media import resolve_profile_photo_display_url


def augment_resume_dict_for_rendering(
    resume_data: Dict[str, Any], *, request: Optional[HttpRequest] = None
) -> Dict[str, Any]:
    data = copy.deepcopy(resume_data)
    pi = data.setdefault("personal_info", {})
    existing_preview = pi.get("profile_photo_display_url")
    computed = resolve_profile_photo_display_url(pi, request=request)
    pi["profile_photo_display_url"] = computed or (existing_preview if isinstance(existing_preview, str) else "") or ""

    skills = data.setdefault("skills", {})
    if not skills.get("rated") and skills.get("technical"):
        skills["rated"] = [
            {"name": str(name), "level": 7} for name in skills["technical"][:14]
        ]
    return data
