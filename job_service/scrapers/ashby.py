from __future__ import annotations

from datetime import datetime
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from job_service.scrapers.base import BaseScraper, ScrapedJob
from job_service.scrapers.greenhouse import normalize_job_type
from job_service.scrapers.http import fetch_json

ASHBY_API_BASE = 'https://api.ashbyhq.com/posting-api/job-board'


def parse_board_name(url: str) -> str:
    """
    Extract Ashby board name from URLs such as:
    - https://jobs.ashbyhq.com/notion
    - https://jobs.ashbyhq.com/notion/05e14247-...
    """
    path = urlparse(url).path.strip('/')
    if not path:
        raise ValueError(f'Could not parse Ashby board name from URL: {url}')
    return path.split('/')[0]


def strip_html(value: str) -> str:
    if not value:
        return ''
    soup = BeautifulSoup(value, 'html.parser')
    return unescape(soup.get_text('\n')).strip()


def parse_ashby_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def resolve_location(job: dict) -> str:
    location = (job.get('location') or '').strip()
    if job.get('isRemote') and location:
        if 'remote' not in location.lower():
            return f'{location} (Remote)'
        return location
    if job.get('isRemote'):
        return 'Remote'
    return location or 'Unspecified'


class AshbyScraper(BaseScraper):
    """Scraper for public Ashby job boards (single JSON request)."""

    def fetch(self) -> list[ScrapedJob]:
        board = parse_board_name(self.source.url)
        api_url = f'{ASHBY_API_BASE}/{board}'
        payload = fetch_json(api_url)
        if not isinstance(payload, dict):
            raise RuntimeError(f'Unexpected Ashby API response for {api_url}')

        jobs = payload.get('jobs') or []
        if not isinstance(jobs, list):
            raise RuntimeError(f'Unexpected Ashby jobs payload for {api_url}')

        company = self.default_company()
        scraped: list[ScrapedJob] = []

        for job in jobs:
            job_id = job.get('id')
            if not job_id:
                continue
            if job.get('isListed') is False:
                continue

            title = (job.get('title') or '').strip()
            if not title:
                continue

            application_url = (job.get('jobUrl') or job.get('applyUrl') or '').strip()
            if not application_url:
                continue

            description = (
                (job.get('descriptionPlain') or '').strip()
                or strip_html(job.get('descriptionHtml') or '')
            )
            if not description:
                description = title

            tags = [
                value
                for value in (
                    job.get('department'),
                    job.get('team'),
                    job.get('employmentType'),
                    job.get('workplaceType'),
                )
                if value
            ]

            scraped.append(
                ScrapedJob(
                    external_id=f'ashby:{job_id}',
                    title=title[:200],
                    company=company[:200],
                    location=resolve_location(job)[:200],
                    job_type=normalize_job_type(job.get('employmentType')),
                    description=description,
                    application_url=application_url[:500],
                    tags=tags[:20],
                    posted_date=parse_ashby_datetime(job.get('publishedAt')),
                    is_active=True,
                )
            )

        return scraped
