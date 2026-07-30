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
            },
        )
        self.assertRedirects(response, reverse('automation:ultimate_setup_done'))
        profile = UltimateAutomationProfile.objects.get(user=self.user)
        self.assertTrue(profile.title_family_confirmed)
        self.assertFalse(profile.auto_apply_enabled)
        self.assertEqual(profile.primary_titles, ['Backend Engineer', 'Software Engineer'])

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
