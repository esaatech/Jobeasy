from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan, PlanDuration
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update Django PlanDuration objects with Stripe prices and Price IDs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plus-monthly-id',
            type=str,
            help='Stripe Price ID for Plus Monthly'
        )
        parser.add_argument(
            '--plus-yearly-id',
            type=str,
            help='Stripe Price ID for Plus Yearly'
        )
        parser.add_argument(
            '--ultimate-monthly-id',
            type=str,
            help='Stripe Price ID for Ultimate Monthly'
        )
        parser.add_argument(
            '--ultimate-yearly-id',
            type=str,
            help='Stripe Price ID for Ultimate Yearly'
        )

    def handle(self, *args, **options):
        # Update Plus Plan prices
        plus_plan = SubscriptionPlan.objects.get(name='Plus')
        
        # Plus Monthly: $19.99
        plus_monthly, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('19.99'),
                'is_active': True,
            }
        )
        if not created:
            plus_monthly.price = Decimal('19.99')
        if options['plus_monthly_id']:
            plus_monthly.stripe_price_id = options['plus_monthly_id']
        plus_monthly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Plus Monthly: ${plus_monthly.price} (Price ID: {plus_monthly.stripe_price_id})'
            )
        )

        # Plus Yearly: $191.99
        plus_yearly, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='YEARLY',
            defaults={
                'price': Decimal('191.99'),
                'is_active': True,
            }
        )
        if not created:
            plus_yearly.price = Decimal('191.99')
        if options['plus_yearly_id']:
            plus_yearly.stripe_price_id = options['plus_yearly_id']
        plus_yearly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Plus Yearly: ${plus_yearly.price} (Price ID: {plus_yearly.stripe_price_id})'
            )
        )

        # Update Ultimate Plan prices
        ultimate_plan = SubscriptionPlan.objects.get(name='Ultimate')
        
        # Ultimate Monthly: $49.99
        ultimate_monthly, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('49.99'),
                'is_active': True,
            }
        )
        if not created:
            ultimate_monthly.price = Decimal('49.99')
        if options['ultimate_monthly_id']:
            ultimate_monthly.stripe_price_id = options['ultimate_monthly_id']
        ultimate_monthly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Ultimate Monthly: ${ultimate_monthly.price} (Price ID: {ultimate_monthly.stripe_price_id})'
            )
        )

        # Ultimate Yearly: $399.99
        ultimate_yearly, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='YEARLY',
            defaults={
                'price': Decimal('399.99'),
                'is_active': True,
            }
        )
        if not created:
            ultimate_yearly.price = Decimal('399.99')
        if options['ultimate_yearly_id']:
            ultimate_yearly.stripe_price_id = options['ultimate_yearly_id']
        ultimate_yearly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Ultimate Yearly: ${ultimate_yearly.price} (Price ID: {ultimate_yearly.stripe_price_id})'
            )
        )

        self.stdout.write(self.style.SUCCESS('Successfully updated all plan prices!'))
        
        # Show current status
        self.stdout.write('\nCurrent Plan Status:')
        self.stdout.write('=' * 50)
        for plan in SubscriptionPlan.objects.filter(name__in=['Plus', 'Ultimate']):
            self.stdout.write(f'\n{plan.name} Plan:')
            for duration in plan.durations.all():
                status = '✓' if duration.stripe_price_id else '✗'
                self.stdout.write(
                    f'  {status} {duration.duration_type}: ${duration.price} '
                    f'(Price ID: {duration.stripe_price_id or "NOT SET"})'
                ) 