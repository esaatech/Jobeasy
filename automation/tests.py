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


class MatchedTaskModelTests(TestCase):
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

    def test_create_matched_task(self):
        from automation.models import MatchedTask

        task = MatchedTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )
        self.assertEqual(task.status, MatchedTask.STATUS_MATCHED)
        self.assertEqual(task.application_url, self.job.application_url)

    def test_unique_user_job(self):
        from automation.models import MatchedTask
        from django.db import IntegrityError

        MatchedTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )
        with self.assertRaises(IntegrityError):
            MatchedTask.objects.create(
                user=self.user,
                job=self.job,
                application_url=self.job.application_url,
            )

    def test_mark_applied_and_skipped(self):
        from automation.models import MatchedTask

        task = MatchedTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )
        task.mark_applied(notes='Submitted via Lever')
        task.refresh_from_db()
        self.assertEqual(task.status, MatchedTask.STATUS_APPLIED)
        self.assertIsNotNone(task.applied_at)
        self.assertIn('Submitted', task.operator_notes)

        task.mark_skipped(reason='job_closed', notes='404 on URL')
        task.refresh_from_db()
        self.assertEqual(task.status, MatchedTask.STATUS_SKIPPED)
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
        from automation.models import MatchedTask
        from automation.services.job_matcher import match_jobs_for_profile

        self.profile.max_applications_per_day = 1
        self.profile.save(update_fields=['max_applications_per_day'])

        result = match_jobs_for_profile(self.profile)
        self.assertEqual(result.created, 1)
        self.assertEqual(MatchedTask.objects.filter(user=self.user).count(), 1)

        again = match_jobs_for_profile(self.profile)
        self.assertTrue(again.skipped_cap)
        self.assertEqual(again.created, 0)

    def test_dry_run_does_not_create(self):
        from automation.models import MatchedTask
        from automation.services.job_matcher import run_match_cycle

        cycle = run_match_cycle(user_id=self.user.id, dry_run=True)
        self.assertGreaterEqual(cycle.tasks_created, 1)
        self.assertEqual(MatchedTask.objects.count(), 0)

    def test_skips_existing_job_application(self):
        from automation.models import MatchedTask
        from automation.services.job_matcher import match_jobs_for_profile
        from job_service.models import JobApplication

        JobApplication.objects.create(user=self.user, job=self.remote_job, status='applied')
        result = match_jobs_for_profile(self.profile)
        self.assertEqual(
            MatchedTask.objects.filter(user=self.user, job=self.remote_job).count(),
            0,
        )
        self.assertEqual(result.created, 0)


