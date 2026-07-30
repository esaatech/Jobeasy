from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from job_service.models import Job, JobScrapingLog, JobSource
from job_service.scrapers.base import ScrapedJob
from job_service.scrapers.registry import get_scraper

logger = logging.getLogger(__name__)


@dataclass
class ScrapeCycleResult:
    sources_processed: int = 0
    sources_failed: int = 0
    jobs_found: int = 0
    jobs_added: int = 0
    jobs_updated: int = 0


def run_scrape_cycle(
    *,
    source_type: str = 'all',
    source_id: int | None = None,
    fetch_details: bool = True,
) -> ScrapeCycleResult:
    """Scrape all matching active sources and upsert jobs into the database."""
    sources = JobSource.objects.filter(is_active=True).order_by('id')

    if source_id is not None:
        sources = sources.filter(pk=source_id)
    elif source_type != 'all':
        sources = sources.filter(source_type=source_type)

    result = ScrapeCycleResult()

    for source in sources:
        result.sources_processed += 1
        try:
            added, updated, found = scrape_source(source, fetch_details=fetch_details)
            result.jobs_found += found
            result.jobs_added += added
            result.jobs_updated += updated
        except Exception:
            result.sources_failed += 1
            logger.exception('Scrape failed for source %s (%s)', source.name, source.pk)

    return result


def scrape_source(source: JobSource, *, fetch_details: bool = True) -> tuple[int, int, int]:
    """
    Scrape a single JobSource.

    Returns:
        (jobs_added, jobs_updated, jobs_found)
    """
    log = JobScrapingLog.objects.create(source=source, status='running')

    try:
        scraper = get_scraper(source, fetch_details=fetch_details)
        scraped_jobs = scraper.fetch()
        added, updated = upsert_jobs(source, scraped_jobs)

        source.last_scraped = timezone.now()
        source.save(update_fields=['last_scraped'])

        log.jobs_found = len(scraped_jobs)
        log.jobs_added = added
        log.jobs_updated = updated
        log.status = 'completed'
        log.completed_at = timezone.now()
        log.save()

        return added, updated, len(scraped_jobs)
    except Exception as exc:
        log.status = 'failed'
        log.error_message = str(exc)
        log.completed_at = timezone.now()
        log.save()
        raise


def upsert_jobs(source: JobSource, scraped_jobs: list[ScrapedJob]) -> tuple[int, int]:
    """Insert or update Job rows for a source. Returns (added, updated)."""
    added = 0
    updated = 0

    with transaction.atomic():
        for scraped in scraped_jobs:
            if not scraped.external_id:
                logger.warning('Skipping job without external_id from source %s', source.pk)
                continue

            defaults = {
                'title': scraped.title,
                'company': scraped.company,
                'location': scraped.location,
                'job_type': scraped.job_type,
                'description': scraped.description,
                'requirements': scraped.requirements,
                'benefits': scraped.benefits,
                'application_url': scraped.application_url,
                'salary_min': scraped.salary_min,
                'salary_max': scraped.salary_max,
                'salary_currency': scraped.salary_currency,
                'tags': scraped.tags,
                'posted_date': scraped.posted_date,
                'is_active': scraped.is_active,
            }

            job, created = Job.objects.update_or_create(
                source=source,
                external_id=scraped.external_id,
                defaults=defaults,
            )
            if created:
                added += 1
            else:
                updated += 1

    return added, updated
