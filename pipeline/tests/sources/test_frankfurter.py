import json
from datetime import date
from decimal import Decimal

from portfolio.sources.frankfurter import FrankfurterFxSource


def test_get_rate_parses_a_range_response(tmp_path):
    payload = {
        "rates": {
            "2026-01-05": {"AUD": 1.50},
            "2026-01-06": {"AUD": 1.51},
        }
    }
    source = FrankfurterFxSource(tmp_path, fetch=lambda url: json.dumps(payload).encode())

    rate = source.get_rate("USD", "AUD", date(2026, 1, 5))
    assert rate == Decimal("1.50")


def test_same_currency_is_always_rate_one(tmp_path):
    source = FrankfurterFxSource(tmp_path, fetch=lambda url: (_ for _ in ()).throw(AssertionError("no fetch")))
    assert source.get_rate("AUD", "AUD", date(2026, 1, 5)) == Decimal(1)


def test_weekend_gap_returns_none_so_valuation_can_carry_forward(tmp_path):
    # ECB doesn't publish weekend rates; the response simply omits them.
    payload = {"rates": {"2026-01-05": {"AUD": 1.50}}}
    source = FrankfurterFxSource(tmp_path, fetch=lambda url: json.dumps(payload).encode())

    assert source.get_rate("USD", "AUD", date(2026, 1, 5)) == Decimal("1.50")
    assert source.get_rate("USD", "AUD", date(2026, 1, 3)) is None  # a Saturday, absent from the response
