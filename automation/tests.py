from django.contrib.auth import get_user_model
from django.test import TestCase

from automation.models import UltimateAutomationProfile

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
