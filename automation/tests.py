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


class JobMatcherTests(TestCase):
    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        from job_service.models import Job, JobSource
        from subscriptions.models import PlanDuration, SubscriptionPlan, UserSubscription

        self.user = User.objects.create_user(username='matcher', password='pass12345')
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name='Ultimate',
            defaults={
                'description': 'Ultimate',
                'has_full_access': True,
                'is_active': True,
            },
        )
        duration, _ = PlanDuration.objects.get_or_create(
            plan=plan,
            duration_type='MONTHLY',
            defaults={'price': 40},
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            plan_duration=duration,
            status='ACTIVE',
            start_date=timezone.now() - timedelta(days=1),
        )
        self.profile = UltimateAutomationProfile.objects.create(
            user=self.user,
            primary_titles=['Backend Engineer'],
            related_titles=['Software Engineer'],
            exclude_titles=['Manager'],
            work_arrangements=['remote', 'hybrid'],
            preferred_countries=[{'name': 'Canada', 'cca2': 'CA', 'states': ['Ontario']}],
            city='Toronto',
            auto_apply_enabled=True,
            setup_completed=True,
            title_family_confirmed=True,
            max_applications_per_day=5,
        )
        self.source = JobSource.objects.create(
            name='Board',
            url='https://jobs.lever.co/board',
            source_type='api',
        )
        self.remote_job = Job.objects.create(
            title='Backend Engineer',
            company='Co',
            location='Toronto, ON (Remote)',
            job_type='full-time',
            work_arrangement='remote',
            description='Build APIs',
            application_url='https://jobs.lever.co/board/1',
            source=self.source,
            external_id='lever:1',
            is_active=True,
        )
        self.onsite_job = Job.objects.create(
            title='Backend Engineer',
            company='Co',
            location='Toronto, ON',
            job_type='full-time',
            work_arrangement='onsite',
            description='Office role',
            application_url='https://jobs.lever.co/board/2',
            source=self.source,
            external_id='lever:2',
            is_active=True,
        )
        self.wrong_title = Job.objects.create(
            title='Engineering Manager',
            company='Co',
            location='Remote',
            job_type='full-time',
            work_arrangement='remote',
            description='Lead team',
            application_url='https://jobs.lever.co/board/3',
            source=self.source,
            external_id='lever:3',
            is_active=True,
        )

    def test_title_and_work_arrangement_filters(self):
        from automation.services.job_matcher import job_matches_user, title_matches, work_arrangement_matches

        self.assertTrue(title_matches(self.remote_job, self.profile))
        self.assertFalse(title_matches(self.wrong_title, self.profile))
        self.assertTrue(work_arrangement_matches(self.remote_job, self.profile))
        self.assertFalse(work_arrangement_matches(self.onsite_job, self.profile))
        self.assertTrue(job_matches_user(self.remote_job, self.profile))
        self.assertFalse(job_matches_user(self.onsite_job, self.profile))
        self.assertFalse(job_matches_user(self.wrong_title, self.profile))

    def test_title_respects_seniority_levels(self):
        from automation.services.job_matcher import title_matches, title_target_matches_job
        from job_service.models import Job

        self.assertTrue(title_target_matches_job('Software Engineer', 'Software Engineer, Platform'))
        self.assertFalse(title_target_matches_job('Software Engineer', 'Staff Software Engineer'))
        self.assertFalse(title_target_matches_job('Software Engineer', 'Senior Software Engineer'))
        self.assertTrue(
            title_target_matches_job('Senior Software Engineer', 'Senior Software Engineer, Backend')
        )
        self.assertFalse(
            title_target_matches_job('Senior Software Engineer', 'Staff+ Software Engineer')
        )

        staff_job = Job.objects.create(
            title='Staff Software Engineer, AI Reliability',
            company='Co',
            location='Remote',
            job_type='full-time',
            work_arrangement='remote',
            description='x',
            application_url='https://jobs.lever.co/board/staff',
            source=self.source,
            external_id='lever:staff',
        )
        self.assertFalse(title_matches(staff_job, self.profile))

        self.profile.related_titles = list(self.profile.related_titles or []) + [
            'Senior Backend Engineer',
        ]
        self.profile.save(update_fields=['related_titles'])
        senior_job = Job.objects.create(
            title='Senior Backend Engineer',
            company='Co',
            location='Toronto (Remote)',
            job_type='full-time',
            work_arrangement='remote',
            description='x',
            application_url='https://jobs.lever.co/board/senior',
            source=self.source,
            external_id='lever:senior',
        )
        self.assertTrue(title_matches(senior_job, self.profile))

    def test_location_remote_wrong_region(self):
        from automation.services.job_matcher import location_matches
        from job_service.models import Job

        job = Job.objects.create(
            title='Backend Engineer',
            company='Co',
            location='Remote - United States',
            job_type='full-time',
            work_arrangement='remote',
            description='US remote',
            application_url='https://jobs.lever.co/board/us',
            source=self.source,
            external_id='lever:us',
        )
        self.assertFalse(location_matches(job, self.profile))

    def test_match_creates_tasks_and_respects_cap(self):
        from automation.models import ApplyTask
        from automation.services.job_matcher import match_jobs_for_profile

        self.profile.max_applications_per_day = 1
        self.profile.save(update_fields=['max_applications_per_day'])

        result = match_jobs_for_profile(self.profile)
        self.assertEqual(result.created, 1)
        self.assertEqual(ApplyTask.objects.filter(user=self.user).count(), 1)

        again = match_jobs_for_profile(self.profile)
        self.assertTrue(again.skipped_cap)
        self.assertEqual(again.created, 0)

    def test_dry_run_does_not_create(self):
        from automation.models import ApplyTask
        from automation.services.job_matcher import run_match_cycle

        cycle = run_match_cycle(user_id=self.user.id, dry_run=True)
        self.assertGreaterEqual(cycle.tasks_created, 1)
        self.assertEqual(ApplyTask.objects.count(), 0)

    def test_skips_existing_job_application(self):
        from automation.models import ApplyTask
        from automation.services.job_matcher import match_jobs_for_profile
        from job_service.models import JobApplication

        JobApplication.objects.create(user=self.user, job=self.remote_job, status='applied')
        result = match_jobs_for_profile(self.profile)
        self.assertEqual(
            ApplyTask.objects.filter(user=self.user, job=self.remote_job).count(),
            0,
        )
        self.assertEqual(result.created, 0)


