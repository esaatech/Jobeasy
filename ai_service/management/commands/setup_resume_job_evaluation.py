"""Seed DB rows for Gemini resume–job evaluation only.

OpenAI-backed services (`setup_ai_prompts`) are untouched. Run:

    python manage.py setup_ai_models
    python manage.py setup_resume_job_evaluation
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.eval_prompts import EVALUATOR_INSTRUCTION_V1_0
from ai_service.models import AIModel, AIService, AIPromptConfiguration
from ai_service.resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG


class Command(BaseCommand):
    help = (
        "Create AIService + default prompt for resume–job evaluation (Gemini). "
        "Does not modify cover letter, resume optimization, or interview coach rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite an existing evaluator prompt's system_instruction text.",
        )

    def handle(self, *args, **options):
        force_update = options["force"]
        self.stdout.write(
            self.style.SUCCESS("Setting up Gemini resume–job evaluation prompts…")
        )

        svc_defaults = {
            "name": "Resume-to-Job Evaluation",
            "description": (
                "Pre-application fit gate (resume vs job description). Consumed only by Gemini "
                "code paths (`ai_service.resume_job_evaluation`)."
            ),
            "is_active": True,
        }

        with transaction.atomic():
            service, created = AIService.objects.get_or_create(
                slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
                defaults=svc_defaults,
            )
            if created:
                self.stdout.write(f"  ✓ Created AI service: {service.name}")
            else:
                self.stdout.write(f"  - AI service already exists: {service.name}")

            slug = "v1-0"
            prompt_name = "Evaluator instruction v1.0"
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
                "system_prompt": EVALUATOR_INSTRUCTION_V1_0,
                "is_default": True,
                "is_active": True,
                "ai_model": default_model,
                "temperature": Decimal("0.35"),
            }

            if existing_prompt and not force_update:
                self.stdout.write(f"  - Prompt already exists: {service.name} — {prompt_name}")
                patched = []
                if default_model and existing_prompt.ai_model_id is None:
                    existing_prompt.ai_model = default_model
                    patched.append("ai_model")
                if existing_prompt.temperature is None:
                    existing_prompt.temperature = Decimal("0.35")
                    patched.append("temperature")
                if patched:
                    existing_prompt.save(update_fields=patched)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    Linked defaults on existing prompt: {', '.join(patched)}"
                        )
                    )
                self.stdout.write(
                    self.style.WARNING("    Use --force to replace the stored system_prompt text.")
                )
            elif existing_prompt and force_update:
                for key, val in prompt_defaults.items():
                    setattr(existing_prompt, key, val)
                existing_prompt.save()
                self.stdout.write(f"  ✓ Updated prompt: {service.name} — {prompt_name}")
            else:
                prompt = AIPromptConfiguration.objects.create(
                    service=service,
                    slug=slug,
                    **prompt_defaults,
                )
                self.stdout.write(f"  ✓ Created prompt: {service.name} — {prompt.name}")

        self.stdout.write(
            self.style.SUCCESS("\nDone. Admin playgrounds: Resume-job evaluations; prompts under AI Prompt Configurations.")
        )
