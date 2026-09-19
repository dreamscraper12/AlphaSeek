from datetime import date
from decimal import Decimal

import pytest

from portfolio.ledger import Cashflow, Instrument, Ledger, Trade
from portfolio.sources import PriceQuote
from portfolio.valuation import value_day

AAA = Instrument(
    instrument_id="TEST:AAA",
    type="equity",
    name="Test Company AAA",
    exchange="NASDAQ",
    currency="USD",
    price_source="manual",
)

SHORT_CALL = Instrument(
    instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
    type="option",
    name="AAA Jun-26 120 Call",
    exchange="NASDAQ",
    currency="USD",
    underlying_id="TEST:AAA",
    expiry=date(2026, 6, 19),
    right="C",
    strike=Decimal("120"),
    multiplier=Decimal("100"),
    exercise_style="american",
    price_source="manual",
)


class _FixedPriceSource:
    def __init__(self, prices: dict[tuple[str, date], Decimal], currency: str = "USD") -> None:
        self._prices = prices
        self._currency = currency

    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        price = self._prices.get((instrument_id, as_of))
        if price is None:
            return None
        return PriceQuote(price=price, currency=self._currency, as_of=as_of)


class _FixedFxSource:
    def __init__(self, rate: Decimal = Decimal("1.5")) -> None:
        self._rate = rate

    def get_rate(self, from_currency: str, to_currency: str, as_of: date) -> Decimal | None:
        if from_currency == to_currency:
            return Decimal(1)
        return self._rate


def _ledger(**overrides) -> Ledger:
    defaults = dict(
        instruments=[AAA, SHORT_CALL],
        trades=[],
        fx=[],
        cashflows=[
            Cashflow(date=date(2026, 1, 1), type="DEPOSIT", amount=Decimal("20000.00"), currency="AUD"),
            Cashflow(date=date(2026, 1, 1), type="DEPOSIT", amount=Decimal("5000.00"), currency="USD"),
        ],
        events=[],
        manual_marks=[],
        corrections=[],
    )
    defaults.update(overrides)
    return Ledger(**defaults)


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


def test_nav_sums_positions_and_cash_converted_to_aud():
    ledger = _ledger(trades=[_trade()])
    prices = _FixedPriceSource({("TEST:AAA", date(2026, 1, 6)): Decimal("110.00")})
    fx = _FixedFxSource(Decimal("1.5"))

    result = value_day(ledger, date(2026, 1, 6), prices, fx)

    # 10 shares * 110 USD * 1.5 = 1650 AUD of equity.
    assert result.positions[0].market_value_aud == Decimal("1650.00")
    # Cash: 20000 AUD, plus (5000 USD deposit - 1000 USD spent) converted at 1.5.
    assert result.cash_aud == Decimal("20000.00") + Decimal("4000.00") * Decimal("1.5")
    assert result.nav_aud == result.positions[0].market_value_aud + result.cash_aud


def test_short_option_carries_negative_market_value():
    ledger = _ledger(
        trades=[
            _trade(
                instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
                side="SELL",
                quantity=Decimal("1"),
                price=Decimal("2.50"),
            )
        ]
    )
    prices = _FixedPriceSource(
        {("OPT:TEST:AAA:2026-06-19:C:120", date(2026, 1, 6)): Decimal("5.00")}
    )
    fx = _FixedFxSource(Decimal("1.5"))

    result = value_day(ledger, date(2026, 1, 6), prices, fx)
    option_valuation = next(p for p in result.positions if p.instrument_id.startswith("OPT:"))

    # Short 1 contract * 100 multiplier * $5.00 = -$500 USD, i.e. it now costs
    # more to buy back than the premium collected.
    assert option_valuation.market_value_local == Decimal("-500.00")
    assert option_valuation.market_value_aud == Decimal("-750.00")


def test_stale_price_is_carried_forward_and_flagged_over_the_threshold():
    ledger = _ledger(trades=[_trade()])
    # Last real quote is 6 calendar (4 business) days before the valuation date.
    prices = _FixedPriceSource({("TEST:AAA", date(2026, 1, 2)): Decimal("100.00")})
    fx = _FixedFxSource(Decimal("1.5"))

    result = value_day(ledger, date(2026, 1, 8), prices, fx)

    position = result.positions[0]
    assert position.price == Decimal("100.00")
    assert position.price_as_of == date(2026, 1, 2)
    assert position.stale_business_days > 3
    assert any("stale" in w for w in result.warnings)


def test_missing_price_with_no_fallback_raises():
    ledger = _ledger(trades=[_trade()])
    prices = _FixedPriceSource({})
    fx = _FixedFxSource()

    with pytest.raises(ValueError, match="missing price"):
        value_day(ledger, date(2026, 1, 6), prices, fx)


def test_negative_cash_raises():
    ledger = _ledger(
        cashflows=[
            Cashflow(date=date(2026, 1, 1), type="WITHDRAWAL", amount=Decimal("50000.00"), currency="AUD")
        ]
    )
    prices = _FixedPriceSource({})
    fx = _FixedFxSource()

    with pytest.raises(ValueError, match="negative cash"):
        value_day(ledger, date(2026, 1, 6), prices, fx)
