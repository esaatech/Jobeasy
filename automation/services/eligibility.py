"""Ultimate / Test subscription eligibility for auto-apply."""

from __future__ import annotations

from subscriptions.models import UserSubscription


def is_ultimate_subscriber(user) -> bool:
    """True when the user has an ACTIVE Ultimate or Test subscription."""
    sub = (
        UserSubscription.objects.filter(
            user=user,
            plan__name__iexact='Ultimate',
            status='ACTIVE',
        )
        .select_related('plan')
        .first()
    )
    if sub and sub.is_active:
        return True

    # Test plan mirrors Ultimate for local/QA.
    test_sub = (
        UserSubscription.objects.filter(
            user=user,
            plan__name__iexact='Test',
            status='ACTIVE',
        )
        .select_related('plan')
        .first()
    )
    return bool(test_sub and test_sub.is_active)
