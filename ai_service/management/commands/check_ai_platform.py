"""Verify AI platform migrations, admin registration, and catalog seed."""

from django.contrib import admin
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from ai_service.models import AIModel, ResumeJobEvaluation
from ai_service.platform_version import AI_PLATFORM_BUILD


class Command(BaseCommand):
    help = (
        "Confirm ai_service migrations, admin models, and AIModel catalog. "
        "Run after deploy (entrypoint) or manually in production."
    )

    def handle(self, *args, **options):
        self.stdout.write(f"AI platform build: {AI_PLATFORM_BUILD}")

        self._check_migrations()
        self._check_admin_registration()
        self._check_catalog()

        self.stdout.write(self.style.SUCCESS("check_ai_platform: OK"))

    def _check_migrations(self) -> None:
        required = {
            "0003_aimodel_and_generation_fields",
            "0004_resumejobevaluation_label_fields",
        }
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name FROM django_migrations
                WHERE app = 'ai_service'
                """
            )
            applied = {row[0] for row in cursor.fetchall()}

        missing = required - applied
        if missing:
            raise CommandError(
                f"Missing ai_service migrations: {', '.join(sorted(missing))}. "
                "Run: python manage.py migrate ai_service"
            )
        self.stdout.write(f"  migrations: {len(applied)} applied (required OK)")

    def _check_admin_registration(self) -> None:
        expected = {AIModel, ResumeJobEvaluation}
        missing = [m.__name__ for m in expected if m not in admin.site._registry]
        if missing:
            raise CommandError(
                f"Admin not registered for: {', '.join(missing)}. "
                "Ensure ai_service.admin loads (AiServiceConfig.ready imports admin)."
            )
        registered = sorted(
            m._meta.object_name
            for m in admin.site._registry
            if m._meta.app_label == "ai_service"
        )
        self.stdout.write(f"  admin models: {', '.join(registered)}")

    def _check_catalog(self) -> None:
        count = AIModel.objects.filter(is_active=True).count()
        if count < 1:
            raise CommandError(
                "No active AIModel rows. Run: python manage.py setup_ai_models"
            )
        self.stdout.write(f"  active AIModel rows: {count}")
