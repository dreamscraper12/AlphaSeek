"""Builds the portfolio's daily NAV/TWR series from the ledger — the piece
that turns single-day valuations (portfolio.valuation.value_day) into the
return history the site is built around. See CLAUDE.md section 9."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from portfolio.calendar_days import business_days
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


def inception_start_date(ledger: Ledger) -> date | None:
    """The date the index starts from: the earliest deposit, which arrives
    before the first trade (CLAUDE.md section 9)."""
    deposit_dates = [c.date for c in ledger.cashflows if c.type == "DEPOSIT"]
    return min(deposit_dates) if deposit_dates else None


def inception_deposit_aud(ledger: Ledger, fx_source: FxRateSource) -> Decimal | None:
    """The deposit(s) on or before the inception date, in AUD — the "prior
    close" baseline the index starts from (CLAUDE.md section 9), and the
    figure the site's headline sentence is built on."""
    start = inception_start_date(ledger)
    if start is None:
        return None

    total = Decimal(0)
    for c in ledger.cashflows:
        if c.type != "DEPOSIT" or c.date > start:
            continue
        rate = rate_with_carry_forward(fx_source, c.currency, "AUD", start)
        if rate is None:
            raise ValueError(f"missing FX rate {c.currency}->AUD on {start}, no fallback available")
        total += c.amount * rate
    return total


def external_flow_aud(
    ledger: Ledger, as_of: date, fx_source: FxRateSource, after: date | None = None
) -> Decimal:
    """Net deposits minus withdrawals credited to this valuation day, in AUD.

    Weekends and holidays carry no valuation points (CLAUDE.md section 8), so
    a flow dated on one belongs to the next valuation day rather than being
    dropped — which matters here, because a US session traded from Sydney
    routinely settles to a Saturday local date. `after` is the previous
    valuation day, making the window (after, as_of]; without it only `as_of`
    itself counts. Each flow converts at the rate on its own date."""
    start_exclusive = after if after is not None else as_of - timedelta(days=1)
    total = Decimal(0)
    for c in ledger.cashflows:
        if c.type not in ("DEPOSIT", "WITHDRAWAL"):
            continue
        if not start_exclusive < c.date <= as_of:
            continue
        rate = rate_with_carry_forward(fx_source, c.currency, "AUD", c.date)
        if rate is None:
            raise ValueError(f"missing FX rate {c.currency}->AUD on {c.date}, no fallback available")
        total += (c.amount if c.type == "DEPOSIT" else -c.amount) * rate
    return total


def external_flows_by_date(ledger: Ledger, fx_source: FxRateSource) -> dict[date, Decimal]:
    """Every date with a net external flow, converted to AUD — used by the
    shadow benchmark to apply the same flows to a different instrument."""
    dates = {c.date for c in ledger.cashflows if c.type in ("DEPOSIT", "WITHDRAWAL")}
    return {d: external_flow_aud(ledger, d, fx_source) for d in dates}


def build_nav_series(
    ledger: Ledger, as_of: date, price_source: PriceSource, fx_source: FxRateSource
) -> list[NavPoint]:
    start = inception_start_date(ledger)
    if start is None:
        return []

    # The deposit(s) on or before the start date define the "prior close"
    # baseline NAV (CLAUDE.md section 9): the first day's return is
    # NAV_D0 / deposit - 1, so that flow isn't also counted as a same-day
    # external flow below.
    previous_nav = inception_deposit_aud(ledger, fx_source)

    rows: list[tuple[date, DailyValuation, Decimal]] = []
    previous_day = start
    for d in business_days(start, as_of):
        valuation = value_day(ledger, d, price_source, fx_source)
        # Day zero's deposit is already the baseline above, so it isn't also
        # a same-day flow. Later days take every flow since the previous
        # valuation day, so weekend-dated ones aren't lost.
        flow = Decimal(0) if d == start else external_flow_aud(ledger, d, fx_source, after=previous_day)
        r = daily_return(valuation.nav_aud, previous_nav, flow)
        rows.append((d, valuation, r))
        previous_nav = valuation.nav_aud
        previous_day = d

    indices = chain_link([r for _, _, r in rows])
    return [
        NavPoint(date=d, nav_aud=v.nav_aud, index=idx, valuation=v)
        for (d, v, _), idx in zip(rows, indices)
    ]
