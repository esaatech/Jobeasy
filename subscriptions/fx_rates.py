"""
Fetch mid-market FX for subscription provisioning (not legal/tax advice).

Uses Frankfurter (ECB data), same source many apps use; no API key required.
Stripe does not expose a general "convert my catalog to MXN" API—you set
Price.unit_amount in the currency you charge.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

FRANKFURTER_CAD_MXN = 'https://api.frankfurter.app/latest?from=CAD&to=MXN'
USER_AGENT = 'JobeasSubscriptionProvisioner/1.0 (+https://jobeas.com)'


def fetch_cad_to_mxn_rate(timeout: float = 20.0) -> tuple[Decimal, str]:
    """
    Return (mxn_per_one_cad, rate_date_iso).

    Example: (Decimal('12.693'), '2026-04-23') means 1 CAD = 12.693 MXN.
    """
    req = urllib.request.Request(
        FRANKFURTER_CAD_MXN,
        headers={'User-Agent': USER_AGENT},
        method='GET',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.load(resp)
    rates = payload.get('rates') or {}
    raw = rates.get('MXN')
    if raw is None:
        raise ValueError(f'Unexpected Frankfurter response (no MXN): {payload!r}')
    rate = Decimal(str(raw)).quantize(Decimal('0.000001'))
    date = str(payload.get('date') or '')
    return rate, date


def convert_cad_to_mxn(cad_amount: Decimal, mxn_per_cad: Decimal) -> Decimal:
    """Convert a CAD major-unit amount to MXN major units (2 dp)."""
    return (cad_amount * mxn_per_cad).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
