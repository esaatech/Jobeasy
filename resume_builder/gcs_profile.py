"""
Backward-compatible re-exports for resume profile portraits.

Prefer importing from :mod:`resume_builder.profile_photo_media` for new code — all logic
(including orphan prevention on upload and purge on resume delete) lives there.
"""

from .profile_photo_media import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_IMAGE_EXTENSIONS,
    delete_stored_profile_photo,
    gcs_object_path,
    has_stored_profile_photo,
    ingest_profile_photo,
    profile_photo_storage_backend,
    purge_profile_photo_for_resume,
    resolve_profile_photo_display_url,
    sanitize_personal_info_for_db,
    validate_profile_upload,
)

__all__ = [
    "ALLOWED_CONTENT_TYPES",
    "ALLOWED_IMAGE_EXTENSIONS",
    "delete_stored_profile_photo",
    "gcs_object_path",
    "has_stored_profile_photo",
    "ingest_profile_photo",
    "profile_photo_storage_backend",
    "purge_profile_photo_for_resume",
    "resolve_profile_photo_display_url",
    "sanitize_personal_info_for_db",
    "validate_profile_upload",
]
