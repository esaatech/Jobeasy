"""Augment resume dict snapshots for HTML/PDF rendering (display-only fields)."""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from django.http import HttpRequest

from .profile_photo_media import (
    has_stored_profile_photo,
    resolve_profile_photo_display_url,
)


def augment_resume_dict_for_rendering(
    resume_data: Dict[str, Any],
    *,
    request: Optional[HttpRequest] = None,
    resume_id: Optional[int] = None,
    force_inline_profile_photo: bool = False,
    cache_version: str = "",
) -> Dict[str, Any]:
    data = copy.deepcopy(resume_data)
    pi = data.setdefault("personal_info", {})
    transient = pi.pop("profile_photo_display_url", None) or pi.pop("profilePhotoDisplayUrl", None)
    computed = resolve_profile_photo_display_url(
        pi,
        request=request,
        resume_id=resume_id,
        force_inline_from_storage=force_inline_profile_photo,
        cache_version=cache_version,
    )
    if computed:
        pi["profile_photo_display_url"] = computed
    elif (
        isinstance(transient, str)
        and transient
        and not has_stored_profile_photo(pi)
        and (transient.startswith("data:") or transient.startswith("http"))
    ):
        # In-memory wizard preview only (anonymous or not yet uploaded); never read from DB.
        pi["profile_photo_display_url"] = transient
    else:
        pi["profile_photo_display_url"] = ""

    skills = data.setdefault("skills", {})
    if not skills.get("rated") and skills.get("technical"):
        skills["rated"] = [
            {"name": str(name), "level": 7} for name in skills["technical"][:14]
        ]
    return data
