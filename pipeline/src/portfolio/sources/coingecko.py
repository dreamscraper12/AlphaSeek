"""CoinGecko adapter for crypto closes (CLAUDE.md section 3, decision log
2026-09-19). Free public API, no key required. Section 8 defines the crypto
valuation point as "close at 00:00 UTC ending UTC day D" — CoinGecko's
`/history` endpoint snapshots each coin as of 00:00 UTC on the requested
date, so day D's close is the snapshot for D+1. The free tier only serves
history within the last 365 days."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from portfolio.sources import PriceQuote
from portfolio.sources.cache import PriceCache
from portfolio.sources.http import Fetcher, fetch_json, urlopen_fetcher

# Extend as new crypto instruments are added to instruments.csv.
_COIN_ID_BY_SYMBOL = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}


class CoinGeckoSource:
    def __init__(
        self, cache_dir: Path, vs_currency: str = "aud", fetch: Fetcher = urlopen_fetcher
    ) -> None:
        self._cache = PriceCache(cache_dir, "coingecko")
        self._vs_currency = vs_currency
        self._fetch = fetch

    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        cached = self._cache.load(instrument_id)
        if as_of not in cached:
            self._refresh(instrument_id, as_of)
            cached = self._cache.load(instrument_id)
        hit = cached.get(as_of)
        if hit is None:
            return None
        price, currency = hit
        return PriceQuote(price=price, currency=currency, as_of=as_of)

    def _refresh(self, instrument_id: str, as_of: date) -> None:
        _, _, symbol = instrument_id.partition(":")
        coin_id = _COIN_ID_BY_SYMBOL.get(symbol)
        if coin_id is None:
            raise ValueError(f"no CoinGecko coin id mapped for {instrument_id}")
        snapshot_date = as_of + timedelta(days=1)
        url = (
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
            f"?date={snapshot_date.strftime('%d-%m-%Y')}&localization=false"
        )
        payload = fetch_json(url, self._fetch)
        price = payload.get("market_data", {}).get("current_price", {}).get(self._vs_currency)
        if price is None:
            return
        self._cache.save(instrument_id, {as_of: (Decimal(str(price)), self._vs_currency.upper())})
