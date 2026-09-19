"""Price lookups with carry-forward across gaps a PriceSource doesn't
publish for (weekends, holidays). Sources stay dumb (exact-date lookups
only, see portfolio.sources); this is the shared place that knows about
staleness. Used by both portfolio.valuation (position prices) and
portfolio.benchmark (the IVV price series). See CLAUDE.md section 8."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from portfolio.sources import PriceSource

_CARRY_FORWARD_LOOKBACK_DAYS = 10


def business_days_between(start: date, end: date) -> int:
    days = 0
    d = start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days += 1
    return days


def price_with_carry_forward(
    source: PriceSource, instrument_id: str, as_of: date
) -> tuple[Decimal, str, date, int] | None:
    """Returns (price, currency, price_as_of, stale_business_days), or None
    if no price is found within the lookback window."""
    d = as_of
    for _ in range(_CARRY_FORWARD_LOOKBACK_DAYS):
        quote = source.get_price(instrument_id, d)
        if quote is not None:
            return quote.price, quote.currency, d, business_days_between(d, as_of)
        d -= timedelta(days=1)
    return None
