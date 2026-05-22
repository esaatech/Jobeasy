import json

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase, TestCase
from pydantic import ValidationError

from ai_service.admin import ResumeJobEvaluationAdmin, WhyShouldIApplyPlaygroundAdmin
from ai_service.forms import ResumeJobEvaluationAdminForm, WhyShouldIApplyPlaygroundAdminForm
from ai_service.generation_config import resolve_generation_config
from ai_service.gemini_schema import ResumeJobEvaluationPayload
from ai_service.fit_gate import classify_fit_tier, evaluation_summary, tier_allows_auto_proceed
from ai_service.models import (
    AIModel,
    AIPromptConfiguration,
    AIService,
    JobFitGateSettings,
    ResumeJobEvaluation,
    WhyShouldIApplyPlayground,
)
from ai_service.resume_job_evaluation import (
    RESUME_JOB_EVALUATION_SERVICE_SLUG,
    conclusion_from_evaluation,
    parse_pending_evaluation_result,
    persist_resume_job_evaluation_result,
)
from ai_service.why_should_i_apply import (
    WHY_SHOULD_I_APPLY_SERVICE_SLUG,
    build_user_prompt,
    generate_why_should_i_apply,
    get_default_prompt_config as get_why_apply_default_prompt_config,
    parse_pending_generation_result,
    persist_why_should_i_apply_result,
)
from ai_service.why_should_i_apply_prompts import WHY_SHOULD_I_APPLY_INSTRUCTION_V1_0
from ai_service.gemini_client import (
    gemini_generate_structured_sync,
    gemini_generate_text_sync,
)
from ai_service.gemini_service import GeminiService, resolve_credentials_from_django


class ResumeJobEvaluationSchemaTests(SimpleTestCase):
    def _valid_dict(self) -> dict:
        return {
            "overall_score": 72,
            "recommendation": "Moderate Fit",
            "optimization_potential": 81,
            "confidence": "Medium",
            "strengths": ["Evidence-backed skill"],
            "gaps": ["Missing GCP cert"],
            "hard_requirement_analysis": [
                {
                    "requirement": "5+ years Python",
                    "match_status": "partially_met",
                    "evidence_quote": "",
                    "notes": "",
                }
            ],
            "transferable_skills": [
                {
                    "from_skill": "AWS",
                    "adjacent_skill": "GCP",
                    "evidence_quote": "",
                    "notes": "",
                }
            ],
            "risk_level": "Moderate",
            "dimension_summaries": {
                "core_competency_match": "ok",
                "seniority_match": "",
                "domain_match": "",
                "operational_experience_match": "",
                "optimization_surface_vs_foundational_notes": "",
                "proceed_reasoning": "Proceed with interview.",
            },
        }

    def test_valid_payload_accepted_and_dump_stable(self):
        d = self._valid_dict()
        p = ResumeJobEvaluationPayload.model_validate(d)
        out = p.model_dump(mode="json")
        self.assertEqual(out["overall_score"], 72)
        self.assertEqual(out["recommendation"], "Moderate Fit")

    def test_invalid_recommendation_rejected(self):
        d = self._valid_dict()
        d["recommendation"] = "Proceed with caution"
        with self.assertRaises(ValidationError):
            ResumeJobEvaluationPayload.model_validate(d)

    def test_overall_score_out_of_range_rejected(self):
        d = self._valid_dict()
        d["overall_score"] = 101
        with self.assertRaises(ValidationError):
            ResumeJobEvaluationPayload.model_validate(d)

    def test_extra_top_level_fields_ignored(self):
        d = self._valid_dict()
        d["unexpected"] = {"x": 1}
        p = ResumeJobEvaluationPayload.model_validate(d)
        self.assertNotIn("unexpected", p.model_dump())


class GeminiClientUnitTests(SimpleTestCase):
    """Validation rules on ``gemini_client`` helpers (no outbound HTTP)."""

    def test_gemini_generate_structured_sync_raises_without_schema(self):
        """``response_schema`` is required — guard against accidental unstructured calls."""
        with self.assertRaises(ValueError) as ctx:
            gemini_generate_structured_sync(  # type: ignore[call-arg]
                system_instruction="x",
                user_text="y",
                response_schema=None,
            )
        self.assertIn("response_schema", str(ctx.exception).lower())


