"""
Create Stripe Products + recurring Prices in a *destination* Stripe account from
Django SubscriptionPlan / PlanDuration rows, then optionally update stripe_price_id.

Stripe does NOT let you "move" live subscriptions, customers, or payment methods
between accounts. This command only recreates catalog (products + prices) and
updates Django price IDs so new checkouts use the new account.

Currency: pass --currency (default usd via STRIPE_PROVISION_CURRENCY). Amounts are
Django PlanDuration.price in *major* units (unit_amount = price * 100 for MXN/CAD/USD).

For your legacy CAD catalog on a fresh project, you can sync DB prices first:
  --seed-legacy-cad-prices

Usage:
  export STRIPE_DESTINATION_SECRET_KEY=sk_test_...   # new Stripe account
  poetry run python manage.py provision_stripe_catalog --seed-legacy-cad-prices --currency cad --dry-run
  poetry run python manage.py provision_stripe_catalog --seed-legacy-cad-prices --currency cad --apply

  poetry run python manage.py provision_stripe_catalog --seed-usd-catalog-prices --currency usd --dry-run
  poetry run python manage.py provision_stripe_catalog --seed-usd-catalog-prices --currency usd --apply

Uses MYAPP_STRIPE_SECRET_KEY if STRIPE_DESTINATION_SECRET_KEY is unset (same .env as the app).

Stripe does not convert catalog prices for you; the MXN seed path uses a mid-market rate, writes MXN
amounts to Django, then creates MXN recurring Prices.

Optional:
  export STRIPE_SOURCE_SECRET_KEY=sk_...   # old account (verification only)
"""
import os
import urllib.error
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from subscriptions.fx_rates import convert_cad_to_mxn, fetch_cad_to_mxn_rate
from subscriptions.models import PlanDuration, SubscriptionPlan

# Your previous Stripe catalog (CAD), keyed by (plan name, duration_type).
LEGACY_CAD_PRICES = {
    ('Plus', 'MONTHLY'): Decimal('19.99'),
    ('Plus', 'YEARLY'): Decimal('191.99'),
    ('Ultimate', 'MONTHLY'): Decimal('49.99'),
    ('Ultimate', 'YEARLY'): Decimal('399.99'),
    ('Test', 'MONTHLY'): Decimal('1.50'),
}

RECURRING_MAP = {
    'WEEKLY': 'week',
    'MONTHLY': 'month',
    'YEARLY': 'year',
    'QUARTERLY': 'month',
    'SEMI_ANNUAL': 'month',
    'ONE_TIME': None,
}

# Default USD catalog (Weekly + Monthly). Use --seed-usd-catalog-prices to write into Django.
CATALOG_USD_PRICES = {
    ('Plus', 'WEEKLY'): Decimal('5.00'),
    ('Plus', 'MONTHLY'): Decimal('15.00'),
    ('Ultimate', 'WEEKLY'): Decimal('10.00'),
    ('Ultimate', 'MONTHLY'): Decimal('39.90'),
    ('Test', 'WEEKLY'): Decimal('0.05'),
    ('Test', 'MONTHLY'): Decimal('0.10'),
}


def _interval_for_duration(duration_type: str):
    if duration_type == 'ONE_TIME':
        return None
    return RECURRING_MAP.get(duration_type, 'month')


def _unit_amount_minor(price: Decimal) -> int:
    """Stripe unit_amount for 2-decimal currencies (USD, CAD, MXN, ...)."""
    return int((price * 100).quantize(Decimal('1')))


