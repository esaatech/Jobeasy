"""Seed resume optimization AIServices (with and without email subject).

Run after setup_ai_models::

    python manage.py setup_ai_models
    python manage.py setup_resume_optimization
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.models import AIModel, AIService, AIPromptConfiguration
from ai_service.resume_optimization import (
    RESUME_OPTIMIZATION_SERVICE_SLUG,
    RESUME_OPTIMIZATION_WITH_EMAIL_SERVICE_SLUG,
)
from ai_service.resume_optimization_prompts import (
    RESUME_OPTIMIZATION_INSTRUCTION_V1_0,
    RESUME_OPTIMIZATION_WITH_EMAIL_INSTRUCTION_V1_0,
)

DEFAULT_PROMPT_SLUG = "v1-0"
LEGACY_EMAIL_SLUGS = frozenset({"with_email_subject", "with-email-subject"})
LEGACY_DEFAULT_SLUGS = frozenset({"default", "letter-only"})


class Command(BaseCommand):
    help = (
        "Create or update resume_optimization AIServices and default v1-0 prompts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing default prompts' system_prompt text.",
        )

    def handle(self, *args, **options):
        force_update = options["force"]
        self.stdout.write(self.style.SUCCESS("Setting up resume optimization prompts…"))

        services_spec = [
            {
                "slug": RESUME_OPTIMIZATION_SERVICE_SLUG,
                "name": "Resume Optimization",
                "description": (
                    "Tailors resume summary, skills, experience bullets, and projects "
                    "to a job description. Used by dashboard generate (no email subject)."
                ),
                "system_prompt": RESUME_OPTIMIZATION_INSTRUCTION_V1_0,
                "prompt_name": "Resume optimization v1.0",
            },
            {
                "slug": RESUME_OPTIMIZATION_WITH_EMAIL_SERVICE_SLUG,
                "name": "Resume Optimization (with email subject)",
                "description": (
                    "Same as resume optimization plus an application email subject line. "
                    "Used when dashboard optimizes resume without a cover letter."
                ),
                "system_prompt": RESUME_OPTIMIZATION_WITH_EMAIL_INSTRUCTION_V1_0,
                "prompt_name": "Resume optimization (with email) v1.0",
            },
        ]

        with transaction.atomic():
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

            letter_svc = None
            email_svc = None
            for spec in services_spec:
                svc, _ = self._upsert_service(spec)
                if spec["slug"] == RESUME_OPTIMIZATION_SERVICE_SLUG:
                    letter_svc = svc
                else:
                    email_svc = svc
                self._upsert_default_prompt(
                    svc, spec, default_model=default_model, force_update=force_update
                )

            if letter_svc and email_svc:
                self._migrate_legacy_prompts(letter_svc, email_svc)

        self.stdout.write(self.style.SUCCESS("\nDone."))

    def _upsert_service(self, spec: dict) -> tuple[AIService, bool]:
        svc_defaults = {
            "name": spec["name"],
            "description": spec["description"],
            "is_active": True,
        }
        service, created = AIService.objects.get_or_create(
            slug=spec["slug"],
            defaults=svc_defaults,
        )
        if not created:
            for key, val in svc_defaults.items():
                setattr(service, key, val)
            service.save()
        label = "Created" if created else "Exists"
        self.stdout.write(f"  {label}: {service.name}")
        return service, created

    def _upsert_default_prompt(
        self,
        service: AIService,
        spec: dict,
        *,
        default_model: AIModel | None,
        force_update: bool,
    ) -> None:
        slug = DEFAULT_PROMPT_SLUG
        existing = AIPromptConfiguration.objects.filter(
            service=service, slug=slug
        ).first()
        prompt_defaults = {
            "name": spec["prompt_name"],
            "system_prompt": spec["system_prompt"],
            "is_default": True,
            "is_active": True,
            "ai_model": default_model,
            "temperature": Decimal("0.50"),
        }
        if existing and not force_update:
            self.stdout.write(f"  - Prompt exists: {spec['prompt_name']}")
            return
        if existing and force_update:
            for k, v in prompt_defaults.items():
                setattr(existing, k, v)
            existing.save()
            self.stdout.write(f"  ✓ Updated prompt: {spec['prompt_name']}")
        else:
            AIPromptConfiguration.objects.create(
                service=service, slug=slug, **prompt_defaults
            )
            self.stdout.write(f"  ✓ Created prompt: {spec['prompt_name']}")

    def _migrate_legacy_prompts(
        self,
        opt_svc: AIService,
        email_svc: AIService,
    ) -> None:
        for prompt in list(opt_svc.prompts.all()):
            slug = (prompt.slug or "").strip()
            if slug in LEGACY_EMAIL_SLUGS:
                target = AIPromptConfiguration.objects.filter(
                    service=email_svc, slug=DEFAULT_PROMPT_SLUG
                ).first()
                if target is None:
                    prompt.service = email_svc
                    prompt.slug = DEFAULT_PROMPT_SLUG
                    prompt.is_default = True
                    prompt.save()
                else:
                    prompt.is_active = False
                    prompt.is_default = False
                    prompt.save()
                self.stdout.write(f"  ✓ Migrated legacy email prompt {slug!r}")
            elif slug in LEGACY_DEFAULT_SLUGS and slug != DEFAULT_PROMPT_SLUG:
                if not AIPromptConfiguration.objects.filter(
                    service=opt_svc, slug=DEFAULT_PROMPT_SLUG
                ).exists():
                    prompt.slug = DEFAULT_PROMPT_SLUG
                    prompt.is_default = True
                    prompt.save()
