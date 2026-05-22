"""Seed AIService + default prompt for why-should-I-apply (Gemini plain text).

Run after setup_ai_models::

    python manage.py setup_ai_models
    python manage.py setup_why_should_i_apply
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.models import AIModel, AIService, AIPromptConfiguration
from ai_service.why_should_i_apply import WHY_SHOULD_I_APPLY_SERVICE_SLUG
from ai_service.why_should_i_apply_prompts import WHY_SHOULD_I_APPLY_INSTRUCTION_V1_0


class Command(BaseCommand):
    help = (
        "Create AIService + default prompt for why-should-I-apply application answers. "
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
            self.style.SUCCESS("Setting up why-should-I-apply prompts…")
        )

        svc_defaults = {
            "name": "Why Should I Apply",
            "description": (
                "Generates a concise application-field answer to "
                '"Why should we hire you?" (not a cover letter). '
                "Consumed by ai_service.why_should_i_apply."
            ),
            "is_active": True,
        }

        with transaction.atomic():
            service, created = AIService.objects.get_or_create(
                slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG,
                defaults=svc_defaults,
            )
            if created:
                self.stdout.write(f"  ✓ Created AI service: {service.name}")
            else:
                self.stdout.write(f"  - AI service already exists: {service.name}")

            slug = "v1-0"
            prompt_name = "Why should I apply v1.0"
            default_model = AIModel.objects.filter(
                provider=AIModel.Provider.GEMINI,
                model_id="gemini-2.5-flash",
                is_active=True,
            ).first()
            if default_model is None:
                self.stdout.write(
                    self.style.WARNING(
                        "  ! No gemini-2.5-flash in AIModel catalog — run setup_ai_models first."
                    )
                )

            existing_prompt = AIPromptConfiguration.objects.filter(
                service=service, slug=slug
            ).first()

            prompt_defaults = {
                "name": prompt_name,
                "system_prompt": WHY_SHOULD_I_APPLY_INSTRUCTION_V1_0,
                "is_default": True,
                "is_active": True,
                "ai_model": default_model,
                "temperature": Decimal("0.55"),
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
                    existing_prompt.temperature = Decimal("0.55")
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
                "\nDone. Admin playground: Why should I apply playground; "
                "prompts under AI Prompt Configurations."
            )
        )
