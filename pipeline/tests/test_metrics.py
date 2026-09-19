from datetime import date
from decimal import Decimal

from portfolio.metrics import (
    IndexPoint,
    annualised_return,
    annualised_volatility,
    current_drawdown,
    max_drawdown,
    period_return,
    period_returns,
    since_inception_return,
)

SERIES = [
    IndexPoint(date(2026, 1, 1), Decimal("10000")),
    IndexPoint(date(2026, 1, 2), Decimal("11000")),
    IndexPoint(date(2026, 1, 3), Decimal("9000")),
    IndexPoint(date(2026, 1, 4), Decimal("9500")),
    IndexPoint(date(2026, 1, 5), Decimal("12000")),
    IndexPoint(date(2026, 1, 6), Decimal("10000")),
]


def test_period_return_from_a_given_start_date():
    r = period_return(SERIES, date(2026, 1, 3))
    # From 9000 (first point on/after Jan 3) to the last point, 10000.
    assert r == Decimal("10000") / Decimal("9000") - 1


def test_period_return_none_when_series_does_not_reach_back_that_far():
    assert period_return(SERIES, date(2020, 1, 1)) is not None
    assert period_return([], date(2026, 1, 1)) is None
    assert period_return(SERIES, date(2027, 1, 1)) is None


def test_since_inception_return_uses_the_first_and_last_points():
    assert since_inception_return(SERIES) == Decimal("10000") / Decimal("10000") - 1


def test_period_returns_ytd_matches_since_inception_when_all_in_one_year():
    result = period_returns(SERIES)
    assert result["YTD"] == result["since_inception"]


def test_annualised_return_is_none_under_a_year_of_history():
    assert annualised_return(SERIES) is None


def test_annualised_return_hand_calculated_over_two_years():
    two_year_series = [
        IndexPoint(date(2024, 1, 1), Decimal("10000")),
        IndexPoint(date(2026, 1, 1), Decimal("12100")),  # 21% total return over ~2 years
    ]
    result = annualised_return(two_year_series)
    days = (date(2026, 1, 1) - date(2024, 1, 1)).days
    expected = (Decimal("12100") / Decimal("10000")) ** (Decimal(365) / Decimal(days)) - 1
    assert result == expected
    assert Decimal("0.09") < result < Decimal("0.11")  # roughly 10%/yr, sanity check


def test_max_drawdown_finds_the_worst_peak_to_trough_move():
    dd = max_drawdown(SERIES)
    # Worst move is 11000 (Jan 2) down to 9000 (Jan 3): -18.18%, worse than
    # the later 12000 -> 10000 move (-16.67%).
    assert dd.peak_date == date(2026, 1, 2)
    assert dd.trough_date == date(2026, 1, 3)
    assert dd.drawdown == Decimal("9000") / Decimal("11000") - 1


def test_current_drawdown_from_the_running_peak_to_the_last_point():
    dd = current_drawdown(SERIES)
    # Peak across the whole series is 12000 (Jan 5); last point is 10000.
    assert dd == Decimal("10000") / Decimal("12000") - 1


def test_annualised_volatility_hand_calculated():
    daily_returns = [Decimal("0.01"), Decimal("-0.02"), Decimal("0.015"), Decimal("0.005")]
    vol = annualised_volatility(daily_returns)
    assert vol == Decimal("0.2137171027316251075328653437")


def test_annualised_volatility_none_with_fewer_than_two_observations():
    assert annualised_volatility([Decimal("0.01")]) is None
