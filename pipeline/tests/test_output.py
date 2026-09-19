import json
from datetime import date, timedelta
from decimal import Decimal

import pytest

from portfolio.benchmark import ShadowPoint
from portfolio.engine import NavPoint
from portfolio.metrics import IndexPoint
from portfolio.output import benchmark_daily_json, metrics_json, nav_daily_json, status_json, write_json
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


def test_benchmark_daily_json_pairs_shadow_dollars_with_the_index():
    benchmark_series = [
        IndexPoint(date(2026, 1, 5), Decimal("10500")),
        IndexPoint(date(2026, 1, 6), Decimal("11000")),
    ]
    shadow_series = [
        ShadowPoint(date(2026, 1, 5), Decimal("10500")),
        ShadowPoint(date(2026, 1, 6), Decimal("11000")),
    ]
    rows = benchmark_daily_json(shadow_series, benchmark_series)
    assert rows == [
        {"date": "2026-01-05", "nav": 10500.0, "index": 10500.0},
        {"date": "2026-01-06", "nav": 11000.0, "index": 11000.0},
    ]


def test_metrics_json_is_null_when_either_series_is_empty():
    series = [IndexPoint(date(2026, 1, 5), Decimal("10000"))]
    assert metrics_json([], series) == {"portfolio": None, "benchmark": None}
    assert metrics_json(series, []) == {"portfolio": None, "benchmark": None}


def test_metrics_json_shape_with_a_short_series():
    base = date(2026, 1, 5)
    portfolio_series = [
        IndexPoint(base + timedelta(days=i), idx)
        for i, idx in enumerate([Decimal("10000"), Decimal("10500"), Decimal("10200")])
    ]
    benchmark_series = [
        IndexPoint(base + timedelta(days=i), idx)
        for i, idx in enumerate([Decimal("10000"), Decimal("10100"), Decimal("10050")])
    ]

    result = metrics_json(portfolio_series, benchmark_series)

    assert result["portfolio"]["returns"]["since_inception"] == pytest.approx(0.02)
    assert result["portfolio"]["current_drawdown"] == pytest.approx((10200 / 10500) - 1)
    # Fewer than 60 paired observations: beta/correlation aren't reported.
    assert result["portfolio"]["beta"] is None
    assert result["portfolio"]["correlation"] is None
    assert result["portfolio"]["excess_return"] == pytest.approx(0.02 - 0.005)
    assert result["benchmark"]["returns"]["since_inception"] == pytest.approx(0.005)
