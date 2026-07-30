from django.core.management.base import BaseCommand

from job_service.services.ingestion import run_scrape_cycle


class Command(BaseCommand):
    help = 'Scrape active job sources and upsert jobs into the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-type',
            choices=['all', 'api', 'rss', 'website', 'manual'],
            default='all',
            help='Only scrape sources of this type (default: all).',
        )
        parser.add_argument(
            '--source-id',
            type=int,
            help='Scrape a single JobSource by primary key.',
        )
        parser.add_argument(
            '--no-fetch-details',
            action='store_true',
            help='Skip per-job detail requests (faster Greenhouse runs; less description text).',
        )

    def handle(self, *args, **options):
        result = run_scrape_cycle(
            source_type=options['source_type'],
            source_id=options.get('source_id'),
            fetch_details=not options['no_fetch_details'],
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Scrape complete: '
                f'sources={result.sources_processed}, '
                f'failed={result.sources_failed}, '
                f'found={result.jobs_found}, '
                f'added={result.jobs_added}, '
                f'updated={result.jobs_updated}'
            )
        )

        if result.sources_failed:
            self.stdout.write(
                self.style.WARNING(
                    f'{result.sources_failed} source(s) failed. Check JobScrapingLog in admin.'
                )
            )
