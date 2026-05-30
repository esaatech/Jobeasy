"""
Blog media storage: local MEDIA in development, Google Cloud Storage in production.

Paths (GCS):
  {env}/blog/featured/<filename>
  {env}/blog/ckeditor/<uuid>.<ext>

Public URLs use GCS_BLOG_MEDIA_BASE_URL when set, else storage.googleapis.com.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from typing import Optional
from urllib.parse import quote, unquote, urlparse

from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def safe_env_segment() -> str:
    raw = getattr(settings, "DJANGO_ENV", "development") or "development"
    return "".join(c for c in str(raw) if c.isalnum() or c in "-_").lower()[:48] or "app"


def gcs_blog_media_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_GCS_BLOG_MEDIA", False)) and bool(
        blog_media_bucket()
    )


def blog_media_bucket() -> str:
    return getattr(settings, "GS_BUCKET_NAME", "").strip()


def blog_media_public_base_url() -> str:
    custom = getattr(settings, "GCS_BLOG_MEDIA_BASE_URL", "").strip()
    if custom:
        return custom.rstrip("/")
    bucket = blog_media_bucket()
    if bucket:
        return f"https://storage.googleapis.com/{bucket}"
    return ""


def normalize_storage_name(name: str) -> str:
    """Storage-relative path using forward slashes."""
    return str(name or "").replace("\\", "/").lstrip("/")


def gcs_object_name_for_upload(name: str) -> str:
    """
    Build the object key for a new upload.

    CKEditor often passes a bare filename; route those under blog/ckeditor/.
    """
    name = normalize_storage_name(name)
    if not gcs_blog_media_enabled():
        return name

    env = safe_env_segment()
    if name.startswith(f"{env}/"):
        return name

    basename = os.path.basename(name)
    if not name.startswith("blog/"):
        ext = os.path.splitext(basename)[1].lower() or ".bin"
        name = f"blog/ckeditor/{uuid.uuid4().hex}{ext}"
    elif name.startswith("blog/") and "/" not in name[len("blog/") :]:
        # e.g. blog/somefile.jpg from misconfigured upload
        ext = os.path.splitext(basename)[1].lower() or ".bin"
        name = f"blog/ckeditor/{uuid.uuid4().hex}{ext}"

    return f"{env}/{name}"


def storage_name_from_public_url(url: str) -> Optional[str]:
    """Map a public blog media URL back to the storage object key, if recognized."""
    if not url:
        return None

    parsed = urlparse(url.strip())
    path = unquote(parsed.path or "").lstrip("/")

    base = blog_media_public_base_url()
    if base and url.startswith(base):
        name = normalize_storage_name(path)
        bucket = blog_media_bucket()
        if bucket and name.startswith(f"{bucket}/"):
            return name[len(bucket) + 1 :]
        return name

    bucket = blog_media_bucket()
    if bucket and parsed.netloc in {
        "storage.googleapis.com",
        "storage.cloud.google.com",
    }:
        # Path is bucket/object or object only depending on URL style
        if path.startswith(f"{bucket}/"):
            return normalize_storage_name(path[len(bucket) + 1 :])
        return normalize_storage_name(path)

    media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
    if not media_url.startswith("/"):
        media_url = "/" + media_url
    media_prefix = media_url.rstrip("/") + "/"
    if path.startswith(media_prefix.lstrip("/")):
        return normalize_storage_name(path[len(media_prefix.lstrip("/")) :])

    if url.startswith(media_prefix):
        return normalize_storage_name(url[len(media_prefix) :])

    return None


def public_url_for_storage_name(name: str) -> str:
    name = normalize_storage_name(name)
    if not name:
        return ""
    if gcs_blog_media_enabled():
        base = blog_media_public_base_url()
        if base:
            return f"{base}/{quote(name, safe='/')}"
    media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
    if not media_url.endswith("/"):
        media_url += "/"
    if not media_url.startswith("/"):
        site = getattr(settings, "SITE_URL", "").rstrip("/")
        return f"{site}{media_url}{name}"
    return f"{media_url}{name}"


def _gcs_client():
    from google.cloud import storage

    project = getattr(settings, "GCP_PROJECT_ID", "") or None
    return storage.Client(project=project)


@deconstructible
class BlogGoogleCloudStorage(Storage):
    """Django storage backend for blog images on Google Cloud Storage."""

    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = (bucket_name or blog_media_bucket()).strip()

    def _bucket(self):
        if not self.bucket_name:
            raise ValueError("GS_BUCKET_NAME is not configured.")
        return _gcs_client().bucket(self.bucket_name)

    def _blob(self, name: str):
        return self._bucket().blob(normalize_storage_name(name))

    def save(self, name, content, max_length=None):
        name = gcs_object_name_for_upload(name)
        blob = self._blob(name)
        if hasattr(content, "chunks"):
            data = b"".join(content.chunks())
        else:
            data = content.read()
        content_type = getattr(content, "content_type", None) or mimetypes.guess_type(name)[
            0
        ]
        blob.upload_from_string(
            data,
            content_type=content_type or "application/octet-stream",
        )
        if getattr(settings, "GCS_BLOG_MEDIA_MAKE_PUBLIC", True):
            try:
                blob.make_public()
            except Exception as exc:
                logger.warning(
                    "Could not make blog object public %s (check bucket IAM): %s",
                    name,
                    exc,
                )
        return name

    def delete(self, name):
        name = normalize_storage_name(name)
        if not name:
            return
        try:
            self._blob(name).delete()
        except Exception as exc:
            logger.warning("Failed to delete GCS blog object %s: %s", name, exc)

    def exists(self, name):
        return self._blob(name).exists()

    def url(self, name):
        return public_url_for_storage_name(name)

    def size(self, name):
        blob = self._blob(name)
        blob.reload()
        return blob.size

    def open(self, name, mode="rb"):
        data = self._blob(name).download_as_bytes()
        return File(ContentFile(data), name=name)


def get_blog_file_storage():
    """Return the active storage backend for blog uploads."""
    if gcs_blog_media_enabled() and blog_media_bucket():
        return BlogGoogleCloudStorage()
    return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)


def delete_blog_storage_name(name: str) -> None:
    """Delete one object from the active blog storage backend."""
    name = normalize_storage_name(name)
    if not name:
        return
    try:
        get_blog_file_storage().delete(name)
    except Exception as exc:
        logger.warning("Failed to delete blog media %s: %s", name, exc)
