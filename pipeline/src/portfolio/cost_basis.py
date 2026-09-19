"""Average-cost basis per instrument, in AUD — the simplest cost method,
and per CLAUDE.md section 9, "reported performance doesn't depend on the
cost method," so this only feeds the P&L figures shown on /portfolio, not
anything performance-related.

Handles both long and short positions (options only, per section 11) with
the same logic: a trade that extends the position in its current direction
updates the weighted average; a trade that reduces it realises P&L against
the existing average first, and only opens a new average if it flips all
the way through zero to the other side."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from portfolio.fx import rate_with_carry_forward
from portfolio.ledger import Ledger
from portfolio.sources import FxRateSource


@dataclass
class CostBasis:
    quantity: Decimal = Decimal(0)
    average_cost_aud: Decimal = Decimal(0)  # per unit (per share, or per option contract's share)
    realised_pnl_aud: Decimal = Decimal(0)


def compute_cost_basis(
    ledger: Ledger, as_of: date, fx_source: FxRateSource
) -> dict[str, CostBasis]:
    instruments_by_id = {i.instrument_id: i for i in ledger.instruments}
    basis: dict[str, CostBasis] = {}

    for t in sorted(ledger.trades, key=lambda t: t.executed_at):
        if t.executed_at.date() > as_of:
            continue
        instrument = instruments_by_id[t.instrument_id]
        multiplier = instrument.multiplier if instrument.type == "option" else Decimal(1)
        rate = rate_with_carry_forward(fx_source, instrument.currency, "AUD", t.executed_at.date())
        if rate is None:
            raise ValueError(
                f"missing FX rate {instrument.currency}->AUD on {t.executed_at.date()}, "
                "no fallback available"
            )
        price_aud = t.price * multiplier * rate

        cb = basis.setdefault(t.instrument_id, CostBasis())
        delta = t.quantity if t.side == "BUY" else -t.quantity
        extending = cb.quantity == 0 or (delta > 0) == (cb.quantity > 0)

        if extending:
            total_cost = cb.average_cost_aud * abs(cb.quantity) + price_aud * abs(delta)
            cb.quantity += delta
            cb.average_cost_aud = total_cost / abs(cb.quantity) if cb.quantity != 0 else Decimal(0)
        else:
            closing_qty = min(abs(delta), abs(cb.quantity))
            direction = 1 if cb.quantity > 0 else -1
            cb.realised_pnl_aud += direction * (price_aud - cb.average_cost_aud) * closing_qty
            cb.quantity += delta
            if abs(delta) > closing_qty:
                # Flipped through zero: the remainder opens a fresh position.
                cb.average_cost_aud = price_aud
            elif cb.quantity == 0:
                cb.average_cost_aud = Decimal(0)

    return basis