def _seed_legacy_cad_prices(stdout, style):
    """Align PlanDuration.price in Django with the known legacy CAD amounts."""
    updated = 0
    for (plan_name, duration_type), amount in LEGACY_CAD_PRICES.items():
        plan = SubscriptionPlan.objects.filter(name__iexact=plan_name, is_active=True).first()
        if not plan:
            stdout.write(style.WARNING(f'  [seed] No plan named {plan_name!r}, skipping.'))
            continue
        dur = PlanDuration.objects.filter(
            plan=plan, duration_type=duration_type, is_active=True
        ).first()
        if not dur:
            stdout.write(
                style.WARNING(
                    f'  [seed] No duration {plan_name!r} {duration_type!r}, skipping.'
                )
            )
            continue
        if dur.price != amount:
            dur.price = amount
            dur.save(update_fields=['price', 'updated_at'])
            updated += 1
            stdout.write(style.SUCCESS(f'  [seed] {plan_name} {duration_type} -> ${amount} CAD (DB)'))
        else:
            stdout.write(f'  [seed] {plan_name} {duration_type} already ${amount} CAD')
    return updated


def _seed_usd_catalog_prices(stdout, style):
    """Sync Plus/Ultimate/(Test) weekly+monthly USD amounts; deactivate yearly durations."""
    updated = 0
    for (plan_name, duration_type), amount in CATALOG_USD_PRICES.items():
        plan = SubscriptionPlan.objects.filter(name__iexact=plan_name, is_active=True).first()
        if not plan:
            stdout.write(style.WARNING(f'  [seed-usd] No plan named {plan_name!r}, skipping.'))
            continue
        dur, created = PlanDuration.objects.get_or_create(
            plan=plan,
            duration_type=duration_type,
            defaults={'price': amount, 'is_active': True},
        )
        dirty = False
        if not created and dur.price != amount:
            dur.price = amount
            dirty = True
        if not dur.is_active:
            dur.is_active = True
            dirty = True
        if dirty or created:
            dur.save()
            updated += 1
        stdout.write(
            style.SUCCESS(f'  [seed-usd] {plan_name} {duration_type} -> US${amount}')
        )

    for plan_name in ('Plus', 'Ultimate', 'Test'):
        plan = SubscriptionPlan.objects.filter(name__iexact=plan_name, is_active=True).first()
        if plan:
            n = PlanDuration.objects.filter(plan=plan, duration_type='YEARLY').update(is_active=False)
            if n:
                stdout.write(style.WARNING(f'  [seed-usd] Deactivated YEARLY for {plan_name}'))
    return updated


def _seed_mxn_from_cad_live_fx(stdout, style):
    """
    Fetch CAD→MXN, convert LEGACY_CAD_PRICES to MXN, save on PlanDuration rows.
    Returns (rows_updated, mxn_per_cad, rate_date, approx_cad_per_mxn_hint).
    """
    mxn_per_cad, rate_date = fetch_cad_to_mxn_rate()
    approx_cad_per_mxn = (Decimal('1') / mxn_per_cad).quantize(Decimal('0.000001'))
    stdout.write(
        style.SUCCESS(
            f'  [fx] Frankfurter (ECB): 1 CAD = {mxn_per_cad} MXN (as of {rate_date}). '
            f'For pricing hints in .env: PRICING_APPROX_CAD_PER_MXN={approx_cad_per_mxn}'
        )
    )
    updated = 0
    for (plan_name, duration_type), cad_amount in LEGACY_CAD_PRICES.items():
        plan = SubscriptionPlan.objects.filter(name__iexact=plan_name, is_active=True).first()
        if not plan:
            stdout.write(style.WARNING(f'  [seed-mxn] No plan named {plan_name!r}, skipping.'))
            continue
        dur = PlanDuration.objects.filter(
            plan=plan, duration_type=duration_type, is_active=True
        ).first()
        if not dur:
            stdout.write(
                style.WARNING(
                    f'  [seed-mxn] No duration {plan_name!r} {duration_type!r}, skipping.'
                )
            )
            continue
        mxn_amount = convert_cad_to_mxn(cad_amount, mxn_per_cad)
        if dur.price != mxn_amount:
            dur.price = mxn_amount
            dur.save(update_fields=['price', 'updated_at'])
            updated += 1
        stdout.write(
            style.SUCCESS(
                f'  [seed-mxn] {plan_name} {duration_type}: {cad_amount} CAD -> {mxn_amount} MXN'
            )
        )
    return updated, mxn_per_cad, rate_date, approx_cad_per_mxn


