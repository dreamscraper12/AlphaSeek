"""Yahoo Finance adapter for ASX closes (CLAUDE.md section 3, decision log
2026-09-20). Twelve Data's free tier excludes the ASX and its cheapest
plan that includes it is US$99/month, which is out of proportion to the
portfolio, so ASX instruments are priced here instead.

This is an undocumented endpoint, not a sanctioned API. It is used because
it answers ordinary requests — nothing is being circumvented, unlike the
bot challenge that ruled out Stooq — but it can change without notice, so
manual marks stay the fallback and the build fails loudly on a missing
price rather than guessing.

Raw `close` is deliberate. Yahoo also returns `adjclose`, which folds
distributions back in; the benchmark adds them separately from iShares'
published history (section 9), so using the adjusted series would count
them twice."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from portfolio.sources import PriceQuote
from portfolio.sources.cache import PriceCache
from portfolio.sources.http import Fetcher, fetch_json, urlopen_fetcher

_SUFFIX_BY_PREFIX = {"ASX": ".AX"}

# Enough that a rebuild with no cache still reaches inception, in one call.
_DEFAULT_RANGE = "5y"

# Yahoo returns float32 artefacts (71.58999633789062 for a 71.59 close).
# Four places clears the noise without touching real precision, including
# for sub-cent ASX listings.
_PRICE_PLACES = 4


def _yahoo_symbol(instrument_id: str) -> str:
    prefix, sep, symbol = instrument_id.partition(":")
    suffix = _SUFFIX_BY_PREFIX.get(prefix)
    if not sep or suffix is None:
        raise ValueError(f"unsupported exchange prefix for Yahoo Finance: {instrument_id}")
    return symbol + suffix


class YahooFinanceSource:
    def __init__(
        self,
        cache_dir: Path,
        fetch: Fetcher = urlopen_fetcher,
        history_range: str = _DEFAULT_RANGE,
    ) -> None:
        self._cache = PriceCache(cache_dir, "yahoo")
        self._fetch = fetch
        self._range = history_range

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
        symbol = _yahoo_symbol(instrument_id)
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?range={self._range}&interval=1d"
        )
        payload = fetch_json(url, self._fetch)

        chart = payload.get("chart") or {}
        if chart.get("error"):
            raise RuntimeError(f"Yahoo Finance error for {instrument_id}: {chart['error']}")
        results = chart.get("result") or []
        if not results:
            return

        result = results[0]
        meta = result.get("meta") or {}
        currency = meta.get("currency") or "AUD"
        gmt_offset = meta.get("gmtoffset") or 0
        timestamps = result.get("timestamp") or []
        quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []

        rows: dict[date, tuple[Decimal, str]] = {}
        for timestamp, close in zip(timestamps, closes):
            if close is None:
                continue
            # Daily bars are stamped at the session open in exchange-local
            # time, so shift by the exchange's offset to recover the date
            # the session belongs to.
            session_date = datetime.fromtimestamp(timestamp + gmt_offset, tz=timezone.utc).date()
            rows[session_date] = (Decimal(str(round(close, _PRICE_PLACES))), currency)

        self._cache.save(instrument_id, rows)
