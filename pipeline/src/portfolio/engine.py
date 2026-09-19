"""Builds the portfolio's daily NAV/TWR series from the ledger — the piece
that turns single-day valuations (portfolio.valuation.value_day) into the
return history the site is built around. See CLAUDE.md section 9."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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


def external_flow_aud(ledger: Ledger, as_of: date, fx_source: FxRateSource) -> Decimal:
    """Net deposits minus withdrawals on exactly this date, converted to AUD."""
    total = Decimal(0)
    for c in ledger.cashflows:
        if c.date != as_of or c.type not in ("DEPOSIT", "WITHDRAWAL"):
            continue
        rate = rate_with_carry_forward(fx_source, c.currency, "AUD", as_of)
        if rate is None:
            raise ValueError(f"missing FX rate {c.currency}->AUD on {as_of}, no fallback available")
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
    previous_nav = sum(
        (
            c.amount * rate_with_carry_forward(fx_source, c.currency, "AUD", start)
            for c in ledger.cashflows
            if c.type == "DEPOSIT" and c.date <= start
        ),
        Decimal(0),
    )

    rows: list[tuple[date, DailyValuation, Decimal]] = []
    for d in business_days(start, as_of):
        valuation = value_day(ledger, d, price_source, fx_source)
        flow = Decimal(0) if d == start else external_flow_aud(ledger, d, fx_source)
        r = daily_return(valuation.nav_aud, previous_nav, flow)
        rows.append((d, valuation, r))
        previous_nav = valuation.nav_aud

    indices = chain_link([r for _, _, r in rows])
    return [
        NavPoint(date=d, nav_aud=v.nav_aud, index=idx, valuation=v)
        for (d, v, _), idx in zip(rows, indices)
    ]
