"""
Diagnose profile-photo GCS configuration (settings, package, ADC, bucket access).

Usage:
    poetry run python manage.py check_profile_photo_gcs
"""

import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Print profile photo GCS settings, verify google-cloud-storage + ADC, "
        "and optionally probe bucket access."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-bucket",
            action="store_true",
            help="Stop after Storage client creation (skip bucket GET).",
        )

    def handle(self, *args, **options):
        skip_bucket = options["skip_bucket"]

        self.stdout.write("=== Interpreter ===")
        self.stdout.write(f"sys.executable: {sys.executable}")
        vers = getattr(sys, "version_info", None)
        if vers:
            self.stdout.write(f"Python version: {vers.major}.{vers.minor}.{vers.micro}")

        self.stdout.write("\n=== Django settings ===")
        self.stdout.write(f"ENABLE_GCS_PROFILE_UPLOAD: {getattr(settings, 'ENABLE_GCS_PROFILE_UPLOAD', None)}")
        self.stdout.write(f"GS_BUCKET_NAME: {repr(getattr(settings, 'GS_BUCKET_NAME', '') or '')}")
        self.stdout.write(f"GCP_PROJECT_ID: {repr(getattr(settings, 'GCP_PROJECT_ID', '') or '')}")
        creds_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if creds_env:
            exists = os.path.isfile(creds_env)
            self.stdout.write(
                f"GOOGLE_APPLICATION_CREDENTIALS: {creds_env!r} (file exists: {exists})"
            )
        else:
            self.stdout.write(
                "GOOGLE_APPLICATION_CREDENTIALS: (unset — using ADC elsewhere, "
                "e.g. gcloud auth application-default login or Cloud Run SA)"
            )

        use_gcs = bool(
            getattr(settings, "ENABLE_GCS_PROFILE_UPLOAD", False)
            and getattr(settings, "GS_BUCKET_NAME", "").strip()
        )
        if not use_gcs:
            self.stdout.write(
                self.style.WARNING(
                    "Configured use_gcs would be False in ingest_profile_photo "
                    "(enable flag + non-empty GS_BUCKET_NAME required)."
                )
            )

        self.stdout.write("\n=== Package: google-cloud-storage ===")
        try:
            from google.cloud import storage as gcs_storage  # noqa: F401

            self.stdout.write(self.style.SUCCESS("Import OK"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            exe = sys.executable
            self.stdout.write(
                "\nThis almost always means this Python environment does NOT have "
                "`google-cloud-storage` installed (or has a broken `google.*` layout). "
                "Your `.env` is unrelated.\n\n"
                f"Install into THIS interpreter:\n"
                f"  {exe} -m pip install google-cloud-storage\n\n"
                "Or always use Poetry's env for Django/uvicorn:\n"
                "  poetry install\n"
                "  poetry run python manage.py check_profile_photo_gcs\n"
                "  poetry run uvicorn jobeas.asgi:application --host 0.0.0.0 --port 8009 --reload\n"
            )
            return

        self.stdout.write("\n=== Storage client (ADC) ===")
        project = getattr(settings, "GCP_PROJECT_ID", "").strip() or None
        try:
            client = gcs_storage.Client(project=project)
            self.stdout.write(self.style.SUCCESS(f"Client OK (project={project!r})"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Client failed: {e}"))
            return

        if skip_bucket:
            self.stdout.write(self.style.WARNING("--skip-bucket: not probing bucket."))
            return

        bucket_name = getattr(settings, "GS_BUCKET_NAME", "").strip()
        if not bucket_name:
            self.stdout.write(self.style.WARNING("GS_BUCKET_NAME empty — skipping bucket probe."))
            return

        self.stdout.write(f"\n=== Bucket probe: {bucket_name!r} ===")
        bucket = client.bucket(bucket_name)
        reload_ok = False

        try:
            bucket.reload()
            loc = getattr(bucket, "location", "?")
            self.stdout.write(
                self.style.SUCCESS(f"bucket.reload() OK (location hint: {loc})")
            )
            reload_ok = True
        except Exception as e:
            text = str(e)
            self.stdout.write(self.style.ERROR(f"bucket.reload() failed: {text}"))
            if "storage.buckets.get" in text or (
                "403" in text and "bucket" in text.lower()
            ):
                self.stdout.write(
                    self.style.WARNING(
                        "\nBucket **metadata** needs `storage.buckets.get` (e.g. Legacy Bucket Reader). "
                        "Photo **upload** only needs **`storage.objects.create`** on the bucket. "
                        "Running a tiny object upload+delete probe (same API as real uploads)...\n"
                    )
                )
            else:
                if not self._object_upload_probe(bucket):
                    return
                self._emit_probe_success_footer(object_only_probe=True)
                return

        if not reload_ok:
            if not self._object_upload_probe(bucket):
                self.stdout.write(
                    self.style.ERROR(
                        "\nGrant this service account on bucket "
                        f"{bucket_name!r} at least **Storage Object Creator** "
                        "(or Object Admin) so uploads can succeed."
                    )
                )
                return
            self._emit_probe_success_footer(object_only_probe=True)
            return

        self._emit_probe_success_footer()

    def _object_upload_probe(self, bucket):
        """Return True if we can upload and delete a tiny blob (same path as profile photos)."""
        import uuid

        probe_name = f"_jobeas_sa_probe/{uuid.uuid4().hex}.txt"
        blob = bucket.blob(probe_name)
        self.stdout.write(f"Object probe: {probe_name!r} ...")
        try:
            blob.upload_from_string(b"jobeas-connectivity-check", content_type="text/plain")
            blob.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    "Object upload + delete OK — IAM allows what `ingest_profile_photo` uses."
                )
            )
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Object probe failed: {e}"))
            return False

    def _emit_probe_success_footer(self, object_only_probe=False):
        note = ""
        if object_only_probe:
            note = (
                " Bucket metadata is still denied (optional: add `storage.buckets.get` for tooling).\n"
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"\nGCS checks passed for profile-photo uploads.{note}\n"
                "If the wizard still saves locally, confirm Creative Studio and "
                "POST /resume/upload-profile-photo/ in the browser Network tab."
            )
        )
