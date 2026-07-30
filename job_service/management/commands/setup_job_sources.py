from django.core.management.base import BaseCommand

from job_service.models import JobSource


DEFAULT_SOURCES = [
    {
        'name': 'Stripe',
        'url': 'https://boards.greenhouse.io/stripe',
        'source_type': 'api',
    },
    {
        'name': 'Datadog',
        'url': 'https://boards.greenhouse.io/datadog',
        'source_type': 'api',
    },
    {
        'name': 'Vercel',
        'url': 'https://jobs.lever.co/vercel',
        'source_type': 'api',
    },
]


class Command(BaseCommand):
    help = 'Create or update default JobSource rows for API-based job boards.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--deactivate-missing',
            action='store_true',
            help='Deactivate default sources that are not in the built-in seed list.',
        )

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for entry in DEFAULT_SOURCES:
            source, was_created = JobSource.objects.update_or_create(
                url=entry['url'],
                defaults={
                    'name': entry['name'],
                    'source_type': entry['source_type'],
                    'is_active': True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created JobSource: {source.name}'))
            else:
                updated += 1
                self.stdout.write(f'Updated JobSource: {source.name}')

        if options['deactivate_missing']:
            default_urls = {entry['url'] for entry in DEFAULT_SOURCES}
            deactivated = (
                JobSource.objects.filter(source_type='api')
                .exclude(url__in=default_urls)
                .update(is_active=False)
            )
            self.stdout.write(f'Deactivated {deactivated} non-default API source(s).')

        self.stdout.write(
            self.style.SUCCESS(f'Done. created={created}, updated={updated}')
        )
