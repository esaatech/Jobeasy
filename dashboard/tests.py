from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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
