from datetime import date
from decimal import Decimal

from portfolio.sources.cache import PriceCache


def test_round_trips_prices_through_disk(tmp_path):
    cache = PriceCache(tmp_path, "testprovider")
    cache.save("TEST:AAA", {date(2026, 1, 5): (Decimal("100.50"), "USD")})

    reloaded = PriceCache(tmp_path, "testprovider")
    assert reloaded.load("TEST:AAA") == {date(2026, 1, 5): (Decimal("100.50"), "USD")}


def test_save_merges_with_existing_rows(tmp_path):
    cache = PriceCache(tmp_path, "testprovider")
    cache.save("TEST:AAA", {date(2026, 1, 5): (Decimal("100.50"), "USD")})
    cache.save("TEST:AAA", {date(2026, 1, 6): (Decimal("101.00"), "USD")})

    rows = cache.load("TEST:AAA")
    assert rows == {
        date(2026, 1, 5): (Decimal("100.50"), "USD"),
        date(2026, 1, 6): (Decimal("101.00"), "USD"),
    }


def test_missing_key_returns_empty_dict(tmp_path):
    cache = PriceCache(tmp_path, "testprovider")
    assert cache.load("TEST:ZZZ") == {}


def test_instrument_id_with_colon_is_a_safe_filename(tmp_path):
    cache = PriceCache(tmp_path, "testprovider")
    cache.save("ASX:BHP", {date(2026, 1, 5): (Decimal("45.00"), "AUD")})
    assert (tmp_path / "prices" / "testprovider" / "ASX_BHP.csv").exists()
