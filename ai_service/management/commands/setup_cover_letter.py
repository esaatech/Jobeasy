"""Seed two AIServices for cover letter generation (letter-only and with email subject).

Run after setup_ai_models::

    python manage.py setup_ai_models
    python manage.py setup_cover_letter
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.cover_letter import (
    COVER_LETTER_SERVICE_SLUG,
    COVER_LETTER_WITH_EMAIL_SUBJECT_SERVICE_SLUG,
    LEGACY_EMAIL_SUBJECT_PROMPT_SLUGS,
    LEGACY_LETTER_ONLY_PROMPT_SLUGS,
)
from ai_service.cover_letter_prompts import (
    COVER_LETTER_INSTRUCTION_LETTER_ONLY,
    COVER_LETTER_INSTRUCTION_WITH_EMAIL_SUBJECT,
)
from ai_service.models import AIModel, AIService, AIPromptConfiguration

DEFAULT_PROMPT_SLUG = "v1-0"


class Command(BaseCommand):
    help = (
        "Create or update cover letter AIServices (letter-only and with email subject) "
        "and their default prompt versions."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing default prompts' system_prompt text.",
        )

    def handle(self, *args, **options):
        force_update = options["force"]
        self.stdout.write(self.style.SUCCESS("Setting up cover letter prompts…"))

        services_spec = [
            {
                "slug": COVER_LETTER_SERVICE_SLUG,
                "name": "Cover Letter (letter only)",
                "description": (
                    "AI cover letter: title and body only. Used by the standalone "
                    "cover letter tool (coverletter app)."
                ),
                "system_prompt": COVER_LETTER_INSTRUCTION_LETTER_ONLY,
                "prompt_name": "Cover letter (letter only) v1.0",
            },
            {
                "slug": COVER_LETTER_WITH_EMAIL_SUBJECT_SERVICE_SLUG,
                "name": "Cover Letter (with email subject)",
                "description": (
                    "AI cover letter with email subject line. Used by the dashboard "
                    "generate flow when the user opts into a cover letter."
                ),
                "system_prompt": COVER_LETTER_INSTRUCTION_WITH_EMAIL_SUBJECT,
                "prompt_name": "Cover letter (with email subject) v1.0",
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

            letter_service = None
            email_service = None
            for spec in services_spec:
                svc, created = self._upsert_service(spec)
                if spec["slug"] == COVER_LETTER_SERVICE_SLUG:
                    letter_service = svc
                else:
                    email_service = svc
                self._upsert_default_prompt(
                    svc,
                    spec,
                    default_model=default_model,
                    force_update=force_update,
                )

            if letter_service and email_service:
                self._migrate_legacy_prompts(letter_service, email_service)

        self.stdout.write(
            self.style.SUCCESS(
                "\nDone. Admin: Cover letter playground; prompts under AI Prompt Configurations."
            )
        )

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
        if created:
            self.stdout.write(f"  ✓ Created AI service: {service.name}")
        else:
            for key, val in svc_defaults.items():
                setattr(service, key, val)
            service.save()
            self.stdout.write(f"  - AI service already exists: {service.name}")
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
        prompt_name = spec["prompt_name"]
        existing = AIPromptConfiguration.objects.filter(
            service=service, slug=slug
        ).first()

        prompt_defaults = {
            "name": prompt_name,
            "system_prompt": spec["system_prompt"],
            "is_default": True,
            "is_active": True,
            "ai_model": default_model,
            "temperature": Decimal("0.70"),
        }

        if existing and not force_update:
            self.stdout.write(f"  - Prompt already exists: {service.name} — {prompt_name}")
            patched = []
            if default_model and existing.ai_model_id is None:
                existing.ai_model = default_model
                patched.append("ai_model")
            if existing.temperature is None:
                existing.temperature = Decimal("0.70")
                patched.append("temperature")
            if not existing.is_default:
                existing.is_default = True
                patched.append("is_default")
            if patched:
                existing.save(update_fields=patched)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    Linked defaults on existing prompt: {', '.join(patched)}"
                    )
                )
            return

        if existing and force_update:
            for key, val in prompt_defaults.items():
                setattr(existing, key, val)
            existing.save()
            self.stdout.write(f"  ✓ Updated prompt: {service.name} — {prompt_name}")
        else:
            AIPromptConfiguration.objects.create(
                service=service, slug=slug, **prompt_defaults
            )
            self.stdout.write(f"  ✓ Created prompt: {service.name} — {prompt_name}")

    def _migrate_legacy_prompts(
        self,
        letter_service: AIService,
        email_service: AIService,
    ) -> None:
        """Move email-subject prompts off cover_letter; normalize letter-only slugs to v1-0."""
        for prompt in list(letter_service.prompts.all()):
            slug = (prompt.slug or "").strip()
            if slug in LEGACY_EMAIL_SUBJECT_PROMPT_SLUGS:
                target = (
                    AIPromptConfiguration.objects.filter(
                        service=email_service, slug=DEFAULT_PROMPT_SLUG
                    ).first()
                )
                if target is None:
                    prompt.service = email_service
                    prompt.slug = DEFAULT_PROMPT_SLUG
                    prompt.is_default = True
                    prompt.is_active = True
                    prompt.save(update_fields=["service", "slug", "is_default", "is_active"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Moved legacy email prompt {slug!r} → "
                            f"{email_service.slug}/{DEFAULT_PROMPT_SLUG}"
                        )
                    )
                else:
                    legacy_text = prompt.system_prompt.strip()
                    if legacy_text and not target.system_prompt.strip():
                        target.system_prompt = legacy_text
                        target.save(update_fields=["system_prompt"])
                    prompt.is_active = False
                    prompt.is_default = False
                    prompt.save(update_fields=["is_active", "is_default"])
                    self.stdout.write(
                        f"  - Deactivated duplicate legacy email prompt {slug!r} on cover_letter"
                    )
                continue

            if slug in LEGACY_LETTER_ONLY_PROMPT_SLUGS and slug != DEFAULT_PROMPT_SLUG:
                existing_v1 = AIPromptConfiguration.objects.filter(
                    service=letter_service, slug=DEFAULT_PROMPT_SLUG
                ).first()
                if existing_v1 is None:
                    prompt.slug = DEFAULT_PROMPT_SLUG
                    prompt.is_default = True
                    prompt.save(update_fields=["slug", "is_default"])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Renamed letter prompt {slug!r} → {DEFAULT_PROMPT_SLUG}"
                        )
                    )
                else:
                    prompt.is_active = False
                    prompt.is_default = False
                    prompt.save(update_fields=["is_active", "is_default"])
                    self.stdout.write(
                        f"  - Deactivated duplicate letter prompt {slug!r} on cover_letter"
                    )
