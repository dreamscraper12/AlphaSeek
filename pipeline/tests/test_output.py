import json
from datetime import date, timedelta
from decimal import Decimal

import pytest

from portfolio.attribution import CASH_AND_FX_LINE, Contribution
from portfolio.benchmark import ShadowPoint
from portfolio.cost_basis import CostBasis
from portfolio.engine import NavPoint
from portfolio.ledger import Instrument, Ledger, Trade
from portfolio.metrics import IndexPoint
from portfolio.output import (
    attribution_json,
    benchmark_daily_json,
    closed_positions_json,
    holdings_json,
    metrics_json,
    nav_daily_json,
    status_json,
    trades_json,
    write_json,
)
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
        "cash_by_currency": {"AUD": 10000.0},
    }


def test_status_json_empty_series():
    assert status_json([]) == {
        "last_valuation_date": None, "stale_prices": [], "warnings": [], "cash_by_currency": {},
    }


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


AAA = Instrument(
    instrument_id="TEST:AAA", type="equity", name="Test Company AAA",
    exchange="NASDAQ", currency="USD", price_source="manual",
)


def _trade(**overrides) -> Trade:
    defaults = dict(
        trade_id="T1", executed_at="2026-01-05T10:00:00+11:00", instrument_id="TEST:AAA",
        side="BUY", quantity=Decimal("10"), price=Decimal("100.00"), fees=Decimal("0"),
        fees_currency="USD", note_slug="why-i-own-aaa", rationale="Test.",
    )
    defaults.update(overrides)
    return Trade(**defaults)


def _ledger(trades: list[Trade]) -> Ledger:
    return Ledger(instruments=[AAA], trades=trades, fx=[], cashflows=[], events=[], manual_marks=[], corrections=[])


def test_trades_json_is_newest_first():
    ledger = _ledger([
        _trade(trade_id="T1", executed_at="2026-01-05T10:00:00+11:00"),
        _trade(trade_id="T2", executed_at="2026-01-06T10:00:00+11:00"),
    ])
    rows = trades_json(ledger)
    assert [r["trade_id"] for r in rows] == ["T2", "T1"]
    assert rows[0]["note_slug"] == "why-i-own-aaa"
    assert rows[0]["currency"] == "USD"


def test_holdings_json_computes_weight_return_and_contribution():
    ledger = _ledger([_trade()])
    position = InstrumentValuation(
        instrument_id="TEST:AAA", quantity=Decimal("10"), price=Decimal("110"), currency="USD",
        price_as_of=date(2026, 1, 6), stale_business_days=0,
        market_value_local=Decimal("1100"), market_value_aud=Decimal("1650"),  # 110 * 10 * 1.5 FX
    )
    cost_basis = {"TEST:AAA": CostBasis(quantity=Decimal("10"), average_cost_aud=Decimal("150"))}
    attribution_rows = [
        Contribution(date(2026, 1, 6), "TEST:AAA", Decimal("0.01")),
        Contribution(date(2026, 1, 7), "TEST:AAA", Decimal("0.02")),
        Contribution(date(2026, 1, 6), CASH_AND_FX_LINE, Decimal("-0.001")),
    ]

    rows = holdings_json(ledger, Decimal("11650"), [position], cost_basis, attribution_rows)

    assert rows == [
        {
            "instrument_id": "TEST:AAA",
            "type": "equity",
            "weight": pytest.approx(1650 / 11650),
            "average_cost": 150.0,
            "price": 165.0,  # 1650 AUD market value / 10 shares
            "price_as_of": "2026-01-06",
            "return": pytest.approx((165 / 150) - 1),
            "contribution": pytest.approx(0.03),
            "note_slug": "why-i-own-aaa",
        }
    ]


def test_holdings_json_return_is_none_with_zero_cost_basis():
    # A real position can't exist with no cost basis at all, but the return
    # figure must still not divide by zero if this ever comes up.
    ledger = _ledger([])
    position = InstrumentValuation(
        instrument_id="TEST:AAA", quantity=Decimal("10"), price=Decimal("110"), currency="USD",
        price_as_of=date(2026, 1, 6), stale_business_days=0,
        market_value_local=Decimal("1100"), market_value_aud=Decimal("1650"),
    )
    rows = holdings_json(ledger, Decimal("11650"), [position], {}, [])
    assert rows[0]["average_cost"] == 0.0
    assert rows[0]["return"] is None


def test_closed_positions_json_only_includes_fully_closed_instruments():
    ledger = _ledger([_trade()])
    cost_basis = {
        "TEST:AAA": CostBasis(quantity=Decimal("0"), realised_pnl_aud=Decimal("500")),
        "TEST:BBB": CostBasis(quantity=Decimal("5"), realised_pnl_aud=Decimal("0")),  # still open
    }
    rows = closed_positions_json(ledger, cost_basis)
    assert rows == [
        {"instrument_id": "TEST:AAA", "type": "equity", "realised_pnl": 500.0, "note_slug": "why-i-own-aaa"}
    ]


def test_attribution_json_matches_the_contribution_rows():
    rows = [
        Contribution(date(2026, 1, 6), "TEST:AAA", Decimal("0.01")),
        Contribution(date(2026, 1, 6), CASH_AND_FX_LINE, Decimal("-0.001")),
    ]
    assert attribution_json(rows) == [
        {"date": "2026-01-06", "instrument_id": "TEST:AAA", "contribution": 0.01},
        {"date": "2026-01-06", "instrument_id": "CASH_AND_FX", "contribution": -0.001},
    ]
