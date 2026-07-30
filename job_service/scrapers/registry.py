from __future__ import annotations

from job_service.models import JobSource
from job_service.scrapers.base import BaseScraper
from job_service.scrapers.greenhouse import GreenhouseScraper
from job_service.scrapers.lever import LeverScraper


def get_scraper(source: JobSource, *, fetch_details: bool = True) -> BaseScraper:
    """
    Resolve the scraper implementation for a JobSource.

    Detection is based on the board URL hostname. Add explicit scraper mapping
    here when new source types are introduced.
    """
    url = (source.url or '').lower()

    if 'lever.co' in url:
        return LeverScraper(source, fetch_details=fetch_details)

    if 'greenhouse.io' in url:
        return GreenhouseScraper(source, fetch_details=fetch_details)

    if source.source_type == 'api':
        raise ValueError(
            f'Unsupported API job source URL for "{source.name}": {source.url}. '
            'Supported API boards: Greenhouse (boards.greenhouse.io) and Lever (jobs.lever.co).'
        )

    if source.source_type == 'rss':
        raise NotImplementedError(f'RSS scraping is not implemented yet for "{source.name}".')

    raise ValueError(
        f'No scraper available for source "{source.name}" ({source.source_type}). '
        f'URL: {source.url}'
    )
