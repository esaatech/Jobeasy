"""Seed dashboard job-fit gate settings and production evaluator prompt."""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.eval_prompts import EVALUATOR_INSTRUCTION_V1_0
from ai_service.job_fit_settings import ensure_job_fit_gate_settings
from ai_service.models import (
    AIModel,
    AIService,
    AIPromptConfiguration,
    DASHBOARD_DEFAULT_EVAL_PROMPT_SLUG,
)
from ai_service.resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG


class Command(BaseCommand):
    help = (
        "Create default-job-evaluation prompt and JobFitGateSettings singleton. "
        "Idempotent: skips existing rows unless --force on prompt text."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite system_prompt on the dashboard production prompt.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        self.stdout.write(self.style.SUCCESS("Setting up job fit gate…"))

        with transaction.atomic():
            service = AIService.objects.filter(
                slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
                is_active=True,
            ).first()
            if service is None:
                self.stdout.write(
                    self.style.ERROR(
                        "  Run setup_resume_job_evaluation first (AIService missing)."
                    )
                )
                return

            flash = AIModel.objects.filter(
                provider=AIModel.Provider.GEMINI,
                model_id="gemini-2.5-flash",
                is_active=True,
            ).first()
            if flash is None:
                self.stdout.write(
                    self.style.WARNING("  No gemini-2.5-flash in catalog — run setup_ai_models.")
                )

            slug = DASHBOARD_DEFAULT_EVAL_PROMPT_SLUG
            prompt_defaults = {
                "name": "Dashboard default job evaluation",
                "system_prompt": EVALUATOR_INSTRUCTION_V1_0,
                "is_default": False,
                "is_active": True,
                "ai_model": flash,
                "temperature": Decimal("0.35"),
            }

            existing = AIPromptConfiguration.objects.filter(
                service=service,
                slug=slug,
            ).first()

            if existing and not force:
                self.stdout.write(f"  - Prompt already exists: {slug}")
                prompt = existing
                patched = []
                if flash and existing.ai_model_id is None:
                    existing.ai_model = flash
                    patched.append("ai_model")
                if existing.temperature is None:
                    existing.temperature = Decimal("0.35")
                    patched.append("temperature")
                if patched:
                    existing.save(update_fields=patched)
                    self.stdout.write(
                        self.style.SUCCESS(f"    Patched: {', '.join(patched)}")
                    )
            elif existing and force:
                for key, val in prompt_defaults.items():
                    setattr(existing, key, val)
                existing.save()
                prompt = existing
                self.stdout.write(f"  ✓ Updated prompt: {slug}")
            else:
                prompt = AIPromptConfiguration.objects.create(
                    service=service,
                    slug=slug,
                    **prompt_defaults,
                )
                self.stdout.write(f"  ✓ Created prompt: {slug}")

            settings = ensure_job_fit_gate_settings(prompt_config_id=prompt.pk)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Job fit gate settings (enabled={settings.is_enabled}, "
                    f"green≥{settings.green_min_score}, prompt={slug})"
                )
            )

        self.stdout.write(self.style.SUCCESS("\nDone."))
