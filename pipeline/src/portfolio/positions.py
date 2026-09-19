"""Reconstruct open positions and cash balances from the ledger as of a
date. Only running totals matter for a point-in-time snapshot, except for
option exercise and assignment, which need the position size at that moment
— so trades and FX conversions are applied in execution order, cashflows are
applied same-day (order doesn't matter, they only move cash), and events are
applied last, since expiry/exercise/assignment happen at the close, after
that day's trades. See CLAUDE.md section 7 (ledger data model)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from portfolio.ledger import Event, Instrument, Ledger

_CASHFLOW_SIGN: dict[str, int] = {
    "DEPOSIT": 1,
    "DIVIDEND": 1,
    "INTEREST": 1,
    "WITHDRAWAL": -1,
    "FEE": -1,
    "WITHHOLDING_TAX": -1,
}


@dataclass
class Positions:
    quantities: dict[str, Decimal] = field(default_factory=dict)
    cash: dict[str, Decimal] = field(default_factory=dict)

    def add_quantity(self, instrument_id: str, delta: Decimal) -> None:
        self.quantities[instrument_id] = self.quantities.get(instrument_id, Decimal(0)) + delta

    def add_cash(self, currency: str, delta: Decimal) -> None:
        self.cash[currency] = self.cash.get(currency, Decimal(0)) + delta


def _parse_split_ratio(details: str) -> Decimal:
    """details is e.g. {"ratio": "4:1"} for a 4-for-1 split: each old share
    becomes 4 new shares, so the quantity multiplier is new/old = 4."""
    new_str, _, old_str = json.loads(details)["ratio"].partition(":")
    return Decimal(new_str) / Decimal(old_str)


def _apply_event(positions: Positions, event: Event, instruments_by_id: dict[str, Instrument]) -> None:
    if event.type == "SPLIT":
        factor = _parse_split_ratio(event.details)
        current = positions.quantities.get(event.instrument_id, Decimal(0))
        positions.quantities[event.instrument_id] = current * factor
        return

    if event.type == "OPTION_EXPIRED":
        positions.quantities[event.instrument_id] = Decimal(0)
        return

    if event.type in ("OPTION_EXERCISED", "OPTION_ASSIGNED"):
        instrument = instruments_by_id[event.instrument_id]
        opt_qty = positions.quantities.get(event.instrument_id, Decimal(0))
        shares = abs(opt_qty) * instrument.multiplier
        cash_amount = instrument.strike * instrument.multiplier * abs(opt_qty)
        underlying_id = instrument.underlying_id
        underlying_currency = instruments_by_id[underlying_id].currency

        # Long call exercised or short put assigned: the owner buys the
        # underlying at strike. Long put exercised or short call assigned:
        # the owner sells the underlying at strike.
        buys_underlying = (instrument.right == "C" and opt_qty > 0) or (
            instrument.right == "P" and opt_qty < 0
        )
        positions.add_quantity(underlying_id, shares if buys_underlying else -shares)
        positions.add_cash(underlying_currency, -cash_amount if buys_underlying else cash_amount)
        positions.quantities[event.instrument_id] = Decimal(0)
        return

    if event.type == "SYMBOL_CHANGE":
        new_id = json.loads(event.details)["new_id"]
        qty = positions.quantities.pop(event.instrument_id, Decimal(0))
        positions.add_quantity(new_id, qty)
        return

    # OTHER: memo only, no position or cash effect.


def build_positions(ledger: Ledger, as_of: date) -> Positions:
    positions = Positions()
    instruments_by_id = {i.instrument_id: i for i in ledger.instruments}

    for t in sorted(ledger.trades, key=lambda t: t.executed_at):
        if t.executed_at.date() > as_of:
            continue
        instrument = instruments_by_id[t.instrument_id]
        signed_qty = t.quantity if t.side == "BUY" else -t.quantity
        positions.add_quantity(t.instrument_id, signed_qty)

        multiplier = instrument.multiplier if instrument.type == "option" else Decimal(1)
        gross = t.quantity * t.price * multiplier
        positions.add_cash(instrument.currency, -gross if t.side == "BUY" else gross)
        positions.add_cash(t.fees_currency, -t.fees)

    for fx in sorted(ledger.fx, key=lambda f: f.converted_at):
        if fx.converted_at.date() > as_of:
            continue
        positions.add_cash(fx.from_currency, -fx.from_amount)
        positions.add_cash(fx.to_currency, fx.to_amount)
        positions.add_cash(fx.fees_currency, -fx.fees)

    for c in ledger.cashflows:
        if c.date > as_of:
            continue
        positions.add_cash(c.currency, _CASHFLOW_SIGN[c.type] * c.amount)

    for e in sorted(ledger.events, key=lambda e: e.date):
        if e.date > as_of:
            continue
        _apply_event(positions, e, instruments_by_id)

    return positions
