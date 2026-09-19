"""Price source adapter interface. Each instrument type, or an individual
instrument via its price_source field, can be backed by a different adapter.
No concrete adapter is chosen yet — see the open decisions in CLAUDE.md."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol


class PriceQuote:
    def __init__(self, price: Decimal, currency: str, as_of: date, stale: bool = False) -> None:
        self.price = price
        self.currency = currency
        self.as_of = as_of
        self.stale = stale


class PriceSource(Protocol):
    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        """Return the close price for instrument_id on as_of, or None if unavailable."""
        ...
