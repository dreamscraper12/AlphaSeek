"""Price and FX source adapter interfaces. Each instrument type, or an
individual instrument via its price_source field, can be backed by a
different adapter. See CLAUDE.md section 3 (decision log 2026-09-19) for the
chosen providers: Twelve Data (equities/ETFs), Frankfurter (FX), CoinGecko
(crypto), and manual marks (options, and as a universal override — see
section 8, "Precedence: manual mark over provider data")."""

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


class FxRateSource(Protocol):
    def get_rate(self, from_currency: str, to_currency: str, as_of: date) -> Decimal | None:
        """Return the from_currency -> to_currency rate on as_of, or None if unavailable."""
        ...