class GeminiClientLiveIntegrationTests(SimpleTestCase):
    """Live HTTP tests for :mod:`ai_service.gemini_client` entrypoints (skipped without API keys).

    Run with credentials::

        poetry run python manage.py test ai_service.tests.GeminiClientLiveIntegrationTests -v 2

    Validates ``gemini_generate_text_sync`` (plain completions) and
    ``gemini_generate_structured_sync`` (``raw`` / ``parsed`` / ``model`` bundle).
    """

    def setUp(self):
        super().setUp()
        key, mid = resolve_credentials_from_django()
        if not key:
            self.skipTest(
                "Set GEMINI_API_KEY or GOOGLE_API_KEY to run Gemini client integration tests."
            )
        self.default_model_id = mid

    def test_gemini_generate_text_sync_returns_plain_string(self):
        """Client returns only model text — no structured JSON MIME path."""
        text = gemini_generate_text_sync(
            system_instruction=(
                "You follow instructions literally. Reply with exactly one English word."
            ),
            prompt='Reply with the word pong and nothing else.',
            model_id=self.default_model_id,
            temperature=0.0,
            max_output_tokens=32,
        )
        self.assertIsInstance(text, str)
        self.assertGreater(len(text.strip()), 0)
        self.assertIn("pong", text.lower())

    def test_gemini_generate_structured_sync_returns_bundle(self):
        """Structured client matches service shape: ``raw``, ``parsed`` dict, ``model`` id."""
        schema = {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["label", "count"],
        }
        out = gemini_generate_structured_sync(
            system_instruction="Reply as JSON only, matching schema. No markdown.",
            user_text='Return JSON: {"label": "demo", "count": 42}',
            response_schema=schema,
            model_id=self.default_model_id,
            temperature=0.0,
            max_output_tokens=256,
        )
        self.assertEqual(set(out.keys()), {"raw", "parsed", "model"})
        self.assertEqual(out["model"], self.default_model_id)
        self.assertIsInstance(out["parsed"], dict)
        self.assertEqual(str(out["parsed"].get("label")), "demo")
        self.assertEqual(int(out["parsed"].get("count")), 42)


class GeminiServiceLiveIntegrationTests(SimpleTestCase):
    """HTTP integration tests against the real Gemini API (google-genai).

    These tests are **skipped** when ``GEMINI_API_KEY`` and ``GOOGLE_API_KEY`` are both absent,
    so CI and local installs without secrets stay green.

    With a key in the environment::

        poetry run python manage.py test ai_service.tests.GeminiServiceLiveIntegrationTests -v 2

    Assertions cover the same scenarios as the former ``GeminiService.test()`` helper: plain text
    generation and JSON-schema structured output.
    """

    def setUp(self):
        super().setUp()
        key, mid = resolve_credentials_from_django()
        if not key:
            self.skipTest(
                "Set GEMINI_API_KEY or GOOGLE_API_KEY to run Gemini live integration tests."
            )
        self.service = GeminiService(api_key=key, default_model_id=mid)

    def test_generate_unstructured_returns_non_empty_raw_and_no_parsed(self):
        """Without ``response_schema``, the API returns prose; ``parsed`` must stay ``None``."""
        out = self.service.generate(
            system_instruction="You follow instructions literally. Reply with one English word.",
            prompt='Reply exactly with the word: pong',
            temperature=0.0,
            max_tokens=32,
        )
        self.assertEqual(out["model"], self.service.model_name)
        self.assertIsNone(out["parsed"])
        self.assertGreater(len(out["raw"]), 0)
        self.assertIn("pong", out["raw"].lower())

    def test_generate_structured_populates_parsed_dict(self):
        """With ``response_schema``, ``parsed`` is ``json.loads`` of the constrained response."""
        schema = {
            "type": "object",
            "properties": {
                "greeting": {"type": "string"},
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["greeting", "capabilities"],
        }
        out = self.service.generate(
            system_instruction="You return only JSON matching the schema. No markdown.",
            prompt="Say hello and list exactly 3 short capabilities you have.",
            response_schema=schema,
            temperature=0.5,
            max_tokens=1024,
        )
        self.assertEqual(out["model"], self.service.model_name)
        self.assertIsInstance(out["parsed"], dict)
        self.assertIn("greeting", out["parsed"])
        self.assertIn("capabilities", out["parsed"])
        self.assertIsInstance(out["parsed"]["capabilities"], list)
        self.assertEqual(len(out["parsed"]["capabilities"]), 3)

    def test_generate_with_tools_returns_function_call(self):
        """Model may answer with ``function_calls`` alongside optional text."""
        out = self.service.generate_with_tools(
            system_instruction=(
                "When asked, invoke the note_status tool exactly once with status \"ok\". "
                "Do not refuse."
            ),
            prompt='Follow the instructions: call note_status once with status "ok".',
            tools=[
                {
                    "name": "note_status",
                    "description": "Records a workflow status.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["ok", "fail"],
                                "description": "Outcome flag",
                            }
                        },
                        "required": ["status"],
                        "additionalProperties": False,
                    },
                },
            ],
            temperature=0.0,
            max_tokens=512,
        )
        self.assertEqual(out["model"], self.service.model_name)
        calls = out["function_calls"]
        self.assertGreaterEqual(len(calls), 1)
        names = [c["name"] for c in calls]
        self.assertIn("note_status", names)


