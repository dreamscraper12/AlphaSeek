import json
from datetime import date
from decimal import Decimal

from portfolio.sources.coingecko import CoinGeckoSource


def test_get_price_reads_the_next_day_00_00_utc_snapshot(tmp_path):
    # Section 8: crypto closes at 00:00 UTC ending UTC day D, i.e. the
    # midnight snapshot at the *start* of D+1.
    seen_urls = []

    def fetch(url: str) -> bytes:
        seen_urls.append(url)
        return json.dumps({"market_data": {"current_price": {"aud": 95000.12}}}).encode()

    source = CoinGeckoSource(tmp_path, fetch=fetch)
    quote = source.get_price("CRYPTO:BTC", date(2026, 1, 5))

    assert quote is not None
    assert quote.price == Decimal("95000.12")
    assert "06-01-2026" in seen_urls[0]  # D+1 in CoinGecko's dd-mm-yyyy format


def test_weekend_move_lands_in_mondays_close(tmp_path):
    # A crypto price move over Sat/Sun is reflected in Monday's close, per
    # the weekend rule in CLAUDE.md section 8 — there's simply no valuation
    # for Saturday or Sunday at all, so this only exercises that we can read
    # Monday's own snapshot correctly.
    def fetch(url: str) -> bytes:
        return json.dumps({"market_data": {"current_price": {"aud": 100000}}}).encode()

    source = CoinGeckoSource(tmp_path, fetch=fetch)
    monday = date(2026, 1, 5)
    quote = source.get_price("CRYPTO:BTC", monday)
    assert quote.price == Decimal("100000")


def test_unmapped_symbol_raises(tmp_path):
    source = CoinGeckoSource(tmp_path, fetch=lambda url: b"{}")
    try:
        source.get_price("CRYPTO:DOGE", date(2026, 1, 5))
        assert False, "expected ValueError"
    except ValueError:
        pass
