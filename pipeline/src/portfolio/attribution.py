"""Per-position daily contribution to portfolio return. See CLAUDE.md
section 9. Builds on the daily valuations portfolio.engine already computed
for the NAV series, so no positions are re-priced here.

Every line uses the same formula:
    contribution = (MV_today - MV_yesterday - net_purchases + income) / NAV_yesterday
"purchases" and "income" only exist to correct for money crossing between
an instrument and cash: buying/selling moves money into/out of an
instrument from outside its own price return, and a dividend leaves the
paying instrument's market value and lands in cash. The "Cash & FX" line
(CLAUDE.md section 9: "FX on cash is its own line") is just cash treated
the same way, with those same crossings netted out so every line together
sums, day by day, to the portfolio's own return — interest needs no such
correction, since it starts and ends in cash with nothing to reattribute.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from portfolio.engine import NavPoint
from portfolio.fx import rate_with_carry_forward
from portfolio.ledger import Ledger
from portfolio.sources import FxRateSource

CASH_AND_FX_LINE = "CASH_AND_FX"


@dataclass(frozen=True)
class Contribution:
    date: date
    instrument_id: str
    contribution: Decimal


def daily_contribution(
    mv_today: Decimal,
    mv_yesterday: Decimal,
    net_purchases: Decimal,
    income: Decimal,
    nav_yesterday: Decimal,
) -> Decimal:
    return (mv_today - mv_yesterday - net_purchases + income) / nav_yesterday


def _net_purchases_by_instrument(
    ledger: Ledger, as_of: date, fx_source: FxRateSource
) -> dict[str, Decimal]:
    """Positive for a BUY (money moving into the position from cash),
    negative for a SELL — mirrors external flows, but between an
    instrument and cash rather than between the portfolio and the owner."""
    instruments_by_id = {i.instrument_id: i for i in ledger.instruments}
    result: dict[str, Decimal] = {}
    for t in ledger.trades:
        if t.executed_at.date() != as_of:
            continue
        instrument = instruments_by_id[t.instrument_id]
        multiplier = instrument.multiplier if instrument.type == "option" else Decimal(1)
        rate = rate_with_carry_forward(fx_source, instrument.currency, "AUD", as_of)
        if rate is None:
            raise ValueError(f"missing FX rate {instrument.currency}->AUD on {as_of}, no fallback available")
        cost_aud = t.quantity * t.price * multiplier * rate
        signed = cost_aud if t.side == "BUY" else -cost_aud
        result[t.instrument_id] = result.get(t.instrument_id, Decimal(0)) + signed
    return result


def _income_by_instrument(ledger: Ledger, as_of: date, fx_source: FxRateSource) -> dict[str, Decimal]:
    """Dividends (and withholding tax against them) attributed back to the
    instrument that paid them, since that cash has already left the
    instrument's own market value by the time it reaches the cash bucket."""
    result: dict[str, Decimal] = {}
    for c in ledger.cashflows:
        if c.date != as_of or c.instrument_id is None or c.type not in ("DIVIDEND", "WITHHOLDING_TAX"):
            continue
        rate = rate_with_carry_forward(fx_source, c.currency, "AUD", as_of)
        if rate is None:
            raise ValueError(f"missing FX rate {c.currency}->AUD on {as_of}, no fallback available")
        signed = c.amount if c.type == "DIVIDEND" else -c.amount
        result[c.instrument_id] = result.get(c.instrument_id, Decimal(0)) + signed * rate
    return result


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


def build_attribution(
    ledger: Ledger, nav_series: list[NavPoint], fx_source: FxRateSource
) -> list[Contribution]:
    rows: list[Contribution] = []

    for i in range(1, len(nav_series)):
        prev, curr = nav_series[i - 1], nav_series[i]
        nav_yesterday = prev.nav_aud
        d = curr.date

        mv_yesterday_by_id = {p.instrument_id: p.market_value_aud for p in prev.valuation.positions}
        mv_today_by_id = {p.instrument_id: p.market_value_aud for p in curr.valuation.positions}
        instrument_ids = set(mv_yesterday_by_id) | set(mv_today_by_id)

        net_purchases = _net_purchases_by_instrument(ledger, d, fx_source)
        income = _income_by_instrument(ledger, d, fx_source)

        for instrument_id in instrument_ids:
            contribution = daily_contribution(
                mv_today_by_id.get(instrument_id, Decimal(0)),
                mv_yesterday_by_id.get(instrument_id, Decimal(0)),
                net_purchases.get(instrument_id, Decimal(0)),
                income.get(instrument_id, Decimal(0)),
                nav_yesterday,
            )
            rows.append(Contribution(date=d, instrument_id=instrument_id, contribution=contribution))

        external_flow = _external_flow_aud(ledger, d, fx_source)
        cash_net_transfers = (
            external_flow - sum(net_purchases.values(), Decimal(0)) + sum(income.values(), Decimal(0))
        )
        cash_contribution = daily_contribution(
            curr.valuation.cash_aud, prev.valuation.cash_aud, cash_net_transfers, Decimal(0), nav_yesterday
        )
        rows.append(Contribution(date=d, instrument_id=CASH_AND_FX_LINE, contribution=cash_contribution))

    return rows


def cumulative_contribution(rows: list[Contribution], instrument_id: str) -> Decimal:
    return sum((r.contribution for r in rows if r.instrument_id == instrument_id), Decimal(0))
