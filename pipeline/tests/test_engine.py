from datetime import date
from decimal import Decimal

from portfolio.engine import build_nav_series
from portfolio.ledger import Cashflow, Instrument, Ledger, Trade
from portfolio.performance import chain_link, daily_return
from portfolio.sources import PriceQuote

AAA = Instrument(
    instrument_id="TEST:AAA",
    type="equity",
    name="Test Company AAA",
    exchange="NASDAQ",
    currency="USD",
    price_source="manual",
)


class _FixedPriceSource:
    def __init__(self, prices: dict[tuple[str, date], Decimal]) -> None:
        self._prices = prices

    def get_price(self, instrument_id, as_of):
        price = self._prices.get((instrument_id, as_of))
        if price is None:
            return None
        return PriceQuote(price=price, currency="USD", as_of=as_of)


class _FixedFxSource:
    def __init__(self, rate: Decimal = Decimal("1.5")) -> None:
        self._rate = rate

    def get_rate(self, from_currency, to_currency, as_of):
        if from_currency == to_currency:
            return Decimal(1)
        return self._rate


def _trade(**overrides) -> Trade:
    defaults = dict(
        trade_id="T1",
        executed_at="2026-01-05T10:00:00+11:00",
        instrument_id="TEST:AAA",
        side="BUY",
        quantity=Decimal("10"),
        price=Decimal("100.00"),
        fees=Decimal("0"),
        fees_currency="USD",
        rationale="Test.",
    )
    defaults.update(overrides)
    return Trade(**defaults)


def _ledger(**overrides) -> Ledger:
    defaults = dict(
        instruments=[AAA],
        trades=[],
        fx=[],
        cashflows=[],
        events=[],
        manual_marks=[],
        corrections=[],
    )
    defaults.update(overrides)
    return Ledger(**defaults)


def test_no_deposit_means_no_series():
    ledger = _ledger()
    prices = _FixedPriceSource({})
    fx = _FixedFxSource()
    assert build_nav_series(ledger, date(2026, 1, 6), prices, fx) == []


def test_first_day_return_uses_the_deposit_as_the_prior_close():
    # 10000 AUD + 1000 USD deposited on the same day the shares are bought;
    # nothing has moved yet, so day zero's return must be exactly 0.
    ledger = _ledger(
        trades=[_trade()],
        cashflows=[
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("10000.00"), currency="AUD"),
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("1000.00"), currency="USD"),
        ],
    )
    prices = _FixedPriceSource({("TEST:AAA", date(2026, 1, 5)): Decimal("100.00")})
    fx = _FixedFxSource(Decimal("1.5"))

    series = build_nav_series(ledger, date(2026, 1, 5), prices, fx)

    assert len(series) == 1
    assert series[0].nav_aud == Decimal("11500.00")  # 1000 USD shares * 1.5 + 10000 AUD cash
    assert series[0].index == Decimal("10000")


def test_second_day_index_matches_chain_link_of_the_same_daily_return():
    ledger = _ledger(
        trades=[_trade()],
        cashflows=[
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("10000.00"), currency="AUD"),
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("1000.00"), currency="USD"),
        ],
    )
    prices = _FixedPriceSource(
        {
            ("TEST:AAA", date(2026, 1, 5)): Decimal("100.00"),
            ("TEST:AAA", date(2026, 1, 6)): Decimal("110.00"),
        }
    )
    fx = _FixedFxSource(Decimal("1.5"))

    series = build_nav_series(ledger, date(2026, 1, 6), prices, fx)

    assert [p.date for p in series] == [date(2026, 1, 5), date(2026, 1, 6)]
    nav_day1, nav_day2 = series[0].nav_aud, series[1].nav_aud
    assert nav_day2 == Decimal("11650.00")  # 1100 USD shares * 1.5 + 10000 AUD cash

    expected_r0 = daily_return(nav_day1, nav_day1, Decimal(0))
    expected_r1 = daily_return(nav_day2, nav_day1, Decimal(0))
    expected_index = chain_link([expected_r0, expected_r1])

    assert [p.index for p in series] == expected_index


def test_weekends_are_not_valued():
    ledger = _ledger(
        cashflows=[
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("10000.00"), currency="AUD")
        ]
    )
    prices = _FixedPriceSource({})
    fx = _FixedFxSource()

    # 2026-01-05 is a Monday; 2026-01-11 is the following Sunday.
    series = build_nav_series(ledger, date(2026, 1, 11), prices, fx)

    dates = [p.date for p in series]
    assert dates == [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8), date(2026, 1, 9)]
    assert all(p.index == Decimal("10000") for p in series)  # cash only, nothing ever moves
