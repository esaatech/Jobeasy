from unittest.mock import patch

from django.test import SimpleTestCase

from job_service.scrapers.greenhouse import GreenhouseScraper, parse_board_token, strip_html
from job_service.scrapers.lever import LeverScraper, parse_site_name
from job_service.scrapers.registry import get_scraper


class GreenhouseParserTests(SimpleTestCase):
    def test_parse_board_token(self):
        self.assertEqual(parse_board_token('https://boards.greenhouse.io/stripe'), 'stripe')

    def test_strip_html(self):
        self.assertIn('Hello', strip_html('<p>Hello <b>world</b></p>'))
        self.assertIn('world', strip_html('<p>Hello <b>world</b></p>'))


class LeverParserTests(SimpleTestCase):
    def test_parse_site_name(self):
        self.assertEqual(parse_site_name('https://jobs.lever.co/netflix'), 'netflix')


class RegistryTests(SimpleTestCase):
    def test_get_greenhouse_scraper(self):
        source = type('JobSource', (), {
            'name': 'Stripe',
            'url': 'https://boards.greenhouse.io/stripe',
            'source_type': 'api',
        })()
        scraper = get_scraper(source)
        self.assertIsInstance(scraper, GreenhouseScraper)

    def test_get_lever_scraper(self):
        source = type('JobSource', (), {
            'name': 'Netflix',
            'url': 'https://jobs.lever.co/netflix',
            'source_type': 'api',
        })()
        scraper = get_scraper(source)
        self.assertIsInstance(scraper, LeverScraper)


class LeverScraperFetchTests(SimpleTestCase):
    @patch('job_service.scrapers.lever.fetch_json')
    def test_fetch_normalizes_jobs(self, mock_fetch_json):
        mock_fetch_json.return_value = [
            {
                'id': 'abc-123',
                'text': 'Software Engineer',
                'hostedUrl': 'https://jobs.lever.co/example/abc-123',
                'descriptionPlain': 'Build great products.',
                'createdAt': 1_700_000_000_000,
                'categories': {
                    'location': 'Remote',
                    'commitment': 'Full-time',
                    'department': 'Engineering',
                },
                'state': 'published',
            }
        ]
        source = type('JobSource', (), {
            'name': 'Example Co',
            'url': 'https://jobs.lever.co/example',
            'source_type': 'api',
        })()
        jobs = LeverScraper(source).fetch()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].external_id, 'lever:abc-123')
        self.assertEqual(jobs[0].title, 'Software Engineer')
        self.assertEqual(jobs[0].company, 'Example Co')
        self.assertEqual(jobs[0].job_type, 'full-time')
