"""
Remove stale portrait fields from Resume.personal_info (base64 display URLs, redundant local paths).

Run once after deploying the single-source-of-truth portrait fix:

    poetry run python manage.py cleanup_profile_photo_json
    poetry run python manage.py cleanup_profile_photo_json --dry-run
"""

from django.core.management.base import BaseCommand

from resume_builder.models import Resume
from resume_builder.profile_photo_media import sanitize_personal_info_for_db


class Command(BaseCommand):
    help = "Strip profile_photo_display_url and redundant portrait keys from all resumes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print how many rows would change without writing.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        changed = 0
        scanned = 0

        for resume in Resume.objects.only("id", "personal_info").iterator(chunk_size=200):
            scanned += 1
            raw = resume.personal_info or {}
            cleaned = sanitize_personal_info_for_db(raw)
            if cleaned == raw:
                continue
            changed += 1
            if dry_run:
                self.stdout.write(f"Would update resume id={resume.id}")
                continue
            resume.personal_info = cleaned
            resume.save(update_fields=["personal_info"])

        suffix = " (dry run)" if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"Scanned {scanned} resume(s); cleaned {changed} personal_info blob(s){suffix}."
            )
        )
