"""Seed Gemini model catalog rows for admin and prompt configuration."""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.models import AIModel


GEMINI_MODELS = [
    {
        "model_id": "gemini-2.5-flash-lite",
        "display_name": "Gemini 2.5 Flash-Lite",
        "description": "Fastest, most cost-efficient 2.5 model.",
        "sort_order": 10,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash",
        "description": "Balanced speed and quality (recommended default).",
        "sort_order": 20,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gemini-2.5-pro",
        "display_name": "Gemini 2.5 Pro",
        "description": "Highest intelligence in the 2.5 family.",
        "sort_order": 30,
        "default_temperature": Decimal("0.35"),
    },
]


class Command(BaseCommand):
    help = "Create or update AIModel rows for Gemini 2.5 Pro / Flash / Flash-Lite."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up AI model catalog…"))
        with transaction.atomic():
            for spec in GEMINI_MODELS:
                obj, created = AIModel.objects.update_or_create(
                    provider=AIModel.Provider.GEMINI,
                    model_id=spec["model_id"],
                    defaults={
                        "display_name": spec["display_name"],
                        "description": spec["description"],
                        "sort_order": spec["sort_order"],
                        "default_temperature": spec["default_temperature"],
                        "is_active": True,
                    },
                )
                verb = "Created" if created else "Updated"
                self.stdout.write(f"  ✓ {verb}: {obj}")
        self.stdout.write(self.style.SUCCESS("\nDone."))
