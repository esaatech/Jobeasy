from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ai_service.models import AIModel, AIPromptConfiguration, AIService, ResumeJobEvaluation
from ai_service.resume_job_evaluation import RESUME_JOB_EVALUATION_SERVICE_SLUG

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
