from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from job_service.scrapers.base import BaseScraper, ScrapedJob
from job_service.scrapers.greenhouse import normalize_job_type
from job_service.scrapers.http import fetch_json

LEVER_API_BASE = 'https://api.lever.co/v0/postings'


def parse_site_name(url: str) -> str:
    """
    Extract Lever site name from URLs such as:
    - https://jobs.lever.co/netflix
    - https://jobs.lever.co/spotify
    """
    path = urlparse(url).path.strip('/')
    if not path:
        raise ValueError(f'Could not parse Lever site name from URL: {url}')
    return path.split('/')[-1]


def strip_html(value: str) -> str:
    if not value:
        return ''
    soup = BeautifulSoup(value, 'html.parser')
    return unescape(soup.get_text('\n')).strip()


def parse_lever_timestamp(value: int | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


class LeverScraper(BaseScraper):
    """Scraper for public Lever job boards (single JSON request)."""

    def fetch(self) -> list[ScrapedJob]:
        site = parse_site_name(self.source.url)
        api_url = f'{LEVER_API_BASE}/{site}?mode=json'
        payload = fetch_json(api_url)
        if not isinstance(payload, list):
            raise RuntimeError(f'Unexpected Lever API response for {api_url}')

        company = self.default_company()
        scraped: list[ScrapedJob] = []

        for job in payload:
            job_id = job.get('id')
            if not job_id:
                continue

            title = (job.get('text') or '').strip()
            if not title:
                continue

            categories = job.get('categories') or {}
            location = (categories.get('location') or 'Unspecified').strip()
            commitment = categories.get('commitment')
            department = categories.get('department')
            team = categories.get('team')

            description = strip_html(
                job.get('descriptionPlain')
                or job.get('description')
                or ''
            )
            if not description:
                description = title

            application_url = (job.get('hostedUrl') or job.get('applyUrl') or '').strip()
            if not application_url:
                continue

            tags = [value for value in (department, team, commitment) if value]

            scraped.append(
                ScrapedJob(
                    external_id=f'lever:{job_id}',
                    title=title[:200],
                    company=company[:200],
                    location=location[:200],
                    job_type=normalize_job_type(commitment),
                    description=description,
                    application_url=application_url[:500],
                    tags=tags[:20],
                    posted_date=parse_lever_timestamp(job.get('createdAt')),
                    is_active=job.get('state', 'published') != 'closed',
                )
            )

        return scraped
