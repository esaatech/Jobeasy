from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from job_service.scrapers.base import BaseScraper, ScrapedJob
from job_service.scrapers.http import fetch_json

GREENHOUSE_API_BASE = 'https://boards-api.greenhouse.io/v1/boards'
JOB_TYPE_MAP = {
    'full-time': 'full-time',
    'full time': 'full-time',
    'part-time': 'part-time',
    'part time': 'part-time',
    'contract': 'contract',
    'intern': 'internship',
    'internship': 'internship',
    'temporary': 'contract',
    'freelance': 'freelance',
}


def parse_board_token(url: str) -> str:
    """
    Extract Greenhouse board token from URLs such as:
    - https://boards.greenhouse.io/stripe
    - https://job-boards.greenhouse.io/airbnb
  """
    path = urlparse(url).path.strip('/')
    if not path:
        raise ValueError(f'Could not parse Greenhouse board token from URL: {url}')
    return path.split('/')[-1]


def strip_html(value: str) -> str:
    if not value:
        return ''
    text = BeautifulSoup(value, 'html.parser').get_text('\n')
    return unescape(re.sub(r'\n{3,}', '\n\n', text)).strip()


def normalize_job_type(raw: str | None) -> str:
    if not raw:
        return 'full-time'
    normalized = JOB_TYPE_MAP.get(raw.strip().lower())
    return normalized or 'full-time'


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


class GreenhouseScraper(BaseScraper):
    """Scraper for public Greenhouse job boards."""

    def fetch(self) -> list[ScrapedJob]:
        board_token = parse_board_token(self.source.url)
        list_url = f'{GREENHOUSE_API_BASE}/{board_token}/jobs?content=true'
        payload = fetch_json(list_url)
        jobs = payload.get('jobs', []) if isinstance(payload, dict) else []
        company = self.default_company()
        scraped: list[ScrapedJob] = []

        for job in jobs:
            job_id = job.get('id')
            if job_id is None:
                continue

            title = (job.get('title') or '').strip()
            if not title:
                continue

            location_name = ''
            location = job.get('location') or {}
            if isinstance(location, dict):
                location_name = (location.get('name') or '').strip()
            elif isinstance(location, str):
                location_name = location.strip()

            application_url = (job.get('absolute_url') or '').strip()
            if not application_url:
                continue

            description = strip_html(job.get('content') or '')
            if self.fetch_details and not description:
                detail_url = f'{GREENHOUSE_API_BASE}/{board_token}/jobs/{job_id}'
                detail = fetch_json(detail_url)
                description = strip_html(detail.get('content') or '')

            if not description:
                description = title

            metadata = job.get('metadata') or []
            tags = []
            if isinstance(metadata, list):
                tags = [str(item) for item in metadata if item]

            departments = job.get('departments') or []
            if isinstance(departments, list):
                tags.extend(
                    dept.get('name', '')
                    for dept in departments
                    if isinstance(dept, dict) and dept.get('name')
                )

            scraped.append(
                ScrapedJob(
                    external_id=f'greenhouse:{job_id}',
                    title=title[:200],
                    company=company[:200],
                    location=(location_name or 'Unspecified')[:200],
                    job_type=normalize_job_type(job.get('employment_type')),
                    description=description,
                    application_url=application_url[:500],
                    tags=tags[:20],
                    posted_date=parse_datetime(job.get('updated_at') or job.get('first_published')),
                    is_active=True,
                )
            )

        return scraped
