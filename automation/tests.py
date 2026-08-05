from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from automation.models import FREE_TITLE_FAMILY_AI_GENERATIONS, UltimateAutomationProfile
from resume_builder.models import Resume

User = get_user_model()


class UltimateAutomationProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ult', password='pass12345')

    def test_title_family_merges_primary_and_related(self):
        profile = UltimateAutomationProfile.objects.create(
            user=self.user,
            primary_titles=['Backend Engineer', 'Software Engineer'],
            related_titles=['Software Engineer', 'Platform Engineer'],
            exclude_titles=['Data Scientist'],
        )
        self.assertEqual(
            profile.title_family,
            ['Backend Engineer', 'Software Engineer', 'Platform Engineer'],
        )

    def test_mark_title_family_confirmed(self):
        profile = UltimateAutomationProfile.objects.create(
            user=self.user,
            primary_titles=['Backend Engineer'],
        )
        profile.mark_title_family_confirmed()
        profile.refresh_from_db()
        self.assertTrue(profile.title_family_confirmed)
        self.assertTrue(profile.setup_completed)
        self.assertIsNotNone(profile.title_family_confirmed_at)


class AutoApplySetupFunnelTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='freeuser', password='pass12345')
        self.resume = Resume.objects.create(
            user=self.user,
            name='Main CV',
            template_id='classic',
        )
        self.client.login(username='freeuser', password='pass12345')

    def test_setup_accessible_without_ultimate(self):
        response = self.client.get(reverse('automation:ultimate_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose your job titles')
        self.assertFalse(response.context['is_ultimate'])

    def test_save_draft_does_not_enable_auto_apply(self):
        response = self.client.post(
            reverse('automation:ultimate_setup'),
            {
                'primary_titles': 'Backend Engineer, Software Engineer',
                'related_titles': 'Platform Engineer',
                'exclude_titles': 'Data Scientist',
                'default_resume': self.resume.pk,
                'auto_apply_enabled': 'on',
                'search_purpose': 'career_growth',
                'preferred_countries': '[{"name":"Canada","cca2":"CA","states":["Ontario"]}]',
                'city': 'Toronto',
                'distance_miles': '50',
                'work_arrangements': '["remote","hybrid"]',
            },
        )
        self.assertRedirects(response, reverse('automation:ultimate_setup_done'))
        profile = UltimateAutomationProfile.objects.get(user=self.user)
        self.assertTrue(profile.title_family_confirmed)
        self.assertFalse(profile.auto_apply_enabled)
        self.assertEqual(profile.primary_titles, ['Backend Engineer', 'Software Engineer'])
        self.assertEqual(profile.city, 'Toronto')
        self.assertEqual(profile.work_arrangements, ['remote', 'hybrid'])
        self.assertEqual(profile.max_applications_per_day, 10)  # admin default; not user-editable
        self.assertEqual(profile.search_purpose, 'career_growth')
        self.assertEqual(profile.preferred_countries[0]['cca2'], 'CA')

    def test_setup_requires_preferences(self):
        response = self.client.post(
            reverse('automation:ultimate_setup'),
            {
                'primary_titles': 'Backend Engineer',
                'default_resume': self.resume.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose why you are looking')

    def test_done_page_shows_checkout_cta_for_free_users(self):
        UltimateAutomationProfile.objects.create(
            user=self.user,
            primary_titles=['Backend Engineer'],
            title_family_confirmed=True,
        )
        response = self.client.get(reverse('automation:ultimate_setup_done'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unlock with Ultimate')
        self.assertContains(response, 'plan=ultimate')

    @patch('automation.views.generate_title_family_from_resume')
    def test_free_user_ai_generate_limit(self, mock_generate):
        mock_generate.return_value = {
            'primary_titles': ['Backend Engineer'],
            'related_titles': ['Software Engineer'],
            'exclude_titles': ['Data Scientist'],
            'rationale': 'test',
        }
        url = reverse('automation:suggest_title_family')
        for _ in range(FREE_TITLE_FAMILY_AI_GENERATIONS):
            response = self.client.post(
                url,
                data='{"resume_id": %s}' % self.resume.pk,
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 200, response.content)

        blocked = self.client.post(
            url,
            data='{"resume_id": %s}' % self.resume.pk,
            content_type='application/json',
        )
        self.assertEqual(blocked.status_code, 403)
        profile = UltimateAutomationProfile.objects.get(user=self.user)
        self.assertEqual(profile.title_family_ai_generations, FREE_TITLE_FAMILY_AI_GENERATIONS)
        self.assertEqual(mock_generate.call_count, FREE_TITLE_FAMILY_AI_GENERATIONS)


class LocationsApiTests(TestCase):
    def test_list_countries(self):
        response = self.client.get(reverse('automation:locations_countries'))
        self.assertEqual(response.status_code, 200)
        codes = [c['code'] for c in response.json()['countries']]
        self.assertEqual(codes, ['US', 'CA', 'GB'])

    def test_us_regions_include_all_states(self):
        response = self.client.get(reverse('automation:locations_regions', args=['US']))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 'US')
        self.assertIn('California', data['regions'])
        self.assertIn('New York', data['regions'])
        self.assertGreaterEqual(len(data['regions']), 50)

    def test_ca_and_gb_regions(self):
        ca = self.client.get(reverse('automation:locations_regions', args=['CA'])).json()
        gb = self.client.get(reverse('automation:locations_regions', args=['GB'])).json()
        self.assertIn('Ontario', ca['regions'])
        self.assertIn('Quebec', ca['regions'])
        self.assertIn('England', gb['regions'])
        self.assertIn('Scotland', gb['regions'])

    def test_unknown_country_404(self):
        response = self.client.get(reverse('automation:locations_regions', args=['XX']))
        self.assertEqual(response.status_code, 404)


class ApplyTaskModelTests(TestCase):
    def setUp(self):
        from job_service.models import Job, JobSource

        self.user = User.objects.create_user(username='applicant', password='pass12345')
        self.source = JobSource.objects.create(
            name='Test Board',
            url='https://jobs.lever.co/testboard',
            source_type='api',
        )
        self.job = Job.objects.create(
            title='Backend Engineer',
            company='Test Co',
            location='Toronto',
            job_type='full-time',
            description='Build APIs',
            application_url='https://jobs.lever.co/testboard/abc',
            source=self.source,
            external_id='lever:abc',
        )

    def test_create_queued_task(self):
        from automation.models import ApplyTask

        task = ApplyTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )
        self.assertEqual(task.status, ApplyTask.STATUS_QUEUED)
        self.assertEqual(task.application_url, self.job.application_url)

    def test_unique_user_job(self):
        from automation.models import ApplyTask
        from django.db import IntegrityError

        ApplyTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )
        with self.assertRaises(IntegrityError):
            ApplyTask.objects.create(
                user=self.user,
                job=self.job,
                application_url=self.job.application_url,
            )

    def test_mark_applied_and_skipped(self):
        from automation.models import ApplyTask

        task = ApplyTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )
        task.mark_applied(notes='Submitted via Lever')
        task.refresh_from_db()
        self.assertEqual(task.status, ApplyTask.STATUS_APPLIED)
        self.assertIsNotNone(task.applied_at)
        self.assertIn('Submitted', task.operator_notes)

        task.mark_skipped(reason='job_closed', notes='404 on URL')
        task.refresh_from_db()
        self.assertEqual(task.status, ApplyTask.STATUS_SKIPPED)
        self.assertEqual(task.skip_reason, 'job_closed')
