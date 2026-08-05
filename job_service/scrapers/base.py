from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from job_service.models import JobSource


@dataclass
class ScrapedJob:
    """Normalized job payload produced by a scraper before DB upsert."""

    external_id: str
    title: str
    company: str
    location: str
    job_type: str
    description: str
    application_url: str
    requirements: str = ''
    benefits: str = ''
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str = 'USD'
    tags: list[str] = field(default_factory=list)
    work_arrangement: str = 'unknown'
    posted_date: datetime | None = None
    is_active: bool = True


class BaseScraper(ABC):
    """Interface for fetching jobs from a single JobSource."""

    def __init__(self, source: JobSource, *, fetch_details: bool = True):
        self.source = source
        self.fetch_details = fetch_details

    @abstractmethod
    def fetch(self) -> list[ScrapedJob]:
        """Return normalized jobs for this source."""

    def default_company(self) -> str:
        return self.source.name
