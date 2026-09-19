"""Builds the portfolio's daily NAV/TWR series from the ledger — the piece
that turns single-day valuations (portfolio.valuation.value_day) into the
return history the site is built around. See CLAUDE.md section 9.

Business days are treated as Monday-Friday; AU/US public holidays aren't
modelled as a separate calendar, since a holiday behaves exactly like a
stale-price gap the valuation layer already carries forward across.

The benchmark (IVV total return, with distributions reinvested — see
section 9) isn't included here: it needs a distribution data source that
hasn't been chosen yet (CLAUDE.md section 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from portfolio.fx import rate_with_carry_forward
from portfolio.ledger import Ledger
from portfolio.performance import chain_link, daily_return
from portfolio.sources import FxRateSource, PriceSource
from portfolio.valuation import DailyValuation, value_day


@dataclass(frozen=True)
class NavPoint:
    date: date
    nav_aud: Decimal
    index: Decimal
    valuation: DailyValuation


def _business_days(start: date, end: date) -> list[date]:
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def _external_flow_aud(ledger: Ledger, as_of: date, fx_source: FxRateSource) -> Decimal:
    total = Decimal(0)
    for c in ledger.cashflows:
        if c.date != as_of or c.type not in ("DEPOSIT", "WITHDRAWAL"):
            continue
        rate = rate_with_carry_forward(fx_source, c.currency, "AUD", as_of)
        if rate is None:
            raise ValueError(f"missing FX rate {c.currency}->AUD on {as_of}, no fallback available")
        total += (c.amount if c.type == "DEPOSIT" else -c.amount) * rate
    return total


def build_nav_series(
    ledger: Ledger, as_of: date, price_source: PriceSource, fx_source: FxRateSource
) -> list[NavPoint]:
    deposit_dates = [c.date for c in ledger.cashflows if c.type == "DEPOSIT"]
    if not deposit_dates:
        return []
    start = min(deposit_dates)

    # The deposit(s) on or before the start date define the "prior close"
    # baseline NAV (CLAUDE.md section 9): the first day's return is
    # NAV_D0 / deposit - 1, so that flow isn't also counted as a same-day
    # external flow below.
    previous_nav = sum(
        (
            c.amount * rate_with_carry_forward(fx_source, c.currency, "AUD", start)
            for c in ledger.cashflows
            if c.type == "DEPOSIT" and c.date <= start
        ),
        Decimal(0),
    )

    rows: list[tuple[date, DailyValuation, Decimal]] = []
    for d in _business_days(start, as_of):
        valuation = value_day(ledger, d, price_source, fx_source)
        flow = Decimal(0) if d == start else _external_flow_aud(ledger, d, fx_source)
        r = daily_return(valuation.nav_aud, previous_nav, flow)
        rows.append((d, valuation, r))
        previous_nav = valuation.nav_aud

    indices = chain_link([r for _, _, r in rows])
    return [
        NavPoint(date=d, nav_aud=v.nav_aud, index=idx, valuation=v)
        for (d, v, _), idx in zip(rows, indices)
    ]