class MatchedTaskAdminActionTests(TestCase):
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
        from automation.models import MatchedTask

        self.task = MatchedTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
            status=MatchedTask.STATUS_READY,
        )

    def test_complete_matched_task_creates_job_application(self):
        from automation.models import MatchedTask
        from automation.services.apply_tasks import complete_matched_task
        from job_service.models import JobApplication

        complete_matched_task(self.task, notes='Done')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, MatchedTask.STATUS_APPLIED)
        self.assertTrue(
            JobApplication.objects.filter(user=self.user, job=self.job).exists()
        )

    def test_admin_mark_applied_action(self):
        from automation.models import MatchedTask
        from job_service.models import JobApplication

        url = reverse('admin:automation_matchedtask_changelist')
        response = self.client.post(
            url + '?queue=open',
            {
                'action': 'mark_as_applied',
                '_selected_action': [str(self.task.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, MatchedTask.STATUS_APPLIED)
        self.assertTrue(
            JobApplication.objects.filter(user=self.user, job=self.job).exists()
        )

    def test_list_shows_open_job_and_resume(self):
        from automation.models import MatchedTask
        from resume_builder.models import Resume

        resume = Resume.objects.create(
            user=self.user,
            name='Base',
            template_id='modern',
            personal_info={'full_name': 'Candidate'},
        )
        self.task.source_resume = resume
        self.task.save(update_fields=['source_resume'])

        url = reverse('admin:automation_matchedtask_changelist')
        response = self.client.get(url + '?queue=open')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Open job')
        self.assertContains(response, 'Open resume')


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
        self.assertContains(response, 'Optimize Resume')
        self.assertContains(response, 'Remember my preference')

    def test_match_post_creates_tasks_once(self):
        from automation.models import MatchedTask
        from unittest.mock import patch

        url = reverse('admin:automation_ultimateautomationprofile_match')
        with patch('automation.admin.build_packets_for_tasks') as mock_packets:
            mock_packets.return_value = []
            response = self.client.post(
                url,
                {'run_match': '1', 'user_ids': [str(self.user.pk)]},
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(MatchedTask.objects.filter(user=self.user).count(), 1)
            self.assertTrue(mock_packets.called)

            # Second run must not duplicate.
            mock_packets.reset_mock()
            self.client.post(url, {'run_match': '1', 'user_ids': [str(self.user.pk)]})
            self.assertEqual(MatchedTask.objects.filter(user=self.user).count(), 1)
            mock_packets.assert_not_called()

    def test_remember_prefs_persists_for_staff(self):
        from automation.models import StaffMatchRunPreferences
        from unittest.mock import patch

        url = reverse('admin:automation_ultimateautomationprofile_match')
        with patch('automation.admin.build_packets_for_tasks') as mock_packets:
            mock_packets.return_value = []
            # Create matched rows; fit builder mocked (always invoked on new tasks).
            self.client.post(
                url,
                {'run_match': '1', 'user_ids': [str(self.user.pk)]},
                follow=True,
            )
            self.assertTrue(mock_packets.called)

            mock_packets.reset_mock()
            self.client.post(
                url,
                {
                    'run_match': '1',
                    'user_ids': [str(self.user.pk)],
                    'optimize_resume': '1',
                    'generate_cover_letter': '1',
                    'remember_prefs': '1',
                },
                follow=True,
            )
            mock_packets.assert_not_called()  # no new MatchedTasks

        prefs = StaffMatchRunPreferences.objects.get(user=self.admin)
        self.assertTrue(prefs.optimize_resume)
        self.assertTrue(prefs.generate_cover_letter)
        self.assertFalse(prefs.generate_why_should_hire)

        response = self.client.get(url)
        self.assertContains(response, 'id="dlg-optimize-resume"')
        self.assertRegex(
            response.content.decode(),
            r'id="dlg-optimize-resume"[^>]*checked',
        )

    def test_profiles_changelist_has_match_link(self):
        url = reverse('admin:automation_ultimateautomationprofile_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Match Ultimate users')
        self.assertContains(
            response,
            reverse('admin:automation_ultimateautomationprofile_match'),
        )


class ApplicationBuilderTests(TestCase):
    def setUp(self):
        from job_service.models import Job, JobSource
        from resume_builder.models import Resume

        self.user = User.objects.create_user(username='packetuser', password='pass12345')
        self.resume = Resume.objects.create(
            user=self.user,
            name='Base Resume',
            template_id='modern',
            personal_info={'full_name': 'Packet User'},
            experience=[{'title': 'Engineer', 'company': 'Acme'}],
            skills={'languages': ['Python']},
        )
        self.profile = UltimateAutomationProfile.objects.create(
            user=self.user,
            primary_titles=['Backend Engineer'],
            default_resume=self.resume,
            auto_apply_enabled=True,
            setup_completed=True,
            title_family_confirmed=True,
        )
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
            description='Build APIs with Python',
            application_url='https://jobs.lever.co/board/p',
            source=self.source,
            external_id='lever:p',
        )
        from automation.models import MatchedTask

        self.task = MatchedTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
        )

    def test_fit_always_runs_without_generators(self):
        from automation.models import MatchedTask
        from automation.services.application_builder import build_packet_for_matched_task

        with patch(
            'automation.services.application_builder.run_dashboard_job_fit_evaluation'
        ) as mock_fit:
            mock_fit.return_value = {
                'success': True,
                'auto_proceed': True,
                'tier': 'green',
                'overall_score': 82,
                'recommendation': 'Strong Fit',
                'summary': {'overall_score': 82, 'recommendation': 'Strong Fit'},
            }
            result = build_packet_for_matched_task(self.task)
        self.assertEqual(result.message, 'ready')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, MatchedTask.STATUS_READY)
        self.assertEqual(self.task.fit_score, 82)
        self.assertIsNone(self.task.optimized_resume_id)
        self.assertIsNone(self.task.cover_letter_id)
        mock_fit.assert_called_once()

    @patch('automation.services.application_builder.run_dashboard_job_fit_evaluation')
    @patch('automation.services.application_builder._optimize_resume_for_job_application')
    def test_green_optimize_checked_sets_ready(self, mock_optimize, mock_fit):
        from automation.models import MatchedTask
        from automation.services.application_builder import build_packet_for_matched_task
        from resume_builder.models import Resume

        optimized = Resume.objects.create(
            user=self.user,
            name='Optimized',
            template_id='modern',
            is_optimized=True,
        )
        mock_fit.return_value = {
            'success': True,
            'auto_proceed': True,
            'tier': 'green',
            'overall_score': 88,
            'recommendation': 'Strong Fit',
            'summary': {'overall_score': 88, 'recommendation': 'Strong Fit'},
            'evaluation_id': None,
        }
        mock_optimize.return_value = (optimized, None, {})

        result = build_packet_for_matched_task(self.task, optimize_resume=True)
        self.task.refresh_from_db()
        self.assertEqual(result.status, MatchedTask.STATUS_READY)
        self.assertEqual(self.task.status, MatchedTask.STATUS_READY)
        self.assertEqual(self.task.optimized_resume_id, optimized.pk)
        mock_optimize.assert_called_once()

    @patch('automation.services.application_builder.run_dashboard_job_fit_evaluation')
    @patch('automation.services.application_builder._optimize_resume_for_job_application')
    @patch('automation.services.application_builder.generate_why_should_i_apply')
    def test_green_optimize_unchecked_skips_optimize(self, mock_why, mock_optimize, mock_fit):
        from automation.models import MatchedTask
        from automation.services.application_builder import build_packet_for_matched_task

        mock_fit.return_value = {
            'success': True,
            'auto_proceed': True,
            'tier': 'green',
            'overall_score': 90,
            'recommendation': 'Strong Fit',
            'summary': {'overall_score': 90, 'recommendation': 'Strong Fit'},
        }
        mock_why.return_value = {
            'success': True,
            'answer_text': 'Strong technical fit.',
            'model_id': 'test-model',
        }

        result = build_packet_for_matched_task(
            self.task,
            generate_cover_letter=False,
            optimize_resume=False,
            generate_why_should_hire=True,
        )
        mock_optimize.assert_not_called()
        self.task.refresh_from_db()
        self.assertEqual(result.status, MatchedTask.STATUS_READY)
        self.assertIsNone(self.task.optimized_resume_id)
        self.assertIsNotNone(self.task.why_should_i_apply_answer_id)

    @patch('automation.services.application_builder.run_dashboard_job_fit_evaluation')
    @patch('automation.services.application_builder._optimize_resume_for_job_application')
    @patch('automation.services.application_builder.generate_cover_letter_from_raw_text')
    @patch('automation.services.application_builder.generate_why_should_i_apply')
    def test_yellow_fit_pauses_without_generators(
        self, mock_why, mock_cl, mock_optimize, mock_fit
    ):
        from automation.models import MatchedTask
        from automation.services.application_builder import build_packet_for_matched_task

        mock_fit.return_value = {
            'success': True,
            'auto_proceed': False,
            'tier': 'yellow',
            'overall_score': 55,
            'recommendation': 'Moderate Fit',
            'summary': {'overall_score': 55, 'recommendation': 'Moderate Fit'},
            'evaluation_id': None,
        }

        result = build_packet_for_matched_task(
            self.task,
            optimize_resume=True,
            generate_cover_letter=True,
            generate_why_should_hire=True,
        )
        self.task.refresh_from_db()
        self.assertEqual(result.status, MatchedTask.STATUS_FIT_PAUSED)
        self.assertEqual(self.task.status, MatchedTask.STATUS_FIT_PAUSED)
        self.assertEqual(self.task.fit_score, 55)
        self.assertIsNone(self.task.optimized_resume_id)
        self.assertIsNone(self.task.cover_letter_id)
        mock_optimize.assert_not_called()
        mock_cl.assert_not_called()
        mock_why.assert_not_called()

    @patch('automation.services.application_builder.generate_cover_letter_from_raw_text')
    def test_ondemand_cover_letter_allowed_when_yellow(self, mock_cl):
        from automation.models import MatchedTask
        from automation.services.application_builder import (
            generate_cover_letter_for_matched_task,
        )

        self.task.status = MatchedTask.STATUS_FIT_PAUSED
        self.task.fit_tier = 'yellow'
        self.task.fit_score = 55
        self.task.source_resume = self.resume
        self.task.save()
        mock_cl.return_value = {
            'success': True,
            'cover_letter': 'Dear hiring manager…',
            'title': 'CL',
        }
        result = generate_cover_letter_for_matched_task(self.task)
        self.task.refresh_from_db()
        self.assertTrue(result.success)
        self.assertIsNotNone(self.task.cover_letter_id)
        self.assertEqual(self.task.status, MatchedTask.STATUS_FIT_PAUSED)


class MatchedTaskOpsViewTests(TestCase):
    def setUp(self):
        from job_service.models import Job, JobSource
        from resume_builder.models import Resume

        from automation.models import MatchedTask

        self.admin = User.objects.create_superuser(
            username='opsdetail',
            email='opsdetail@example.com',
            password='pass12345',
        )
        self.client = Client()
        self.client.force_login(self.admin)
        self.user = User.objects.create_user(username='cand', password='pass12345')
        self.resume = Resume.objects.create(
            user=self.user,
            name='Base',
            template_id='modern',
            personal_info={'full_name': 'Cand'},
        )
        UltimateAutomationProfile.objects.create(
            user=self.user,
            default_resume=self.resume,
        )
        source = JobSource.objects.create(
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
            description='Build APIs',
            application_url='https://jobs.lever.co/board/ops',
            source=source,
            external_id='lever:ops',
        )
        self.task = MatchedTask.objects.create(
            user=self.user,
            job=self.job,
            application_url=self.job.application_url,
            status=MatchedTask.STATUS_READY,
            fit_score=88,
            fit_tier='green',
            fit_summary={'overall_score': 88, 'recommendation': 'Strong Fit'},
            source_resume=self.resume,
        )

    def test_ops_page_renders(self):
        url = reverse('automation:matched_task_ops', args=[self.task.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backend Engineer')
        self.assertContains(response, 'Job fit evaluation')
        self.assertContains(response, 'Open job')
        self.assertContains(response, 'Optimize resume')
        self.assertContains(response, 'Generate cover letter')

    @patch('automation.services.application_builder._optimize_resume_for_job_application')
    def test_ops_optimize_post(self, mock_optimize):
        from resume_builder.models import Resume

        optimized = Resume.objects.create(
            user=self.user,
            name='Opt',
            template_id='modern',
            is_optimized=True,
        )
        mock_optimize.return_value = (optimized, None, {})
        url = reverse('automation:matched_task_ops', args=[self.task.pk])
        response = self.client.post(url, {'action': 'optimize_resume'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.optimized_resume_id, optimized.pk)

    def test_admin_list_has_ops_open_link(self):
        url = reverse('admin:automation_matchedtask_changelist')
        response = self.client.get(url + '?queue=open')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('automation:matched_task_ops', args=[self.task.pk]))
        self.assertContains(response, 'target="_blank"')
