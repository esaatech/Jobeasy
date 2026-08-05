from django.test import TestCase

from job_service.models import Job, JobScrapingLog, JobSource
from job_service.scrapers.base import ScrapedJob
from job_service.services.ingestion import scrape_source, upsert_jobs


class UpsertJobsTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name='Test Co',
            url='https://jobs.lever.co/testco',
            source_type='api',
        )

    def test_upsert_creates_and_updates(self):
        scraped = [
            ScrapedJob(
                external_id='lever:1',
                title='Backend Engineer',
                company='Test Co',
                location='Remote',
                job_type='full-time',
                description='Build APIs',
                application_url='https://jobs.lever.co/testco/1',
            )
        ]
        added, updated, deactivated = upsert_jobs(self.source, scraped)
        self.assertEqual(added, 1)
        self.assertEqual(updated, 0)
        self.assertEqual(deactivated, 0)
        self.assertEqual(Job.objects.count(), 1)

        scraped[0] = ScrapedJob(
            external_id='lever:1',
            title='Senior Backend Engineer',
            company='Test Co',
            location='Remote',
            job_type='full-time',
            description='Build better APIs',
            application_url='https://jobs.lever.co/testco/1',
        )
        added, updated, deactivated = upsert_jobs(self.source, scraped)
        self.assertEqual(added, 0)
        self.assertEqual(updated, 1)
        self.assertEqual(deactivated, 0)
        self.assertEqual(Job.objects.get(external_id='lever:1').title, 'Senior Backend Engineer')

    def test_upsert_deactivates_missing_external_ids(self):
        upsert_jobs(
            self.source,
            [
                ScrapedJob(
                    external_id='lever:1',
                    title='Backend Engineer',
                    company='Test Co',
                    location='Remote',
                    job_type='full-time',
                    description='Build APIs',
                    application_url='https://jobs.lever.co/testco/1',
                ),
                ScrapedJob(
                    external_id='lever:2',
                    title='Frontend Engineer',
                    company='Test Co',
                    location='Remote',
                    job_type='full-time',
                    description='Build UI',
                    application_url='https://jobs.lever.co/testco/2',
                ),
            ],
        )
        self.assertEqual(Job.objects.filter(source=self.source, is_active=True).count(), 2)

        added, updated, deactivated = upsert_jobs(
            self.source,
            [
                ScrapedJob(
                    external_id='lever:1',
                    title='Backend Engineer',
                    company='Test Co',
                    location='Remote',
                    job_type='full-time',
                    description='Build APIs',
                    application_url='https://jobs.lever.co/testco/1',
                ),
            ],
        )
        self.assertEqual(added, 0)
        self.assertEqual(updated, 1)
        self.assertEqual(deactivated, 1)
        self.assertTrue(Job.objects.get(external_id='lever:1').is_active)
        self.assertFalse(Job.objects.get(external_id='lever:2').is_active)

    def test_upsert_persists_work_arrangement(self):
        scraped = [
            ScrapedJob(
                external_id='lever:remote-1',
                title='Remote Engineer',
                company='Test Co',
                location='Remote',
                job_type='full-time',
                description='Build APIs',
                application_url='https://jobs.lever.co/testco/remote-1',
                work_arrangement='remote',
            )
        ]
        upsert_jobs(self.source, scraped)
        job = Job.objects.get(external_id='lever:remote-1')
        self.assertEqual(job.work_arrangement, 'remote')


class ScrapeSourceFailureTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name='Bad Source',
            url='https://example.com/jobs',
            source_type='website',
        )

    def test_failed_scrape_writes_log(self):
        with self.assertRaises(ValueError):
            scrape_source(self.source)

        log = JobScrapingLog.objects.get(source=self.source)
        self.assertEqual(log.status, 'failed')
        self.assertTrue(log.error_message)
