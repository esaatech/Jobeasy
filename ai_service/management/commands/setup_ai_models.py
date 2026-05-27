"""Seed provider model catalog rows (Gemini, OpenAI, DeepSeek) for admin and prompt configuration."""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_service.models import AIModel


# GPT-5.x — latest OpenAI frontier (see https://developers.openai.com/api/docs/models)
OPENAI_MODELS_GPT5 = [
    {
        "model_id": "gpt-5.5",
        "display_name": "GPT-5.5",
        "description": "OpenAI flagship for complex reasoning and coding (recommended default).",
        "sort_order": 100,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5.4",
        "display_name": "GPT-5.4",
        "description": "Strong general-purpose GPT-5.4 model; 1M context window.",
        "sort_order": 101,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5.4-mini",
        "display_name": "GPT-5.4 mini",
        "description": "Lower latency and cost than GPT-5.4.",
        "sort_order": 102,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5.4-nano",
        "display_name": "GPT-5.4 nano",
        "description": "Fastest, most cost-efficient GPT-5.4 variant.",
        "sort_order": 103,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5.2",
        "display_name": "GPT-5.2",
        "description": "Prior-generation GPT-5.2 for stable production workloads.",
        "sort_order": 104,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5.1",
        "display_name": "GPT-5.1",
        "description": "GPT-5.1 general model.",
        "sort_order": 105,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5",
        "display_name": "GPT-5",
        "description": "Base GPT-5 model.",
        "sort_order": 106,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5-mini",
        "display_name": "GPT-5 mini",
        "description": "Smaller GPT-5 variant for cost-sensitive tasks.",
        "sort_order": 107,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "gpt-5-nano",
        "display_name": "GPT-5 nano",
        "description": "Smallest GPT-5 variant for high-throughput tasks.",
        "sort_order": 108,
        "default_temperature": Decimal("0.35"),
    },
]

# GPT-4.x — existing JobEas integrations (hardcoded until wired to AIModel)
OPENAI_MODELS_GPT4 = [
    {
        "model_id": "gpt-4o-mini",
        "display_name": "GPT-4o mini",
        "description": "Fast, cost-efficient OpenAI model for assistants and light tasks.",
        "sort_order": 110,
        "default_temperature": Decimal("0.30"),
    },
    {
        "model_id": "gpt-4o",
        "display_name": "GPT-4o",
        "description": "General-purpose OpenAI model (summary, cover letter, optimization).",
        "sort_order": 120,
        "default_temperature": Decimal("0.30"),
    },
    {
        "model_id": "gpt-4o-2024-08-06",
        "display_name": "GPT-4o (2024-08-06)",
        "description": "Structured-output parsing (resume upload / Pydantic parse).",
        "sort_order": 130,
        "default_temperature": Decimal("0.10"),
    },
    {
        "model_id": "gpt-4",
        "display_name": "GPT-4",
        "description": "Legacy GPT-4 id still referenced by some services.",
        "sort_order": 140,
        "default_temperature": Decimal("0.30"),
    },
]

OPENAI_MODELS = OPENAI_MODELS_GPT5 + OPENAI_MODELS_GPT4

# DeepSeek V4 — https://api-docs.deepseek.com/
DEEPSEEK_MODELS = [
    {
        "model_id": "deepseek-v4-pro",
        "display_name": "DeepSeek V4 Pro",
        "description": "Frontier tier: coding, agents, 1M context (recommended).",
        "sort_order": 40,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "deepseek-v4-flash",
        "display_name": "DeepSeek V4 Flash",
        "description": "Default chat tier; enable thinking via API params, not model id.",
        "sort_order": 41,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "deepseek-chat",
        "display_name": "DeepSeek Chat (legacy)",
        "description": "Alias to V4 Flash non-thinking; deprecated 2026-07-24.",
        "sort_order": 42,
        "default_temperature": Decimal("0.35"),
    },
    {
        "model_id": "deepseek-reasoner",
        "display_name": "DeepSeek Reasoner (legacy)",
        "description": "Alias to V4 Flash thinking mode; deprecated 2026-07-24.",
        "sort_order": 43,
        "default_temperature": Decimal("0.35"),
    },
]


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
    help = "Create or update AIModel rows for Gemini, OpenAI (GPT-5/4), and DeepSeek V4."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up AI model catalog…"))
        with transaction.atomic():
            self._seed_provider(AIModel.Provider.GEMINI, GEMINI_MODELS)
            self._seed_provider(AIModel.Provider.DEEPSEEK, DEEPSEEK_MODELS)
            self._seed_provider(AIModel.Provider.OPENAI, OPENAI_MODELS)
        self.stdout.write(self.style.SUCCESS("\nDone."))

    def _seed_provider(self, provider: str, specs: list[dict]) -> None:
        label = AIModel.Provider(provider).label
        self.stdout.write(f"\n{label}:")
        for spec in specs:
            obj, created = AIModel.objects.update_or_create(
                provider=provider,
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
