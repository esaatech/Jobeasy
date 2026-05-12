"""Stripe recurring intervals and local period fallbacks aligned with PlanDuration.duration_type."""

from __future__ import annotations

from datetime import timedelta

STRIPE_RECURRING_INTERVAL: dict[str, str] = {
    'WEEKLY': 'week',
    'MONTHLY': 'month',
    'QUARTERLY': 'month',
    'SEMI_ANNUAL': 'month',
    'YEARLY': 'year',
}


def stripe_recurring_interval(duration_type: str) -> str:
    return STRIPE_RECURRING_INTERVAL.get(duration_type, 'month')


def fallback_period_delta(duration_type: str) -> timedelta:
    """When Stripe does not return current_period_end (fallback only)."""
    return {
        'WEEKLY': timedelta(days=7),
        'MONTHLY': timedelta(days=30),
        'QUARTERLY': timedelta(days=90),
        'SEMI_ANNUAL': timedelta(days=182),
        'YEARLY': timedelta(days=365),
    }.get(duration_type, timedelta(days=30))
