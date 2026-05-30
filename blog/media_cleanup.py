"""
Delete blog media files on post update/delete and when inline images are removed from HTML.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable, Set

from django.db.models.fields.files import FieldFile

from .storage import (
    delete_blog_storage_name,
    normalize_storage_name,
    storage_name_from_public_url,
)

logger = logging.getLogger(__name__)

_IMG_SRC_RE = re.compile(
    r"""<img[^>]+src=["']([^"']+)["']""",
    re.IGNORECASE,
)


def extract_blog_media_names_from_html(html: str) -> Set[str]:
    """Collect storage object keys referenced by <img src> in post HTML."""
    if not html:
        return set()
    names: Set[str] = set()
    for match in _IMG_SRC_RE.finditer(html):
        src = match.group(1).strip()
        if not src or src.startswith("data:"):
            continue
        storage_name = storage_name_from_public_url(src)
        if storage_name:
            names.add(storage_name)
    return names


def featured_image_storage_name(featured_image: FieldFile) -> str:
    if not featured_image:
        return ""
    return normalize_storage_name(getattr(featured_image, "name", "") or "")


def delete_blog_media_names(names: Iterable[str]) -> None:
    for name in names:
        delete_blog_storage_name(name)


def cleanup_orphan_body_images(old_body: str, new_body: str) -> None:
    """Remove inline images that were dropped from the article body."""
    old_refs = extract_blog_media_names_from_html(old_body or "")
    new_refs = extract_blog_media_names_from_html(new_body or "")
    orphans = old_refs - new_refs
    if orphans:
        delete_blog_media_names(orphans)
        logger.info("Deleted %s orphan blog inline image(s)", len(orphans))


def purge_blog_post_media(post) -> None:
    """
    Delete featured image and all inline images referenced in the body.
    Call before deleting the post row or when fully clearing media.
    """
    names: Set[str] = set()
    featured = featured_image_storage_name(post.featured_image)
    if featured:
        names.add(featured)
    names.update(extract_blog_media_names_from_html(post.body or ""))
    if names:
        delete_blog_media_names(names)
        logger.info(
            "Purged %s blog media object(s) for post pk=%s slug=%s",
            len(names),
            post.pk,
            post.slug,
        )
