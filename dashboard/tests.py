from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ai_service.models import AIModel, AIPromptConfiguration, AIService, ResumeJobEvaluation, WhyShouldIApplyAnswer
from ai_service.resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG
from ai_service.why_should_i_apply import WHY_SHOULD_I_APPLY_SERVICE_SLUG

from resume_builder.models import Resume

from .models import JobApplication


class JobApplicationDetailViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.job_app = JobApplication.objects.create(
            user=self.user,
            job_name="Test Role",
            job_description="Build things.",
            application_kind=JobApplication.APPLICATION_KIND_MANUAL,
            status="completed",
        )

    def test_owner_gets_200(self):
        self.client.login(username="owner", password="pass")
        url = reverse("dashboard:job_application_detail", args=[self.job_app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Role")
        self.assertContains(response, "Build things.")

    def test_other_user_gets_404(self):
        self.client.login(username="other", password="pass")
        url = reverse("dashboard:job_application_detail", args=[self.job_app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_updates_company_fields(self):
        self.client.login(username="owner", password="pass")
        url = reverse("dashboard:job_application_detail", args=[self.job_app.id])
        response = self.client.post(
            url,
            {"company_name": "Acme", "company_email": "hr@acme.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.job_app.refresh_from_db()
        self.assertEqual(self.job_app.company_name, "Acme")
        self.assertEqual(self.job_app.company_email, "hr@acme.com")


class JobApplicationFitReviewDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fituser", password="pass")
        svc = AIService.objects.create(
            slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
            name="Eval",
            is_active=True,
        )
        flash = AIModel.objects.create(
            provider=AIModel.Provider.GEMINI,
            model_id="gemini-2.5-flash",
            display_name="Flash",
            is_active=True,
        )
        prompt = AIPromptConfiguration.objects.create(
            service=svc,
            name="Default",
            slug="default-job-evaluation",
            system_prompt="test",
            ai_model=flash,
            is_active=True,
        )
        self.eval_row = ResumeJobEvaluation.objects.create(
            user=self.user,
            job_description="Need Python.",
            resume_text="Python dev",
            prompt_config=prompt,
            succeeded=True,
            overall_score=55,
            recommendation="Weak Fit",
            evaluation_json={
                "overall_score": 55,
                "recommendation": "Weak Fit",
                "optimization_potential": 72,
                "dimension_summaries": {"proceed_reasoning": "Gaps in domain."},
                "gaps": ["Kubernetes"],
                "strengths": ["Python"],
            },
        )
        self.job_app = JobApplication.objects.create(
            user=self.user,
            job_name="Backend Role",
            job_description="Need Python.",
            status="fit_review",
            fit_evaluation=self.eval_row,
        )
        self.eval_row.job_application = self.job_app
        self.eval_row.save()

    def test_fit_review_detail_renders_summary(self):
        self.client.login(username="fituser", password="pass")
        url = reverse("dashboard:job_application_detail", args=[self.job_app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fit summary")
        self.assertContains(response, "Weak Fit")
        self.assertContains(response, "Generate resume")
        self.assertNotContains(response, "Compose email")


class JobApplicationCompletedFitMetricsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="doneuser", password="pass")
        svc = AIService.objects.create(
            slug=RESUME_JOB_EVALUATION_SERVICE_SLUG,
            name="Eval",
            is_active=True,
        )
        flash = AIModel.objects.create(
            provider=AIModel.Provider.GEMINI,
            model_id="gemini-2.5-flash",
            display_name="Flash",
            is_active=True,
        )
        prompt = AIPromptConfiguration.objects.create(
            service=svc,
            name="Default",
            slug="default-job-evaluation",
            system_prompt="test",
            ai_model=flash,
            is_active=True,
        )
        self.eval_row = ResumeJobEvaluation.objects.create(
            user=self.user,
            job_description="Need Python.",
            resume_text="Python dev",
            prompt_config=prompt,
            succeeded=True,
            overall_score=82,
            recommendation="Good Fit",
            evaluation_json={
                "overall_score": 82,
                "recommendation": "Good Fit",
                "optimization_potential": 88,
                "dimension_summaries": {"proceed_reasoning": "Strong match."},
                "gaps": [],
                "strengths": ["Python"],
            },
        )
        self.job_app = JobApplication.objects.create(
            user=self.user,
            job_name="Senior Backend",
            job_description="Need Python.",
            status="completed",
            fit_evaluation=self.eval_row,
        )
        self.eval_row.job_application = self.job_app
        self.eval_row.save()

    def test_completed_detail_shows_fit_hero_metrics(self):
        self.client.login(username="doneuser", password="pass")
        url = reverse("dashboard:job_application_detail", args=[self.job_app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Job fit evaluation")
        self.assertContains(response, "Overall score")
        self.assertContains(response, "Recommendation")
        self.assertContains(response, "Optimization potential")
        self.assertContains(response, "Good Fit")
        self.assertNotContains(response, "Why generation was paused")

    def test_unified_list_includes_fit_summary_for_completed(self):
        from dashboard.views import get_unified_job_applications

        items = get_unified_job_applications(self.user)
        dashboard_items = [i for i in items if i["source"] == "dashboard"]
        self.assertEqual(len(dashboard_items), 1)
        self.assertEqual(dashboard_items[0]["fit_summary"]["overall_score"], 82)
        self.assertEqual(dashboard_items[0]["fit_summary"]["recommendation"], "Good Fit")


class WhyShouldIApplyDocumentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="applyuser", password="pass")
        self.resume = Resume.objects.create(
            user=self.user,
            name="My Resume",
            personal_info={"full_name": "Jane Doe", "summary": "Full stack engineer."},
            experience=[{"title": "Engineer", "company": "Acme", "description": "Built APIs."}],
        )
        AIService.objects.get_or_create(
            slug=WHY_SHOULD_I_APPLY_SERVICE_SLUG,
            defaults={"name": "Why Should I Apply", "is_active": True},
        )
        self.job_app = JobApplication.objects.create(
            user=self.user,
            job_name="Backend Role",
            job_description="Need Python and Django.",
            resume=self.resume,
            status="completed",
        )

    def test_detail_shows_why_apply_section(self):
        self.client.login(username="applyuser", password="pass")
        url = reverse("dashboard:job_application_detail", args=[self.job_app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Why should we hire you?")
        self.assertContains(response, "Generate")

    def test_generate_creates_answer(self):
        from unittest.mock import patch

        self.client.login(username="applyuser", password="pass")
        url = reverse("dashboard:generate_why_should_i_apply", args=[self.job_app.id])
        mock_result = {
            "success": True,
            "answer_text": "I bring six years of Python experience.",
            "error": None,
            "raw_text": "I bring six years of Python experience.",
            "gemini_model": "gemini-2.5-flash",
            "instruction_slug": "v1-0",
            "prompt_config_id": None,
            "temperature": 0.55,
        }
        with patch(
            "ai_service.dashboard_why_should_i_apply.generate_why_should_i_apply",
            return_value=mock_result,
        ):
            response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.job_app.refresh_from_db()
        self.assertIsNotNone(self.job_app.why_should_i_apply_answer)
        self.assertEqual(
            self.job_app.why_should_i_apply_answer.content,
            "I bring six years of Python experience.",
        )

    def test_download_completed_answer(self):
        answer = WhyShouldIApplyAnswer.objects.create(
            user=self.user,
            content="Hire me because of Python.",
            status="completed",
        )
        self.job_app.why_should_i_apply_answer = answer
        self.job_app.save()

        self.client.login(username="applyuser", password="pass")
        url = reverse("dashboard:download_why_should_i_apply", args=[self.job_app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn(b"Hire me because of Python.", response.content)
