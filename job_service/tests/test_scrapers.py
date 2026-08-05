from unittest.mock import patch

from django.test import SimpleTestCase

from job_service.scrapers.ashby import AshbyScraper, parse_board_name
from job_service.scrapers.greenhouse import GreenhouseScraper, parse_board_token, strip_html
from job_service.scrapers.lever import LeverScraper, parse_site_name
from job_service.scrapers.registry import get_scraper
from job_service.scrapers.workplace import (
    classify_ashby,
    classify_from_text,
)


class WorkplaceClassifierTests(SimpleTestCase):
    def test_remote_and_hybrid_from_location(self):
        self.assertEqual(classify_from_text('Remote'), 'remote')
        self.assertEqual(classify_from_text('New York, NY (Hybrid)'), 'hybrid')
        self.assertEqual(classify_from_text('Toronto, ON'), 'onsite')
        self.assertEqual(classify_from_text('Unspecified'), 'unknown')

    def test_ashby_prefers_workplace_type(self):
        self.assertEqual(
            classify_ashby(
                is_remote=True,
                workplace_type='Hybrid',
                location='San Francisco (Remote)',
            ),
            'hybrid',
        )
        self.assertEqual(
            classify_ashby(is_remote=True, workplace_type=None, location='Remote'),
            'remote',
        )
        self.assertEqual(
            classify_ashby(is_remote=False, workplace_type='Onsite', location='NYC'),
            'onsite',
        )


class GreenhouseParserTests(SimpleTestCase):
    def test_parse_board_token(self):
        self.assertEqual(parse_board_token('https://boards.greenhouse.io/stripe'), 'stripe')

    def test_strip_html(self):
        self.assertIn('Hello', strip_html('<p>Hello <b>world</b></p>'))
        self.assertIn('world', strip_html('<p>Hello <b>world</b></p>'))


class LeverParserTests(SimpleTestCase):
    def test_parse_site_name(self):
        self.assertEqual(parse_site_name('https://jobs.lever.co/netflix'), 'netflix')


class AshbyParserTests(SimpleTestCase):
    def test_parse_board_name(self):
        self.assertEqual(parse_board_name('https://jobs.ashbyhq.com/notion'), 'notion')
        self.assertEqual(
            parse_board_name('https://jobs.ashbyhq.com/notion/05e14247-17c4'),
            'notion',
        )


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

    def test_get_ashby_scraper(self):
        source = type('JobSource', (), {
            'name': 'Notion',
            'url': 'https://jobs.ashbyhq.com/notion',
            'source_type': 'api',
        })()
        scraper = get_scraper(source)
        self.assertIsInstance(scraper, AshbyScraper)


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
        self.assertEqual(jobs[0].work_arrangement, 'remote')


class AshbyScraperFetchTests(SimpleTestCase):
    @patch('job_service.scrapers.ashby.fetch_json')
    def test_fetch_normalizes_jobs(self, mock_fetch_json):
        mock_fetch_json.return_value = {
            'jobs': [
                {
                    'id': '05e14247-17c4-4e98-9a13-53828a4e2f13',
                    'title': 'Backend Engineer',
                    'department': 'Engineering',
                    'team': 'Platform',
                    'employmentType': 'FullTime',
                    'location': 'San Francisco',
                    'isListed': True,
                    'isRemote': True,
                    'workplaceType': 'Hybrid',
                    'jobUrl': 'https://jobs.ashbyhq.com/notion/05e14247',
                    'descriptionPlain': 'Build APIs.',
                    'publishedAt': '2026-04-02T21:00:55.755+00:00',
                }
            ]
        }
        source = type('JobSource', (), {
            'name': 'Notion',
            'url': 'https://jobs.ashbyhq.com/notion',
            'source_type': 'api',
        })()
        jobs = AshbyScraper(source).fetch()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].external_id, 'ashby:05e14247-17c4-4e98-9a13-53828a4e2f13')
        self.assertEqual(jobs[0].title, 'Backend Engineer')
        self.assertIn('Remote', jobs[0].location)
        self.assertEqual(jobs[0].job_type, 'full-time')
        self.assertEqual(jobs[0].work_arrangement, 'hybrid')
