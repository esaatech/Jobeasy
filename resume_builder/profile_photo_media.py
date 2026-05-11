"""
Centralized resume profile portrait storage.

Storage policy
--------------
- Pointers live on ``Resume.personal_info`` JSON: ``profile_image_gcs_bucket`` +
  ``profile_image_blob``, or ``profile_image_local_path`` under Django default storage.
  Browser display URLs use an authenticated same-origin proxy or inline data for PDFs — not V4
  signed URLs (Cloud Run ADC has no private signing key).

Replacement uploads
-------------------
``ingest_profile_photo()`` always calls ``delete_stored_profile_photo()`` first so the
previous GCS blob or local file is removed before writing the new asset (no orphaned
files from user photo updates).

Resume deletion
---------------
``Resume.delete()`` invokes ``delete_stored_profile_photo()`` so portrait files are
removed when the resume row is deleted (single-instance delete, used by dashboard and
wizard flows).

Templates without a photo slot continue to omit display; stored bytes may remain until
replace/delete per product preference.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})
ALLOWED_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)


def _safe_env_segment() -> str:
    raw = getattr(settings, "DJANGO_ENV", "development") or "development"
    return "".join(c for c in str(raw) if c.isalnum() or c in "-_").lower()[:48] or "app"


def gcs_object_path(user_id: int, resume_id: int, ext: str) -> str:
    return f"{_safe_env_segment()}/profile-photos/user-{user_id}/resume-{resume_id}{ext}"


def validate_profile_upload(upload: UploadedFile) -> str:
    if not upload or not getattr(upload, "name", ""):
        raise ValueError("No image file was uploaded.")
    if getattr(upload, "size", None) == 0:
        raise ValueError("The uploaded image was empty.")
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Please upload a JPG, PNG, WebP, or GIF image.")
    ctype = (getattr(upload, "content_type", "") or "").split(";")[0].strip().lower()
    if ctype and ctype not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported image type.")
    max_bytes = int(getattr(settings, "PROFILE_PHOTO_MAX_BYTES", 2_621_440))
    if getattr(upload, "size", None) is not None and upload.size > max_bytes:
        raise ValueError(f"Image is too large (max {max_bytes // (1024 * 1024)} MB).")
    return ext


def delete_stored_profile_photo(personal_info: Optional[Dict[str, Any]]) -> None:
    """
    Remove portrait bytes from GCS and/or default storage using JSON pointers.
    Safe to call when ``personal_info`` is None or missing keys.
    Runs GCS delete whenever bucket + blob are set (even if ``ENABLE_GCS_PROFILE_UPLOAD``
    is off) so legacy blobs are not left behind after config changes.
    """
    if not personal_info:
        return
    bucket_name = personal_info.get("profile_image_gcs_bucket")
    blob_name = personal_info.get("profile_image_blob")
    if bucket_name and blob_name:
        try:
            from google.cloud import storage

            client = storage.Client(project=(getattr(settings, "GCP_PROJECT_ID", "") or None))
            client.bucket(bucket_name).blob(blob_name).delete()
        except Exception as exc:
            logger.warning("Failed to delete GCS profile photo: %s", exc)
    local_path = personal_info.get("profile_image_local_path")
    if local_path:
        try:
            from django.core.files.storage import default_storage

            default_storage.delete(local_path)
        except Exception as exc:
            logger.warning("Failed to delete local profile photo: %s", exc)


def _persist_profile_photo_locally(
    personal_info: Dict[str, Any], resume: Any, upload: UploadedFile, ext: str
) -> None:
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    upload.file.seek(0)
    rel_path = os.path.join(
        "profile_photos", str(resume.user_id), f"resume_{resume.id}{ext}"
    ).replace("\\", "/")
    saved = default_storage.save(rel_path, ContentFile(upload.read()))
    personal_info["profile_image_local_path"] = saved.replace("\\", "/")
    personal_info.pop("profile_image_gcs_bucket", None)
    personal_info.pop("profile_image_blob", None)


def ingest_profile_photo(resume: Any, upload: UploadedFile) -> Dict[str, Any]:
    """
    Persist a new portrait: delete prior storage keys first (no orphans),
    then write locally or GCS and update ``resume.personal_info``.
    """
    ext = validate_profile_upload(upload)
    delete_stored_profile_photo(resume.personal_info or {})

    personal_info = dict(resume.personal_info or {})
    for k in ("profile_photo_display_url",):
        personal_info.pop(k, None)

    use_gcs = bool(
        getattr(settings, "ENABLE_GCS_PROFILE_UPLOAD", False)
        and getattr(settings, "GS_BUCKET_NAME", "").strip()
    )
    upload.file.seek(0)

    gcs_enabled_flag = getattr(settings, "ENABLE_GCS_PROFILE_UPLOAD", False)
    bucket_setting = getattr(settings, "GS_BUCKET_NAME", "").strip()

    if use_gcs:
        try:
            from google.cloud import storage as gcs_storage
        except ImportError:
            logger.warning(
                "ENABLE_GCS_PROFILE_UPLOAD is set but google-cloud-storage is not importable; "
                "install it in this environment or set ENABLE_GCS_PROFILE_UPLOAD=false — "
                "using local MEDIA storage for this upload."
            )
            _persist_profile_photo_locally(personal_info, resume, upload, ext)
            logger.info(
                "Profile photo ingest resume_id=%s stored=local reason=missing_google_cloud_storage_package",
                resume.id,
            )
        else:
            client = gcs_storage.Client(project=(getattr(settings, "GCP_PROJECT_ID", "") or None))
            bucket_name = settings.GS_BUCKET_NAME.strip()
            blob_name = gcs_object_path(resume.user_id, resume.id, ext)
            blob = client.bucket(bucket_name).blob(blob_name)
            blob.upload_from_file(
                upload.file,
                rewind=True,
                content_type=getattr(upload, "content_type", None) or "application/octet-stream",
            )

            personal_info["profile_image_gcs_bucket"] = bucket_name
            personal_info["profile_image_blob"] = blob_name
            personal_info.pop("profile_image_local_path", None)
            logger.info(
                "Profile photo ingest resume_id=%s stored=gcs bucket=%s blob=%s",
                resume.id,
                bucket_name,
                blob_name,
            )
    else:
        reason_parts = []
        if not gcs_enabled_flag:
            reason_parts.append("ENABLE_GCS_PROFILE_UPLOAD_off_or_false")
        if not bucket_setting:
            reason_parts.append("GS_BUCKET_NAME_empty")
        reason = "_".join(reason_parts) if reason_parts else "gcs_conditions_not_met"
        _persist_profile_photo_locally(personal_info, resume, upload, ext)
        logger.info(
            "Profile photo ingest resume_id=%s stored=local reason=%s",
            resume.id,
            reason,
        )

    resume.personal_info = personal_info
    resume.save(update_fields=["personal_info", "updated_at"])
    return personal_info


def gcs_profile_photo_data_uri(bucket_name: str, blob_name: str) -> str:
    """
    Load portrait bytes from GCS using ADC (works on Cloud Run without a signing key).
    Returns a data: URI for HTML/PDF contexts where cookie-auth proxy URLs cannot load.
    """
    try:
        from google.cloud import storage

        client = storage.Client(project=(getattr(settings, "GCP_PROJECT_ID", "") or None))
        blob = client.bucket(bucket_name).blob(blob_name)
        data = blob.download_as_bytes()
        if not data:
            return ""
        ctype = (
            (blob.content_type or "").split(";")[0].strip()
            or mimetypes.guess_type(blob_name)[0]
            or "image/jpeg"
        )
        b64 = base64.standard_b64encode(data).decode("ascii")
        return f"data:{ctype};base64,{b64}"
    except Exception as exc:
        logger.warning("Could not load GCS profile photo for inline data URI: %s", exc)
        return ""


def local_storage_profile_photo_data_uri(local_path: str) -> str:
    """Embed MEDIA-backed portrait bytes as data URI (PDF/export contexts)."""
    try:
        from django.core.files.storage import default_storage

        rel = str(local_path).lstrip("/").replace("\\", "/")
        if not default_storage.exists(rel):
            return ""
        with default_storage.open(rel, "rb") as fh:
            data = fh.read()
        if not data:
            return ""
        ctype = mimetypes.guess_type(rel)[0] or "image/jpeg"
        b64 = base64.standard_b64encode(data).decode("ascii")
        return f"data:{ctype};base64,{b64}"
    except Exception as exc:
        logger.warning("Could not load local profile photo for inline data URI: %s", exc)
        return ""


def resolve_profile_photo_display_url(
    personal_info: Optional[Dict[str, Any]],
    *,
    request=None,
    resume_id: Optional[int] = None,
    force_inline_from_storage: bool = False,
) -> str:
    """
    URL or data URI suitable for <img src>.

    Cloud Run credentials cannot sign V4 URLs without a private key; use the authenticated
    proxy when resume_id + request are available, or embed bytes when rendering PDF/offline HTML.
    """
    if not personal_info:
        return ""
    bucket_name = personal_info.get("profile_image_gcs_bucket")
    blob_name = personal_info.get("profile_image_blob")

    if (
        bucket_name
        and blob_name
        and getattr(settings, "ENABLE_GCS_PROFILE_UPLOAD", False)
    ):
        if force_inline_from_storage:
            return gcs_profile_photo_data_uri(bucket_name, blob_name)
        if request is not None and resume_id is not None:
            path = reverse(
                "resume_builder:profile_photo_proxy",
                kwargs={"resume_id": resume_id},
            )
            return request.build_absolute_uri(path)
        return gcs_profile_photo_data_uri(bucket_name, blob_name)

    local_path = personal_info.get("profile_image_local_path")
    if not local_path:
        return ""

    if force_inline_from_storage:
        return local_storage_profile_photo_data_uri(local_path)

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    if not media_url.startswith("/"):
        media_url = "/" + media_url
    path = f"{media_url.rstrip('/')}/{str(local_path).lstrip('/')}"
    if request is not None:
        return request.build_absolute_uri(path)

    base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    return base + path


def profile_photo_storage_backend(personal_info: Optional[Dict[str, Any]]) -> str:
    """Return ``gcs``, ``local``, or ``none`` based on persisted pointer keys."""
    if not personal_info:
        return "none"
    if personal_info.get("profile_image_gcs_bucket") and personal_info.get(
        "profile_image_blob"
    ):
        return "gcs"
    if personal_info.get("profile_image_local_path"):
        return "local"
    return "none"


def purge_profile_photo_for_resume(resume: Any) -> None:
    """
    Explicit hook for callers that operate on ``Resume`` instances.
    ``Resume.delete`` uses ``delete_stored_profile_photo(resume.personal_info)``.
    """
    delete_stored_profile_photo(getattr(resume, "personal_info", None) or {})


PROFILE_PHOTO_POINTER_KEYS = (
    "profile_image_gcs_bucket",
    "profile_image_blob",
    "profile_image_local_path",
    "profile_photo_display_url",
)


def clear_resume_profile_photo(resume: Any) -> None:
    """Delete stored bytes and strip portrait pointers from ``resume.personal_info``."""
    personal_info = dict(getattr(resume, "personal_info", None) or {})
    delete_stored_profile_photo(personal_info)
    for key in PROFILE_PHOTO_POINTER_KEYS:
        personal_info.pop(key, None)
    resume.personal_info = personal_info
    resume.save(update_fields=["personal_info", "updated_at"])
