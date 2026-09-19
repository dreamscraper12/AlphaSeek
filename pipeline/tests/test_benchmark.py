from datetime import date
from decimal import Decimal

from portfolio.benchmark import (
    Distribution,
    ivv_total_return_series,
    shadow_benchmark_series,
)
from portfolio.sources import PriceQuote


class _FixedPriceSource:
    def __init__(self, prices: dict[date, Decimal]) -> None:
        self._prices = prices

    def get_price(self, instrument_id, as_of):
        price = self._prices.get(as_of)
        if price is None:
            return None
        return PriceQuote(price=price, currency="AUD", as_of=as_of)


def test_total_return_index_chains_price_returns_with_no_distribution():
    # Previous close (a Friday) is found via carry-forward from the Sunday
    # immediately before `start`.
    prices = _FixedPriceSource(
        {
            date(2026, 1, 2): Decimal("100"),
            date(2026, 1, 5): Decimal("105"),
            date(2026, 1, 6): Decimal("110"),
        }
    )
    series = ivv_total_return_series(date(2026, 1, 5), date(2026, 1, 6), prices, [])

    assert [p.date for p in series] == [date(2026, 1, 5), date(2026, 1, 6)]
    assert series[0].index == Decimal("10500")  # 100 -> 105 is +5%
    assert series[1].index == Decimal("11000")  # 105 -> 110 is +4.7619...%


def test_distribution_on_the_ex_date_is_added_back_before_computing_return():
    prices = _FixedPriceSource(
        {
            date(2026, 1, 2): Decimal("100"),
            date(2026, 1, 5): Decimal("105"),
            date(2026, 1, 6): Decimal("110"),
        }
    )
    distributions = [
        Distribution(
            ex_date=date(2026, 1, 6),
            amount_per_unit=Decimal("2"),
            currency="AUD",
            source="iShares distribution history",
        )
    ]
    series = ivv_total_return_series(date(2026, 1, 5), date(2026, 1, 6), prices, distributions)

    # (110 + 2) / 105 - 1 = 6.666...%, vs 4.7619% without the distribution.
    assert series[1].index == Decimal("11200")


def test_missing_ivv_price_with_no_fallback_raises():
    prices = _FixedPriceSource({})
    try:
        ivv_total_return_series(date(2026, 1, 5), date(2026, 1, 6), prices, [])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_shadow_benchmark_inception_deposit_tracks_the_index_from_10000():
    from portfolio.metrics import IndexPoint

    benchmark_series = [
        IndexPoint(date(2026, 1, 5), Decimal("10500")),
        IndexPoint(date(2026, 1, 6), Decimal("11000")),
    ]
    flows = {date(2026, 1, 5): Decimal("10000")}

    shadow = shadow_benchmark_series(flows, benchmark_series, inception_date=date(2026, 1, 5))

    assert shadow[0].value_aud == Decimal("10500")  # 10000 * 10500/10000
    assert shadow[1].value_aud == Decimal("11000")  # 10000 * 11000/10000


def test_shadow_benchmark_later_flow_lands_at_end_of_day_with_no_same_day_return():
    from portfolio.metrics import IndexPoint

    benchmark_series = [
        IndexPoint(date(2026, 1, 5), Decimal("10500")),
        IndexPoint(date(2026, 1, 6), Decimal("11000")),
    ]
    flows = {date(2026, 1, 5): Decimal("10000"), date(2026, 1, 6): Decimal("1000")}

    shadow = shadow_benchmark_series(flows, benchmark_series, inception_date=date(2026, 1, 5))

    assert shadow[0].value_aud == Decimal("10500")  # the Jan-6 flow hasn't happened yet
    # Inception leg grows to 11000; the new 1000 arrives at Jan 6's own
    # close, so it contributes exactly 1000, not 1000 scaled by a return.
    assert shadow[1].value_aud == Decimal("12000")
