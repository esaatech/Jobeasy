from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from job_service.models import Job, JobSource, JobScrapingLog
from job_service.scrapers.base import ScrapedJob


User = get_user_model()


@override_settings(ROOT_URLCONF='jobeas.urls')
class JobSourceAdminScrapeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='scrapeadmin',
            email='scrapeadmin@example.com',
            password='pass12345',
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.source = JobSource.objects.create(
            name='Spotify',
            url='https://jobs.lever.co/spotify',
            source_type='api',
            is_active=True,
        )

    def test_change_form_shows_scrape_button(self):
        url = reverse('admin:job_service_jobsource_change', args=[self.source.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scrape jobs now')
        scrape_url = f'/admin/job_service/jobsource/{self.source.pk}/scrape/'
        self.assertContains(response, scrape_url)
        # Nested <form action=".../scrape/"> breaks in Django admin; use formaction.
        self.assertContains(response, f'formaction="{scrape_url}"')
        self.assertNotContains(response, f'<form method="post" action="{scrape_url}"')

    @patch('job_service.admin.scrape_source')
    def test_scrape_post_calls_shared_pipeline(self, mock_scrape):
        mock_scrape.return_value = (3, 1, 0, 4)
        url = reverse('admin:job_service_jobsource_scrape', args=[self.source.pk])
        response = self.client.post(url, {'fetch_details': '1'})
        self.assertEqual(response.status_code, 302)
        mock_scrape.assert_called_once_with(self.source, fetch_details=True)

    @patch('job_service.services.ingestion.get_scraper')
    def test_scrape_persists_jobs_and_log(self, mock_get_scraper):
        scraped = [
            ScrapedJob(
                external_id='lever:test-1',
                title='Backend Engineer',
                company='Spotify',
                location='Remote',
                job_type='full-time',
                description='Build APIs',
                application_url='https://jobs.lever.co/spotify/test-1',
            )
        ]

        class FakeScraper:
            def fetch(self):
                return scraped

        mock_get_scraper.return_value = FakeScraper()
        url = reverse('admin:job_service_jobsource_scrape', args=[self.source.pk])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Job.objects.filter(source=self.source).count(), 1)
        log = JobScrapingLog.objects.filter(source=self.source).latest('id')
        self.assertEqual(log.status, 'completed')
        self.assertEqual(log.jobs_found, 1)
        self.assertEqual(log.jobs_added, 1)
