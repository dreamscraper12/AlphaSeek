"""Frankfurter (ECB reference rates) adapter for FX (CLAUDE.md section 3,
decision log 2026-09-19). Free, keyless, no signup. ECB only publishes rates
on business days, so weekends and ECB holidays are simply absent from the
response; valuation.py is responsible for carrying the last rate forward."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from portfolio.sources.cache import PriceCache
from portfolio.sources.http import Fetcher, fetch_json, urlopen_fetcher


class FrankfurterFxSource:
    def __init__(self, cache_dir: Path, fetch: Fetcher = urlopen_fetcher) -> None:
        self._cache = PriceCache(cache_dir, "frankfurter")
        self._fetch = fetch

    def get_rate(self, from_currency: str, to_currency: str, as_of: date) -> Decimal | None:
        if from_currency == to_currency:
            return Decimal(1)
        key = f"{from_currency}{to_currency}"
        cached = self._cache.load(key)
        if as_of not in cached:
            self._refresh(key, from_currency, to_currency, as_of)
            cached = self._cache.load(key)
        hit = cached.get(as_of)
        return hit[0] if hit else None

    def _refresh(self, key: str, from_currency: str, to_currency: str, as_of: date) -> None:
        start = as_of.replace(day=1)
        url = (
            f"https://api.frankfurter.dev/v1/{start.isoformat()}..{as_of.isoformat()}"
            f"?base={from_currency}&symbols={to_currency}"
        )
        payload = fetch_json(url, self._fetch)
        rows: dict[date, tuple[Decimal, str]] = {}
        for d_str, rates in payload.get("rates", {}).items():
            rate = rates.get(to_currency)
            if rate is not None:
                rows[date.fromisoformat(d_str)] = (Decimal(str(rate)), to_currency)
        self._cache.save(key, rows)
