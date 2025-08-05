from django.core.management.base import BaseCommand
from subscriptions.utils import sync_prices_from_stripe


class Command(BaseCommand):
    help = 'Sync plan prices from Stripe to Django database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self.stdout.write('DRY RUN - No changes will be made')
            self.stdout.write('=' * 50)
        
        self.stdout.write('Syncing prices from Stripe...')
        
        try:
            updated_count = sync_prices_from_stripe()
            
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully synced {updated_count} price(s) from Stripe'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No prices needed updating')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing prices: {str(e)}')
            ) 