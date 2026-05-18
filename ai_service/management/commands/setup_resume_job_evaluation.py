"""Seed DB rows for Gemini resume–job evaluation only.

OpenAI-backed services (`setup_ai_prompts`) are untouched. Run:

    python manage.py setup_resume_job_evaluation
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.eval_prompts import EVALUATOR_INSTRUCTION_V1_0
from ai_service.models import AIService, AIPromptConfiguration
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

            existing_prompt = AIPromptConfiguration.objects.filter(
                service=service, slug=slug
            ).first()

            if existing_prompt and not force_update:
                self.stdout.write(f"  - Prompt already exists: {service.name} — {prompt_name}")
                self.stdout.write(
                    self.style.WARNING("    Use --force to replace the stored system_prompt text.")
                )
            elif existing_prompt and force_update:
                existing_prompt.name = prompt_name
                existing_prompt.system_prompt = EVALUATOR_INSTRUCTION_V1_0
                existing_prompt.is_default = True
                existing_prompt.is_active = True
                existing_prompt.save()
                self.stdout.write(f"  ✓ Updated prompt: {service.name} — {prompt_name}")
            else:
                prompt = AIPromptConfiguration.objects.create(
                    service=service,
                    name=prompt_name,
                    slug=slug,
                    system_prompt=EVALUATOR_INSTRUCTION_V1_0,
                    is_default=True,
                    is_active=True,
                )
                self.stdout.write(f"  ✓ Created prompt: {service.name} — {prompt.name}")

        self.stdout.write(
            self.style.SUCCESS("\nDone. Admin playgrounds: Resume-job evaluations; prompts under AI Prompt Configurations.")
        )
