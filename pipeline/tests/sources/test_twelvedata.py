import json
from datetime import date
from decimal import Decimal

from portfolio.sources.twelvedata import TwelveDataSource


def _fake_fetch(payload: dict):
    def fetch(url: str) -> bytes:
        return json.dumps(payload).encode()

    return fetch


def test_get_price_parses_and_caches_a_time_series(tmp_path):
    payload = {
        "meta": {"symbol": "AAPL", "currency": "USD"},
        "values": [
            {"datetime": "2026-01-06", "close": "101.00"},
            {"datetime": "2026-01-05", "close": "100.00"},
        ],
        "status": "ok",
    }
    source = TwelveDataSource(tmp_path, api_key="test-key", fetch=_fake_fetch(payload))

    quote = source.get_price("NASDAQ:AAPL", date(2026, 1, 5))

    assert quote is not None
    assert quote.price == Decimal("100.00")
    assert quote.currency == "USD"


def test_second_lookup_uses_cache_not_a_second_fetch(tmp_path):
    calls = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        return json.dumps(
            {
                "meta": {"currency": "USD"},
                "values": [{"datetime": "2026-01-05", "close": "100.00"}],
                "status": "ok",
            }
        ).encode()

    source = TwelveDataSource(tmp_path, api_key="test-key", fetch=fetch)
    source.get_price("NASDAQ:AAPL", date(2026, 1, 5))
    source.get_price("NASDAQ:AAPL", date(2026, 1, 5))

    assert len(calls) == 1


def test_unknown_exchange_prefix_raises(tmp_path):
    source = TwelveDataSource(tmp_path, api_key="k", fetch=lambda url: b"{}")
    try:
        source.get_price("CRYPTO:BTC", date(2026, 1, 5))
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_provider_error_status_raises(tmp_path):
    payload = {"status": "error", "message": "bad symbol"}
    source = TwelveDataSource(tmp_path, api_key="test-key", fetch=_fake_fetch(payload))
    try:
        source.get_price("NASDAQ:AAPL", date(2026, 1, 5))
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
