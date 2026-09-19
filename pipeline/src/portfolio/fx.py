"""FX conversion. Rates come from an FxRateSource (Frankfurter — see
CLAUDE.md section 3 decision log); this module carries the rate forward
across gaps the source doesn't publish (weekends, holidays), so any caller
gets a rate for every calendar day without needing its own carry-forward
logic. See CLAUDE.md section 8."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from portfolio.sources import FxRateSource

_CARRY_FORWARD_LOOKBACK_DAYS = 10


def convert(amount: Decimal, rate: Decimal) -> Decimal:
    return amount * rate


def rate_with_carry_forward(
    fx_source: FxRateSource, from_currency: str, to_currency: str, as_of: date
) -> Decimal | None:
    if from_currency == to_currency:
        return Decimal(1)
    d = as_of
    for _ in range(_CARRY_FORWARD_LOOKBACK_DAYS):
        rate = fx_source.get_rate(from_currency, to_currency, d)
        if rate is not None:
            return rate
        d -= timedelta(days=1)
    return None