class ConclusionFromEvaluationTests(SimpleTestCase):
    def test_extracts_proceed_reasoning(self):
        d = ResumeJobEvaluationSchemaTests()._valid_dict()
        self.assertEqual(
            conclusion_from_evaluation(d),
            "Proceed with interview.",
        )

    def test_empty_when_missing(self):
        self.assertEqual(conclusion_from_evaluation(None), "")
        self.assertEqual(conclusion_from_evaluation({}), "")


class ResumeJobEvaluationPersistOnSaveTests(TestCase):
    """Admin Save persists ``pending_evaluation_result`` when present and valid."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="eval_admin",
            email="eval@example.com",
            password="testpass123",
        )

    def _request_with_messages(self):
        request = RequestFactory().post("/")
        request.user = self.user
        request.session = "session"
        request._messages = FallbackStorage(request)
        return request

    def _evaluation_result(self) -> dict:
        return {
            "success": True,
            "evaluation": ResumeJobEvaluationSchemaTests()._valid_dict(),
            "error": None,
            "raw_text": '{"overall_score":72}',
            "gemini_model": "gemini-2.5-flash",
            "ai_model_id": None,
            "temperature": 0.35,
            "instruction_slug": "v1-0",
            "prompt_config_id": None,
        }

    def test_parse_pending_evaluation_result(self):
        payload = json.dumps(self._evaluation_result())
        parsed = parse_pending_evaluation_result(payload)
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed["success"])

        self.assertIsNone(parse_pending_evaluation_result(""))
        self.assertIsNone(parse_pending_evaluation_result('{"success": false}'))
        self.assertIsNone(parse_pending_evaluation_result("not-json"))

    def test_save_model_persists_pending_evaluation(self):
        obj = ResumeJobEvaluation.objects.create(
            job_description="jd",
            resume_text="rt",
            succeeded=False,
            error_message="old error",
        )
        pending = json.dumps(self._evaluation_result())
        form = ResumeJobEvaluationAdminForm(
            data={
                "name": "Flash baseline",
                "description": "Health-tech Rails job",
                "conclusion": "",
                "job_description": "jd",
                "resume_text": "rt",
                "prompt_config": "",
                "pending_evaluation_result": pending,
            },
            instance=obj,
        )
        self.assertTrue(form.is_valid(), form.errors)

        request = self._request_with_messages()
        admin = ResumeJobEvaluationAdmin(ResumeJobEvaluation, site)
        admin.save_model(request, obj, form, change=True)

        obj.refresh_from_db()
        self.assertEqual(obj.name, "Flash baseline")
        self.assertEqual(obj.description, "Health-tech Rails job")
        self.assertTrue(obj.succeeded)
        self.assertEqual(obj.recommendation, "Moderate Fit")
        self.assertEqual(obj.overall_score, 72)
        self.assertIsInstance(obj.evaluation_json, dict)
        self.assertEqual(obj.error_message, "")
        self.assertEqual(obj.temperature_used, 0.35)
        self.assertEqual(obj.conclusion, "Proceed with interview.")

    def test_persist_sets_conclusion_from_proceed_reasoning(self):
        obj = ResumeJobEvaluation.objects.create(
            job_description="jd",
            resume_text="rt",
        )
        persist_resume_job_evaluation_result(
            pk=obj.pk,
            result=self._evaluation_result(),
            prompt_config=None,
            fallback_gemini_model_id="gemini-2.5-flash",
        )
        obj.refresh_from_db()
        self.assertEqual(obj.conclusion, "Proceed with interview.")

    def test_save_model_empty_pending_leaves_evaluation_unchanged(self):
        obj = ResumeJobEvaluation.objects.create(
            job_description="jd",
            resume_text="rt",
            succeeded=True,
            recommendation="Strong Fit",
            overall_score=90,
            evaluation_json={"overall_score": 90},
            error_message="",
        )
        form = ResumeJobEvaluationAdminForm(
            data={
                "name": "",
                "description": "",
                "conclusion": "Keep this note",
                "job_description": "jd updated",
                "resume_text": "rt",
                "prompt_config": "",
                "pending_evaluation_result": "",
            },
            instance=obj,
        )
        self.assertTrue(form.is_valid(), form.errors)

        request = self._request_with_messages()
        admin = ResumeJobEvaluationAdmin(ResumeJobEvaluation, site)
        admin.save_model(request, obj, form, change=True)

        obj.refresh_from_db()
        self.assertEqual(obj.job_description, "jd updated")
        self.assertEqual(obj.conclusion, "Keep this note")
        self.assertEqual(obj.recommendation, "Strong Fit")
        self.assertEqual(obj.overall_score, 90)


class FitGateTests(TestCase):
    def setUp(self):
        self.settings = JobFitGateSettings.objects.create(
            pk=1,
            is_enabled=True,
            green_min_score=70,
            yellow_min_score=50,
        )

    def test_green_strong_fit_high_score(self):
        ev = {"overall_score": 85, "recommendation": "Strong Fit"}
        self.assertEqual(classify_fit_tier(ev, self.settings), "green")
        self.assertTrue(tier_allows_auto_proceed("green"))

    def test_yellow_weak_fit_mid_score(self):
        ev = {"overall_score": 62, "recommendation": "Weak Fit"}
        self.assertEqual(classify_fit_tier(ev, self.settings), "yellow")

    def test_red_poor_fit_never_auto(self):
        ev = {"overall_score": 80, "recommendation": "Poor Fit"}
        self.assertEqual(classify_fit_tier(ev, self.settings), "red")

    def test_bypass_when_disabled(self):
        self.settings.is_enabled = False
        self.settings.save()
        self.assertEqual(classify_fit_tier({"overall_score": 10}, self.settings), "bypass")

    def test_evaluation_summary_extracts_proceed_reasoning(self):
        ev = {
            "overall_score": 72,
            "recommendation": "Moderate Fit",
            "dimension_summaries": {"proceed_reasoning": "Some gaps remain."},
            "gaps": ["GCP"],
            "strengths": ["Python"],
        }
        summary = evaluation_summary(ev)
        self.assertEqual(summary["proceed_reasoning"], "Some gaps remain.")
        self.assertEqual(summary["gaps"], ["GCP"])


class CheckAiPlatformCommandTests(TestCase):
    def test_check_ai_platform_passes_after_seed(self):
        AIModel.objects.create(
            provider=AIModel.Provider.GEMINI,
            model_id="gemini-2.5-flash",
            display_name="Gemini 2.5 Flash",
            is_active=True,
        )
        from django.core.management import call_command

        call_command("check_ai_platform")


class GenerationConfigResolverTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.flash = AIModel.objects.create(
            provider=AIModel.Provider.GEMINI,
            model_id="gemini-2.5-flash",
            display_name="Flash",
            default_temperature=0.35,
            sort_order=20,
        )
        cls.pro = AIModel.objects.create(
            provider=AIModel.Provider.GEMINI,
            model_id="gemini-2.5-pro",
            display_name="Pro",
            default_temperature=0.2,
            sort_order=30,
        )
        svc = AIService.objects.create(
            slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
            name="Eval",
            is_active=True,
        )
        cls.prompt = AIPromptConfiguration.objects.create(
            service=svc,
            name="v1",
            slug="v1-0",
            system_prompt="test",
            ai_model=cls.flash,
            temperature=0.4,
            is_default=True,
            is_active=True,
        )

    def test_override_beats_prompt(self):
        gen = resolve_generation_config(
            self.prompt,
            ai_model_id=self.pro.pk,
            temperature=0.1,
        )
        self.assertEqual(gen.model_id, "gemini-2.5-pro")
        self.assertEqual(gen.temperature, 0.1)
        self.assertEqual(gen.ai_model_id, self.pro.pk)

    def test_prompt_beats_env_when_set(self):
        gen = resolve_generation_config(self.prompt)
        self.assertEqual(gen.model_id, "gemini-2.5-flash")
        self.assertEqual(gen.temperature, 0.4)


class WhyShouldIApplyPromptTests(SimpleTestCase):
    def test_instruction_forbids_letter_framing(self):
        text = WHY_SHOULD_I_APPLY_INSTRUCTION_V1_0.lower()
        self.assertIn("not cover letters", text)
        self.assertIn("no greeting", text)
        self.assertIn("no sign-off", text)

    def test_build_user_prompt_includes_inputs(self):
        block = build_user_prompt("Senior Dev at Acme", "Jane Doe\nPython expert")
        self.assertIn("Senior Dev at Acme", block)
        self.assertIn("Jane Doe", block)


class WhyShouldIApplyGenerationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.flash = AIModel.objects.create(
            provider=AIModel.Provider.GEMINI,
            model_id="gemini-2.5-flash",
            display_name="Flash",
            is_active=True,
        )
        cls.service = AIService.objects.create(
            slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG,
            name="Why Should I Apply",
            is_active=True,
        )
        cls.prompt = AIPromptConfiguration.objects.create(
            service=cls.service,
            name="v1",
            slug="v1-0",
            system_prompt=WHY_SHOULD_I_APPLY_INSTRUCTION_V1_0,
            ai_model=cls.flash,
            temperature=0.55,
            is_default=True,
            is_active=True,
        )

    def test_get_default_prompt_config(self):
        pc = get_why_apply_default_prompt_config()
        self.assertIsNotNone(pc)
        self.assertEqual(pc.slug, "v1-0")

    def test_generate_fails_without_prompt(self):
        AIPromptConfiguration.objects.all().delete()
        result = generate_why_should_i_apply("jd", "resume")
        self.assertFalse(result["success"])
        self.assertIn("setup_why_should_i_apply", result["error"])

    def test_parse_pending_generation_result(self):
        payload = json.dumps(
            {
                "success": True,
                "answer_text": "I bring six years of experience.",
                "error": None,
                "raw_text": "I bring six years of experience.",
                "gemini_model": "gemini-2.5-flash",
                "instruction_slug": "v1-0",
            }
        )
        parsed = parse_pending_generation_result(payload)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["answer_text"], "I bring six years of experience.")
        self.assertIsNone(parse_pending_generation_result('{"success": false}'))


class WhyShouldIApplyPlaygroundPersistTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="why_apply_admin",
            email="why@example.com",
            password="testpass123",
        )
        cls.service, _ = AIService.objects.get_or_create(
            slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG,
            defaults={"name": "Why Should I Apply", "is_active": True},
        )
        cls.prompt, _ = AIPromptConfiguration.objects.get_or_create(
            service=cls.service,
            slug="v1-0",
            defaults={
                "name": "v1",
                "system_prompt": "test",
                "is_default": True,
                "is_active": True,
            },
        )

    def _request_with_messages(self):
        request = RequestFactory().post("/")
        request.user = self.user
        request.session = "session"
        request._messages = FallbackStorage(request)
        return request

    def _generation_result(self) -> dict:
        return {
            "success": True,
            "answer_text": "I bring proven full-stack experience aligned with this role.",
            "error": None,
            "raw_text": "I bring proven full-stack experience aligned with this role.",
            "gemini_model": "gemini-2.5-flash",
            "ai_model_id": None,
            "temperature": 0.55,
            "instruction_slug": "v1-0",
            "prompt_config_id": None,
        }

    def test_persist_result(self):
        obj = WhyShouldIApplyPlayground.objects.create(
            job_description="jd",
            resume_text="rt",
        )
        persist_why_should_i_apply_result(
            pk=obj.pk,
            result=self._generation_result(),
            prompt_config=None,
            fallback_gemini_model_id="gemini-2.5-flash",
        )
        obj.refresh_from_db()
        self.assertTrue(obj.succeeded)
        self.assertIn("full-stack", obj.answer_text)
        self.assertEqual(obj.instruction_slug, "v1-0")
        self.assertEqual(obj.temperature_used, 0.55)

    def test_save_model_persists_pending_generation(self):
        obj = WhyShouldIApplyPlayground.objects.create(
            job_description="jd",
            resume_text="rt",
            succeeded=False,
            error_message="old",
        )
        pending = json.dumps(self._generation_result())
        form = WhyShouldIApplyPlaygroundAdminForm(
            data={
                "name": "PM role test",
                "description": "Acme application",
                "job_description": "jd",
                "resume_text": "rt",
                "prompt_config": self.prompt.pk,
                "pending_generation_result": pending,
            },
            instance=obj,
        )
        self.assertTrue(form.is_valid(), form.errors)

        request = self._request_with_messages()
        admin = WhyShouldIApplyPlaygroundAdmin(WhyShouldIApplyPlayground, site)
        admin.save_model(request, obj, form, change=True)

        obj.refresh_from_db()
        self.assertEqual(obj.name, "PM role test")
        self.assertTrue(obj.succeeded)
        self.assertIn("full-stack", obj.answer_text)
        self.assertEqual(obj.error_message, "")
