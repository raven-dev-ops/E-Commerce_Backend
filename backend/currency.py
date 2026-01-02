from __future__ import annotations

"""Utilities for currency conversion."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import requests  # type: ignore[import]
from django.conf import settings


DEFAULT_API = "https://api.exchangerate.host/latest"
CURRENCY_QUANTIZE = Decimal("0.01")


def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
    """Fetch exchange rate from `from_currency` to `to_currency` using an external API."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency == to_currency:
        return Decimal("1")
    url = getattr(settings, "EXCHANGE_RATE_API_URL", DEFAULT_API)
    response = requests.get(
        url, params={"base": from_currency, "symbols": to_currency}, timeout=5
    )
    response.raise_for_status()
    data: Any = response.json()
    rates = data.get("rates", {})
    rate = rates.get(to_currency)
    if rate is None:
        raise ValueError("Exchange rate not available")
    return Decimal(str(rate))


def _quantize_amount(amount: Decimal) -> Decimal:
    """Apply the currency rounding policy (2 decimal places, half-up)."""
    return amount.quantize(CURRENCY_QUANTIZE, rounding=ROUND_HALF_UP)


def convert_amount(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """Convert an amount between currencies using real-time rates."""
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    rate = get_exchange_rate(from_currency, to_currency)
    return _quantize_amount(amount * rate)
