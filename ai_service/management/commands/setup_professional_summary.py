"""Seed AIService + default prompt for professional summary (OpenAI JSON).

Run after setup_ai_models::

    python manage.py setup_ai_models
    python manage.py setup_professional_summary
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.models import AIModel, AIService, AIPromptConfiguration
from ai_service.professional_summary import PROFESSIONAL_SUMMARY_SERVICE_SLUG
from ai_service.professional_summary_prompts import PROFESSIONAL_SUMMARY_INSTRUCTION_V1_0


class Command(BaseCommand):
    help = (
        "Create AIService + default prompt for AI professional summary generation. "
        "Does not modify other AI service rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite an existing prompt's system_prompt text.",
        )

    def handle(self, *args, **options):
        force_update = options["force"]
        self.stdout.write(
            self.style.SUCCESS("Setting up professional summary prompts…")
        )

        svc_defaults = {
            "name": "Professional Summary",
            "description": (
                "Generates a 3–5 sentence professional summary for the resume wizard. "
                "Consumed by ai_service.professional_summary."
            ),
            "is_active": True,
        }

        with transaction.atomic():
            service, created = AIService.objects.get_or_create(
                slug=PROFESSIONAL_SUMMARY_SERVICE_SLUG,
                defaults=svc_defaults,
            )
            if created:
                self.stdout.write(f"  ✓ Created AI service: {service.name}")
            else:
                self.stdout.write(f"  - AI service already exists: {service.name}")

            slug = "v1-0"
            prompt_name = "Professional summary v1.0"
            default_model = AIModel.objects.filter(
                provider=AIModel.Provider.OPENAI,
                model_id="gpt-4o",
                is_active=True,
            ).first()
            if default_model is None:
                self.stdout.write(
                    self.style.WARNING(
                        "  ! No gpt-4o in AIModel catalog — run setup_ai_models first."
                    )
                )

            existing_prompt = AIPromptConfiguration.objects.filter(
                service=service, slug=slug
            ).first()

            prompt_defaults = {
                "name": prompt_name,
                "system_prompt": PROFESSIONAL_SUMMARY_INSTRUCTION_V1_0,
                "is_default": True,
                "is_active": True,
                "ai_model": default_model,
                "temperature": Decimal("0.30"),
            }

            if existing_prompt and not force_update:
                self.stdout.write(
                    f"  - Prompt already exists: {service.name} — {prompt_name}"
                )
                patched = []
                if default_model and existing_prompt.ai_model_id is None:
                    existing_prompt.ai_model = default_model
                    patched.append("ai_model")
                if existing_prompt.temperature is None:
                    existing_prompt.temperature = Decimal("0.30")
                    patched.append("temperature")
                if patched:
                    existing_prompt.save(update_fields=patched)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    Linked defaults on existing prompt: {', '.join(patched)}"
                        )
                    )
                self.stdout.write(
                    self.style.WARNING(
                        "    Use --force to replace the stored system_prompt text."
                    )
                )
            elif existing_prompt and force_update:
                for key, val in prompt_defaults.items():
                    setattr(existing_prompt, key, val)
                existing_prompt.save()
                self.stdout.write(f"  ✓ Updated prompt: {service.name} — {prompt_name}")
            else:
                AIPromptConfiguration.objects.create(
                    service=service,
                    slug=slug,
                    **prompt_defaults,
                )
                self.stdout.write(f"  ✓ Created prompt: {service.name} — {prompt_name}")

        self.stdout.write(
            self.style.SUCCESS(
                "\nDone. Admin playground: Professional summary playground; "
                "prompts under AI Prompt Configurations."
            )
        )
