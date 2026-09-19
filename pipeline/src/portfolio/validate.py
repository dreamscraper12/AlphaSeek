"""Structural ledger checks that don't require priced valuation. See CLAUDE.md
section 11. Price-dependent checks (negative cash, stale prices, NAV jumps)
live in valuation.py once a price source is chosen."""

from __future__ import annotations

from decimal import Decimal

from portfolio.ledger import Ledger


class ValidationError(Exception):
    pass


def validate_ledger(ledger: Ledger, note_slugs: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    instrument_ids = {i.instrument_id for i in ledger.instruments}
    option_ids = {i.instrument_id for i in ledger.instruments if i.type == "option"}

    seen_trade_ids: set[str] = set()
    for t in ledger.trades:
        if t.trade_id in seen_trade_ids:
            errors.append(f"duplicate trade_id: {t.trade_id}")
        seen_trade_ids.add(t.trade_id)
        if t.instrument_id not in instrument_ids:
            errors.append(f"trade {t.trade_id} references unknown instrument_id: {t.instrument_id}")
        if note_slugs is not None and t.note_slug is not None and t.note_slug not in note_slugs:
            errors.append(f"trade {t.trade_id} references unknown note_slug: {t.note_slug}")

    for c in ledger.cashflows:
        if c.instrument_id is not None and c.instrument_id not in instrument_ids:
            errors.append(f"cashflow on {c.date} references unknown instrument_id: {c.instrument_id}")

    for e in ledger.events:
        if e.instrument_id not in instrument_ids:
            errors.append(f"event on {e.date} references unknown instrument_id: {e.instrument_id}")

    for m in ledger.manual_marks:
        if m.instrument_id not in instrument_ids:
            errors.append(f"manual mark on {m.date} references unknown instrument_id: {m.instrument_id}")

    running_quantity: dict[str, Decimal] = {}
    for t in sorted(ledger.trades, key=lambda t: t.executed_at):
        delta = t.quantity if t.side == "BUY" else -t.quantity
        running_quantity[t.instrument_id] = running_quantity.get(t.instrument_id, Decimal(0)) + delta
        if running_quantity[t.instrument_id] < 0 and t.instrument_id not in option_ids:
            errors.append(f"short position in non-option instrument: {t.instrument_id}")

    return errors
