from django.core.management.base import BaseCommand

from job_service.models import JobSource


DEFAULT_SOURCES = [
    # --- Existing / US ---
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
        'name': 'Airbnb',
        'url': 'https://boards.greenhouse.io/airbnb',
        'source_type': 'api',
    },
    {
        'name': 'Cloudflare',
        'url': 'https://boards.greenhouse.io/cloudflare',
        'source_type': 'api',
    },
    {
        'name': 'Discord',
        'url': 'https://boards.greenhouse.io/discord',
        'source_type': 'api',
    },
    {
        'name': 'Anthropic',
        'url': 'https://boards.greenhouse.io/anthropic',
        'source_type': 'api',
    },
    {
        'name': 'Notion',
        'url': 'https://jobs.ashbyhq.com/notion',
        'source_type': 'api',
    },
    {
        'name': 'Linear',
        'url': 'https://jobs.ashbyhq.com/linear',
        'source_type': 'api',
    },
    {
        'name': 'Ramp',
        'url': 'https://jobs.ashbyhq.com/ramp',
        'source_type': 'api',
    },
    # --- Canadian ---
    {
        'name': 'Cohere',
        'url': 'https://jobs.ashbyhq.com/cohere',
        'source_type': 'api',
    },
    {
        'name': '1Password',
        'url': 'https://jobs.ashbyhq.com/1password',
        'source_type': 'api',
    },
    {
        'name': 'Hopper',
        'url': 'https://jobs.ashbyhq.com/hopper',
        'source_type': 'api',
    },
    {
        'name': 'Wealthsimple',
        'url': 'https://jobs.ashbyhq.com/wealthsimple',
        'source_type': 'api',
    },
    {
        'name': 'Wattpad',
        'url': 'https://jobs.lever.co/wattpad',
        'source_type': 'api',
    },
    {
        'name': 'Hootsuite',
        'url': 'https://boards.greenhouse.io/hootsuite',
        'source_type': 'api',
    },
    {
        'name': 'Lightspeed',
        'url': 'https://jobs.ashbyhq.com/lightspeed',
        'source_type': 'api',
    },
    {
        'name': 'Ritual',
        'url': 'https://boards.greenhouse.io/ritual',
        'source_type': 'api',
    },
    {
        'name': 'BenchSci',
        'url': 'https://jobs.lever.co/benchsci',
        'source_type': 'api',
    },
    # --- European ---
    {
        'name': 'Monzo',
        'url': 'https://boards.greenhouse.io/monzo',
        'source_type': 'api',
    },
    {
        'name': 'Spotify',
        'url': 'https://jobs.lever.co/spotify',
        'source_type': 'api',
    },
    {
        'name': 'SumUp',
        'url': 'https://boards.greenhouse.io/sumup',
        'source_type': 'api',
    },
    {
        'name': 'HelloFresh',
        'url': 'https://boards.greenhouse.io/hellofresh',
        'source_type': 'api',
    },
    {
        'name': 'Wolt',
        'url': 'https://boards.greenhouse.io/wolt',
        'source_type': 'api',
    },
    {
        'name': 'Celonis',
        'url': 'https://boards.greenhouse.io/celonis',
        'source_type': 'api',
    },
    {
        'name': 'Adyen',
        'url': 'https://boards.greenhouse.io/adyen',
        'source_type': 'api',
    },
    {
        'name': 'Elastic',
        'url': 'https://boards.greenhouse.io/elastic',
        'source_type': 'api',
    },
    {
        'name': 'Deliveroo',
        'url': 'https://jobs.ashbyhq.com/deliveroo',
        'source_type': 'api',
    },
    {
        'name': 'Doctolib',
        'url': 'https://boards.greenhouse.io/doctolib',
        'source_type': 'api',
    },
    {
        'name': 'Tide',
        'url': 'https://boards.greenhouse.io/tide',
        'source_type': 'api',
    },
    {
        'name': 'Alan',
        'url': 'https://jobs.ashbyhq.com/alan',
        'source_type': 'api',
    },
    {
        'name': 'N26',
        'url': 'https://boards.greenhouse.io/n26',
        'source_type': 'api',
    },
    {
        'name': 'Cabify',
        'url': 'https://boards.greenhouse.io/cabify',
        'source_type': 'api',
    },
    {
        'name': 'Trainline',
        'url': 'https://jobs.ashbyhq.com/trainline',
        'source_type': 'api',
    },
    {
        'name': 'DeepL',
        'url': 'https://jobs.ashbyhq.com/deepl',
        'source_type': 'api',
    },
    {
        'name': 'Bitpanda',
        'url': 'https://boards.greenhouse.io/bitpanda',
        'source_type': 'api',
    },
    {
        'name': 'Miro',
        'url': 'https://jobs.ashbyhq.com/miro',
        'source_type': 'api',
    },
    {
        'name': 'Mollie',
        'url': 'https://jobs.ashbyhq.com/mollie',
        'source_type': 'api',
    },
    {
        'name': 'Qonto',
        'url': 'https://jobs.ashbyhq.com/qonto',
        'source_type': 'api',
    },
    {
        'name': 'GoCardless',
        'url': 'https://boards.greenhouse.io/gocardless',
        'source_type': 'api',
    },
    {
        'name': 'Contentful',
        'url': 'https://boards.greenhouse.io/contentful',
        'source_type': 'api',
    },
    {
        'name': 'BlaBlaCar',
        'url': 'https://jobs.lever.co/blablacar',
        'source_type': 'api',
    },
    {
        'name': 'Back Market',
        'url': 'https://jobs.ashbyhq.com/backmarket',
        'source_type': 'api',
    },
    {
        'name': 'Typeform',
        'url': 'https://boards.greenhouse.io/typeform',
        'source_type': 'api',
    },
    {
        'name': 'Cleo',
        'url': 'https://boards.greenhouse.io/cleo',
        'source_type': 'api',
    },
    {
        'name': 'Trade Republic',
        'url': 'https://boards.greenhouse.io/traderepublic',
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
