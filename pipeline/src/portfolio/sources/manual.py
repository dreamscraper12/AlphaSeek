"""Manual marks as a PriceSource — a first-class fallback, not an
afterthought (CLAUDE.md section 8). Used by default for options in Phase 1,
and checked ahead of every provider for any instrument, since a manual mark
always takes precedence over provider data."""

from __future__ import annotations

from datetime import date

from portfolio.ledger import ManualMark
from portfolio.sources import PriceQuote


class ManualMarkSource:
    def __init__(self, marks: list[ManualMark]) -> None:
        self._by_key = {(m.instrument_id, m.date): m for m in marks}

    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        mark = self._by_key.get((instrument_id, as_of))
        if mark is None:
            return None
        return PriceQuote(price=mark.price, currency=mark.currency, as_of=as_of)