class ApplyTaskAdminActionTests(TestCase):
    def setUp(self):
        from job_service.models import Job, JobSource

        self.admin = User.objects.create_superuser(
            username='ops',
            email='ops@example.com',
            password='pass12345',
        )
        self.user = User.objects.create_user(username='candidate', password='pass12345')
        UltimateAutomationProfile.objects.create(user=self.user)
        self.client = Client()
        self.client.force_login(self.admin)
        self.source = JobSource.objects.create(
            name='Board',
            url='https://jobs.lever.co/board',
            source_type='api',
        )
        self.job = Job.objects.create(
            title='Backend Engineer',
            company='Co',
            location='Remote',
            job_type='full-time',
            work_arrangement='remote',
            description='Build',
            application_url='https://jobs.lever.co/board/x',
            source=self.source,
            external_id='lever:x',
        )
        from automation.models import ApplyTask

        self.task = ApplyTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )

    def test_complete_apply_task_creates_job_application(self):
        from automation.models import ApplyTask
        from automation.services.apply_tasks import complete_apply_task
        from job_service.models import JobApplication

        complete_apply_task(self.task, notes='Done')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, ApplyTask.STATUS_APPLIED)
        self.assertTrue(
            JobApplication.objects.filter(user=self.user, job=self.job).exists()
        )

    def test_admin_mark_applied_action(self):
        from automation.models import ApplyTask
        from job_service.models import JobApplication

        url = reverse('admin:automation_applytask_changelist')
        response = self.client.post(
            url + '?status__exact=queued',
            {
                'action': 'mark_as_applied',
                '_selected_action': [str(self.task.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, ApplyTask.STATUS_APPLIED)
        self.assertTrue(
            JobApplication.objects.filter(user=self.user, job=self.job).exists()
        )


class MatchUltimateUsersAdminTests(TestCase):
    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        from job_service.models import Job, JobSource
        from subscriptions.models import PlanDuration, SubscriptionPlan, UserSubscription

        self.admin = User.objects.create_superuser(
            username='matchadmin',
            email='matchadmin@example.com',
            password='pass12345',
        )
        self.client = Client()
        self.client.force_login(self.admin)

        self.user = User.objects.create_user(username='ultmatch', password='pass12345')
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name='Ultimate',
            defaults={
                'description': 'Ultimate',
                'has_full_access': True,
                'is_active': True,
            },
        )
        duration, _ = PlanDuration.objects.get_or_create(
            plan=plan,
            duration_type='MONTHLY',
            defaults={'price': 40},
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            plan_duration=duration,
            status='ACTIVE',
            start_date=timezone.now() - timedelta(days=1),
        )
        UltimateAutomationProfile.objects.create(
            user=self.user,
            primary_titles=['Backend Engineer'],
            work_arrangements=['remote'],
            preferred_countries=[{'name': 'Canada', 'cca2': 'CA', 'states': []}],
            auto_apply_enabled=True,
            setup_completed=True,
            title_family_confirmed=True,
            max_applications_per_day=10,
        )
        self.source = JobSource.objects.create(
            name='Board',
            url='https://jobs.lever.co/board',
            source_type='api',
        )
        Job.objects.create(
            title='Backend Engineer',
            company='Co',
            location='Remote',
            job_type='full-time',
            work_arrangement='remote',
            description='Build',
            application_url='https://jobs.lever.co/board/m',
            source=self.source,
            external_id='lever:m',
            is_active=True,
        )

    def test_match_page_lists_ultimate_user(self):
        url = reverse('admin:automation_ultimateautomationprofile_match')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ultmatch')
        self.assertContains(response, 'Select all')
        self.assertContains(response, 'Match selected users')

    def test_match_post_creates_tasks_once(self):
        from automation.models import ApplyTask

        url = reverse('admin:automation_ultimateautomationprofile_match')
        response = self.client.post(
            url,
            {'run_match': '1', 'user_ids': [str(self.user.pk)]},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ApplyTask.objects.filter(user=self.user).count(), 1)

        # Second run must not duplicate.
        self.client.post(url, {'run_match': '1', 'user_ids': [str(self.user.pk)]})
        self.assertEqual(ApplyTask.objects.filter(user=self.user).count(), 1)

    def test_profiles_changelist_has_match_link(self):
        url = reverse('admin:automation_ultimateautomationprofile_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Match Ultimate users')
        self.assertContains(
            response,
            reverse('admin:automation_ultimateautomationprofile_match'),
        )
