"""Twelve Data adapter for ASX and US equity/ETF closes (CLAUDE.md section 3,
decision log 2026-09-19). Needs a free API key from twelvedata.com, read from
TWELVE_DATA_API_KEY (a GitHub Actions secret in CI, .env locally — never
committed, per section 2 ground rule 7).

Symbol mapping and the exchange coverage this relies on haven't been
verified against a live API key yet — smoke-test with a real ASX instrument
before trusting this for a real valuation."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

from portfolio.sources import PriceQuote
from portfolio.sources.cache import PriceCache
from portfolio.sources.http import Fetcher, fetch_json, urlopen_fetcher

_EXCHANGE_BY_PREFIX = {
    "ASX": "ASX",
    "NASDAQ": "NASDAQ",
    "NYSE": "NYSE",
}


def _split_symbol(instrument_id: str) -> tuple[str, str]:
    prefix, sep, symbol = instrument_id.partition(":")
    exchange = _EXCHANGE_BY_PREFIX.get(prefix)
    if not sep or exchange is None:
        raise ValueError(f"unsupported exchange prefix for Twelve Data: {instrument_id}")
    return symbol, exchange


class TwelveDataSource:
    def __init__(
        self,
        cache_dir: Path,
        api_key: str | None = None,
        fetch: Fetcher = urlopen_fetcher,
        output_size: int = 90,
    ) -> None:
        self._cache = PriceCache(cache_dir, "twelvedata")
        self._api_key = api_key if api_key is not None else os.environ["TWELVE_DATA_API_KEY"]
        self._fetch = fetch
        self._output_size = output_size

    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        cached = self._cache.load(instrument_id)
        if as_of not in cached:
            self._refresh(instrument_id)
            cached = self._cache.load(instrument_id)
        hit = cached.get(as_of)
        if hit is None:
            return None
        price, currency = hit
        return PriceQuote(price=price, currency=currency, as_of=as_of)

    def _refresh(self, instrument_id: str) -> None:
        symbol, exchange = _split_symbol(instrument_id)
        url = (
            "https://api.twelvedata.com/time_series"
            f"?symbol={symbol}&exchange={exchange}&interval=1day"
            f"&outputsize={self._output_size}&apikey={self._api_key}"
        )
        payload = fetch_json(url, self._fetch)
        if payload.get("status") == "error":
            raise RuntimeError(f"Twelve Data error for {instrument_id}: {payload.get('message')}")
        currency = payload.get("meta", {}).get("currency", "USD")
        rows: dict[date, tuple[Decimal, str]] = {}
        for point in payload.get("values", []):
            d = date.fromisoformat(point["datetime"][:10])
            rows[d] = (Decimal(point["close"]), currency)
        self._cache.save(instrument_id, rows)
