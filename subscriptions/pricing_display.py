from __future__ import annotations

"""
Localized / country-aware *display* helpers for subscription prices.

Billing is charged in STRIPE_BILLING_CURRENCY (default USD). Optional approximate
lines for visitors in CA/US use PRICING_APPROX_* env vars when billing is MXN (see jobeas/settings.py).
"""
from decimal import Decimal

from django.conf import settings


def get_client_country_code(request):
    """
    Best-effort country for pricing hints (not legal/tax residency).

    Prefer Cloudflare's CF-IPCountry when present; otherwise None (show billing only).
    """
    if not request:
        return None
    cf = (request.META.get('HTTP_CF_IPCOUNTRY') or '').strip().upper()
    if cf and cf not in ('XX', 'T1', ''):
        return cf
    return None


def format_money_amount(amount: Decimal, currency: str) -> str:
    """Human-readable amount in the billing currency (no locale dependency)."""
    currency = (currency or getattr(settings, 'STRIPE_BILLING_CURRENCY', 'usd')).upper()
    s = f'{amount:,.2f}'
    if currency == 'MXN':
        return f'MXN ${s}'
    if currency == 'USD':
        return f'US${s}'
    if currency == 'CAD':
        return f'CA${s}'
    return f'{currency} {s}'


def approximate_secondary_line(amount: Decimal, billing_currency: str, country_code: str | None):
    """
    Optional indicative conversion when billing is MXN and visitor is CA/US.

    Uses PRICING_APPROX_CAD_PER_MXN / PRICING_APPROX_USD_PER_MXN: multiply MXN
    amount by the rate to get approximate CAD/USD for display only.
    """
    billing_currency = (billing_currency or 'USD').upper()
    if billing_currency != 'MXN' or not country_code:
        return None
    try:
        amt = Decimal(amount)
    except Exception:
        return None

    if country_code == 'CA':
        rate = getattr(settings, 'PRICING_APPROX_CAD_PER_MXN', None)
        if rate is None:
            return None
        foreign = (amt * Decimal(str(rate))).quantize(Decimal('0.01'))
        return f'About CA${foreign:,.2f} (indicative; you are charged in MXN)'

    if country_code == 'US':
        rate = getattr(settings, 'PRICING_APPROX_USD_PER_MXN', None)
        if rate is None:
            return None
        foreign = (amt * Decimal(str(rate))).quantize(Decimal('0.01'))
        return f'About US${foreign:,.2f} (indicative; you are charged in MXN)'

    return None


def attach_price_display(duration, request):
    """Set price_display_primary / price_display_secondary on a PlanDuration instance."""
    billing_currency = (
        getattr(duration, 'stripe_currency', None)
        or getattr(settings, 'STRIPE_BILLING_CURRENCY', 'usd').upper()
    )
    if duration.has_stripe_price and getattr(duration, 'stripe_price', None) is not None:
        amt = duration.stripe_price
    else:
        amt = duration.price

    duration.price_display_primary = format_money_amount(amt, billing_currency)
    country = get_client_country_code(request)
    duration.price_display_secondary = approximate_secondary_line(
        amt, billing_currency, country
    )
