from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan, PlanDuration


class Command(BaseCommand):
    help = 'Update Django PlanDuration objects with test mode Stripe Price IDs'

    def add_arguments(self, parser):
        parser.add_argument('--plus-monthly-id', type=str, help='Test Stripe Price ID for Plus Monthly')
        parser.add_argument('--plus-weekly-id', type=str, help='Test Stripe Price ID for Plus Weekly')
        parser.add_argument('--ultimate-monthly-id', type=str, help='Test Stripe Price ID for Ultimate Monthly')
        parser.add_argument('--ultimate-weekly-id', type=str, help='Test Stripe Price ID for Ultimate Weekly')

    def handle(self, *args, **options):
        plus_plan = SubscriptionPlan.objects.filter(name='Plus', is_active=True).first()
        ultimate_plan = SubscriptionPlan.objects.filter(name='Ultimate', is_active=True).first()

        if not plus_plan:
            self.stdout.write(self.style.ERROR('Plus plan not found'))
            return

        if not ultimate_plan:
            self.stdout.write(self.style.ERROR('Ultimate plan not found'))
            return

        if plus_plan:
            plus_monthly = PlanDuration.objects.filter(
                plan=plus_plan,
                duration_type='MONTHLY'
            ).first()

            plus_weekly = PlanDuration.objects.filter(
                plan=plus_plan,
                duration_type='WEEKLY'
            ).first()

            if plus_monthly and options['plus_monthly_id']:
                plus_monthly.stripe_price_id = options['plus_monthly_id']
                plus_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Plus Monthly: {options["plus_monthly_id"]}')
                )

            if plus_weekly and options['plus_weekly_id']:
                plus_weekly.stripe_price_id = options['plus_weekly_id']
                plus_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Plus Weekly: {options["plus_weekly_id"]}')
                )

        if ultimate_plan:
            ultimate_monthly = PlanDuration.objects.filter(
                plan=ultimate_plan,
                duration_type='MONTHLY'
            ).first()

            ultimate_weekly = PlanDuration.objects.filter(
                plan=ultimate_plan,
                duration_type='WEEKLY'
            ).first()

            if ultimate_monthly and options['ultimate_monthly_id']:
                ultimate_monthly.stripe_price_id = options['ultimate_monthly_id']
                ultimate_monthly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Ultimate Monthly: {options["ultimate_monthly_id"]}')
                )

            if ultimate_weekly and options['ultimate_weekly_id']:
                ultimate_weekly.stripe_price_id = options['ultimate_weekly_id']
                ultimate_weekly.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated Ultimate Weekly: {options["ultimate_weekly_id"]}')
                )

        self.stdout.write(self.style.SUCCESS('Test Price IDs updated successfully!'))