def _resolve_stripe_secret_key():
    return (
        os.environ.get('STRIPE_DESTINATION_SECRET_KEY', '').strip()
        or os.environ.get('MYAPP_STRIPE_SECRET_KEY', '').strip()
    )


class Command(BaseCommand):
    help = (
        'Create Products and Prices in a destination Stripe account from Django '
        'plan data; optionally update PlanDuration.stripe_price_id. '
        'Does not migrate subscriptions or customers. Use --currency for CAD/MXN/etc.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Create objects in Stripe and update Django stripe_price_id fields',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions only (default if neither --apply nor --dry-run: dry-run)',
        )
        parser.add_argument(
            '--currency',
            type=str,
            default=os.environ.get('STRIPE_PROVISION_CURRENCY', 'usd').lower().strip(),
            help='Stripe currency code (default: usd, or STRIPE_PROVISION_CURRENCY). Examples: usd, mxn, cad.',
        )
        parser.add_argument(
            '--seed-legacy-cad-prices',
            action='store_true',
            help='Update Django PlanDuration.price to match the legacy CAD catalog (Plus/Ultimate/Test) before provisioning.',
        )
        parser.add_argument(
            '--seed-usd-catalog-prices',
            action='store_true',
            help='Write default Weekly+Monthly USD amounts to Django (Plus/Ultimate/Test), deactivate YEARLY, then provision.',
        )
        parser.add_argument(
            '--seed-mxn-from-cad-fx',
            action='store_true',
            help='Fetch live CAD→MXN (Frankfurter/ECB), convert legacy CAD catalog to MXN in Django, then provision in MXN.',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        dry_run = options['dry_run'] or not apply_changes
        currency = (options['currency'] or 'usd').lower().strip()
        if len(currency) != 3:
            self.stderr.write(self.style.ERROR('--currency must be a 3-letter ISO code (e.g. cad, mxn).'))
            return

        seed_flags = sum(
            1
            for k in (
                'seed_legacy_cad_prices',
                'seed_mxn_from_cad_fx',
                'seed_usd_catalog_prices',
            )
            if options[k]
        )
        if seed_flags > 1:
            self.stderr.write(
                self.style.ERROR(
                    'Use only one seed flag: --seed-legacy-cad-prices, '
                    '--seed-mxn-from-cad-fx, or --seed-usd-catalog-prices.'
                )
            )
            return

        if options['seed_legacy_cad_prices']:
            self.stdout.write('Seeding legacy CAD prices into Django...')
            n = _seed_legacy_cad_prices(self.stdout, self.style)
            self.stdout.write(self.style.SUCCESS(f'Seed complete ({n} row(s) updated).\n'))

        if options['seed_usd_catalog_prices']:
            self.stdout.write('Seeding default USD catalog (weekly + monthly) into Django...')
            n = _seed_usd_catalog_prices(self.stdout, self.style)
            self.stdout.write(self.style.SUCCESS(f'USD seed complete ({n} row(s) touched).\n'))
            currency = 'usd'

        if options['seed_mxn_from_cad_fx']:
            self.stdout.write('Fetching live CAD→MXN and seeding Django with converted MXN amounts...')
            try:
                n, rate, rate_date, cad_per_mxn = _seed_mxn_from_cad_live_fx(self.stdout, self.style)
            except urllib.error.URLError as exc:
                self.stderr.write(self.style.ERROR(f'FX fetch failed (network): {exc}'))
                return
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'FX fetch failed: {exc}'))
                return
            self.stdout.write(
                self.style.SUCCESS(
                    f'Seed MXN complete ({n} row(s) changed). Stripe catalog will use currency=MXN.\n'
                )
            )
            currency = 'mxn'

        dest_key = _resolve_stripe_secret_key()
        if not dest_key:
            self.stderr.write(
                self.style.ERROR(
                    'Set STRIPE_DESTINATION_SECRET_KEY or MYAPP_STRIPE_SECRET_KEY to your '
                    'Stripe secret key (sk_test_... or sk_live_...).'
                )
            )
            return

        source_key = os.environ.get('STRIPE_SOURCE_SECRET_KEY', '').strip()
        if source_key:
            stripe.api_key = source_key
            try:
                acct = stripe.Account.retrieve()
                self.stdout.write(
                    f'[source] Stripe account: {getattr(acct, "id", "?")} '
                    f'(optional; catalog built from Django)'
                )
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'[source] Could not verify key: {exc}'))
        else:
            self.stdout.write('[source] STRIPE_SOURCE_SECRET_KEY not set (optional).')

        stripe.api_key = dest_key
        try:
            dest_acct = stripe.Account.retrieve()
            self.stdout.write(
                self.style.SUCCESS(
                    f'[dest]   Stripe account: {getattr(dest_acct, "id", "?")}  currency={currency.upper()}'
                )
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'[dest] Invalid destination key: {exc}'))
            return

        plans_qs = SubscriptionPlan.objects.filter(is_active=True).exclude(name='Free')
        if not settings.DEBUG:
            plans_qs = plans_qs.exclude(name='Test')

        product_by_plan_id = {}

        def get_or_create_product(plan: SubscriptionPlan):
            if plan.id in product_by_plan_id:
                return product_by_plan_id[plan.id]
            name = f'JOBEAS {plan.name}'
            meta = {
                'jobeas_plan_id': str(plan.id),
                'jobeas_plan_slug': plan.name.lower(),
            }
            if dry_run:
                self.stdout.write(f'  [dry-run] Product: {name} metadata={meta}')
                fake = type('obj', (), {'id': 'prod_DRYRUN'})()
                product_by_plan_id[plan.id] = fake
                return fake
            prod = stripe.Product.create(name=name, metadata=meta)
            product_by_plan_id[plan.id] = prod
            self.stdout.write(self.style.SUCCESS(f'  Created product {prod.id} ({name})'))
            return prod

        updates = []

        for plan in plans_qs.prefetch_related('durations'):
            for dur in plan.durations.filter(is_active=True):
                interval = _interval_for_duration(dur.duration_type)
                if interval is None and dur.duration_type != 'ONE_TIME':
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Skip {plan.name} {dur.duration_type}: unsupported mapping.'
                        )
                    )
                    continue
                if dur.duration_type == 'ONE_TIME':
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Skip {plan.name} ONE_TIME: create manually or extend this command.'
                        )
                    )
                    continue

                product = get_or_create_product(plan)
                unit_amount = _unit_amount_minor(dur.price)

                recurring = {'interval': interval}
                if dur.duration_type == 'QUARTERLY':
                    recurring['interval_count'] = 3
                    recurring['interval'] = 'month'
                elif dur.duration_type == 'SEMI_ANNUAL':
                    recurring['interval_count'] = 6
                    recurring['interval'] = 'month'

                self.stdout.write(
                    f'  Price: {plan.name} / {dur.duration_type} '
                    f'{dur.price} {currency.upper()} recurring={recurring} '
                    f'unit_amount={unit_amount}'
                )

                if dry_run:
                    updates.append((dur, 'price_DRYRUN'))
                    continue

                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=unit_amount,
                    currency=currency,
                    recurring=recurring,
                    metadata={
                        'jobeas_plan_duration_id': str(dur.id),
                        'jobeas_duration_type': dur.duration_type,
                    },
                )
                self.stdout.write(self.style.SUCCESS(f'    -> {price.id}'))
                updates.append((dur, price.id))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\nDry run complete. Re-run with --apply to write to Stripe + Django.'
                )
            )
            return

        with transaction.atomic():
            for dur, price_id in updates:
                dur.stripe_price_id = price_id
                dur.save(update_fields=['stripe_price_id', 'updated_at'])
        self.stdout.write(
            self.style.SUCCESS(
                f'\nUpdated {len(updates)} PlanDuration row(s). '
                'Set MYAPP_STRIPE_SECRET_KEY and MYAPP_STRIPE_PUBLISHABLE_KEY to this '
                'Stripe account in .env and restart the app.'
            )
        )
