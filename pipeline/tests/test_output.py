import json
from datetime import date
from decimal import Decimal

from portfolio.engine import NavPoint
from portfolio.output import nav_daily_json, status_json, write_json
from portfolio.valuation import DailyValuation, InstrumentValuation


def _valuation(warnings=(), positions=()) -> DailyValuation:
    return DailyValuation(
        date=date(2026, 1, 6),
        nav_aud=Decimal("11650.00"),
        positions=list(positions),
        cash_by_currency={"AUD": Decimal("10000.00")},
        cash_aud=Decimal("10000.00"),
        warnings=list(warnings),
    )


def test_nav_daily_json_matches_the_site_schema():
    series = [
        NavPoint(date=date(2026, 1, 5), nav_aud=Decimal("11500.00"), index=Decimal("10000"), valuation=_valuation()),
        NavPoint(date=date(2026, 1, 6), nav_aud=Decimal("11650.00"), index=Decimal("10130.43"), valuation=_valuation()),
    ]
    rows = nav_daily_json(series)
    assert rows == [
        {"date": "2026-01-05", "nav": 11500.0, "index": 10000.0},
        {"date": "2026-01-06", "nav": 11650.0, "index": 10130.43},
    ]


def test_status_json_reflects_only_the_latest_day():
    stale_position = InstrumentValuation(
        instrument_id="TEST:AAA", quantity=Decimal("10"), price=Decimal("100"),
        currency="USD", price_as_of=date(2026, 1, 2), stale_business_days=4,
        market_value_local=Decimal("1000"), market_value_aud=Decimal("1500"),
    )
    series = [
        NavPoint(date=date(2026, 1, 5), nav_aud=Decimal("11500"), index=Decimal("10000"),
                  valuation=_valuation(warnings=["an earlier, now-stale warning"])),
        NavPoint(date=date(2026, 1, 6), nav_aud=Decimal("11650"), index=Decimal("10130"),
                  valuation=_valuation(warnings=["today's warning"], positions=[stale_position])),
    ]
    status = status_json(series)
    assert status == {
        "last_valuation_date": "2026-01-06",
        "stale_prices": ["TEST:AAA"],
        "warnings": ["today's warning"],
    }


def test_status_json_empty_series():
    assert status_json([]) == {"last_valuation_date": None, "stale_prices": [], "warnings": []}


def test_write_json_creates_parent_directories(tmp_path):
    target = tmp_path / "nested" / "nav_daily.json"
    write_json(target, [{"date": "2026-01-05", "nav": 1.0, "index": 2.0}])
    assert json.loads(target.read_text(encoding="utf-8")) == [{"date": "2026-01-05", "nav": 1.0, "index": 2.0}]
