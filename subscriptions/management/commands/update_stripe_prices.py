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
            '--plus-weekly-id',
            type=str,
            help='Stripe Price ID for Plus Weekly'
        )
        parser.add_argument(
            '--ultimate-monthly-id',
            type=str,
            help='Stripe Price ID for Ultimate Monthly'
        )
        parser.add_argument(
            '--ultimate-weekly-id',
            type=str,
            help='Stripe Price ID for Ultimate Weekly'
        )

    def handle(self, *args, **options):
        plus_plan = SubscriptionPlan.objects.get(name='Plus')

        plus_monthly, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('15.00'),
                'is_active': True,
            }
        )
        if not created:
            plus_monthly.price = Decimal('15.00')
        if options['plus_monthly_id']:
            plus_monthly.stripe_price_id = options['plus_monthly_id']
        plus_monthly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Plus Monthly: ${plus_monthly.price} (Price ID: {plus_monthly.stripe_price_id})'
            )
        )

        plus_weekly, created = PlanDuration.objects.get_or_create(
            plan=plus_plan,
            duration_type='WEEKLY',
            defaults={
                'price': Decimal('5.00'),
                'is_active': True,
            }
        )
        if not created:
            plus_weekly.price = Decimal('5.00')
        if options['plus_weekly_id']:
            plus_weekly.stripe_price_id = options['plus_weekly_id']
        plus_weekly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Plus Weekly: ${plus_weekly.price} (Price ID: {plus_weekly.stripe_price_id})'
            )
        )

        ultimate_plan = SubscriptionPlan.objects.get(name='Ultimate')

        ultimate_monthly, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='MONTHLY',
            defaults={
                'price': Decimal('39.90'),
                'is_active': True,
            }
        )
        if not created:
            ultimate_monthly.price = Decimal('39.90')
        if options['ultimate_monthly_id']:
            ultimate_monthly.stripe_price_id = options['ultimate_monthly_id']
        ultimate_monthly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Ultimate Monthly: ${ultimate_monthly.price} (Price ID: {ultimate_monthly.stripe_price_id})'
            )
        )

        ultimate_weekly, created = PlanDuration.objects.get_or_create(
            plan=ultimate_plan,
            duration_type='WEEKLY',
            defaults={
                'price': Decimal('10.00'),
                'is_active': True,
            }
        )
        if not created:
            ultimate_weekly.price = Decimal('10.00')
        if options['ultimate_weekly_id']:
            ultimate_weekly.stripe_price_id = options['ultimate_weekly_id']
        ultimate_weekly.save()
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated Ultimate Weekly: ${ultimate_weekly.price} (Price ID: {ultimate_weekly.stripe_price_id})'
            )
        )

        PlanDuration.objects.filter(
            plan__name__in=['Plus', 'Ultimate'], duration_type='YEARLY'
        ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS('Successfully updated all plan prices!'))

        self.stdout.write('\nCurrent Plan Status:')
        self.stdout.write('=' * 50)
        for plan in SubscriptionPlan.objects.filter(name__in=['Plus', 'Ultimate']):
            self.stdout.write(f'\n{plan.name} Plan:')
            for duration in plan.durations.all().order_by('duration_type'):
                status = '✓' if duration.stripe_price_id else '✗'
                self.stdout.write(
                    f'  {status} {duration.duration_type}: ${duration.price} '
                    f'(active={duration.is_active}, Price ID: {duration.stripe_price_id or "NOT SET"})'
                )
