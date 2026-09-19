from datetime import date
from decimal import Decimal

from portfolio.ledger import Cashflow, Event, FxConversion, Instrument, Ledger, Trade
from portfolio.positions import build_positions

AAA = Instrument(
    instrument_id="TEST:AAA",
    type="equity",
    name="Test Company AAA",
    exchange="NASDAQ",
    currency="USD",
    price_source="manual",
)

CALL_OPTION = Instrument(
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

PUT_OPTION = Instrument(
    instrument_id="OPT:TEST:AAA:2026-06-19:P:80",
    type="option",
    name="AAA Jun-26 80 Put",
    exchange="NASDAQ",
    currency="USD",
    underlying_id="TEST:AAA",
    expiry=date(2026, 6, 19),
    right="P",
    strike=Decimal("80"),
    multiplier=Decimal("100"),
    exercise_style="american",
    price_source="manual",
)


def _ledger(**overrides) -> Ledger:
    defaults = dict(
        instruments=[AAA, CALL_OPTION, PUT_OPTION],
        trades=[],
        fx=[],
        cashflows=[],
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


def test_buy_reduces_cash_by_price_times_quantity_plus_fees():
    ledger = _ledger(
        trades=[_trade(quantity=Decimal("10"), price=Decimal("100.00"), fees=Decimal("5.00"))]
    )
    positions = build_positions(ledger, date(2026, 1, 5))

    assert positions.quantities["TEST:AAA"] == Decimal("10")
    assert positions.cash["USD"] == Decimal("-1005.00")


def test_fx_conversion_moves_cash_and_charges_fees_in_their_own_currency():
    # Convert 1000 USD to 1500 AUD at a market rate that would give 1520 AUD;
    # the 20 AUD conversion cost falls out of comparing the two.
    fx = FxConversion(
        converted_at="2026-01-05T10:00:00+11:00",
        from_currency="USD",
        from_amount=Decimal("1000.00"),
        to_currency="AUD",
        to_amount=Decimal("1500.00"),
        fees=Decimal("5.00"),
        fees_currency="AUD",
    )
    ledger = _ledger(fx=[fx])
    positions = build_positions(ledger, date(2026, 1, 5))

    assert positions.cash["USD"] == Decimal("-1000.00")
    assert positions.cash["AUD"] == Decimal("1495.00")  # 1500 credited, less 5 in fees


def test_dividend_and_withholding_tax_both_move_cash():
    ledger = _ledger(
        cashflows=[
            Cashflow(
                date=date(2026, 2, 1), type="DIVIDEND", amount=Decimal("100.00"),
                currency="USD", instrument_id="TEST:AAA", memo="Q1 dividend",
            ),
            Cashflow(
                date=date(2026, 2, 1), type="WITHHOLDING_TAX", amount=Decimal("15.00"),
                currency="USD", instrument_id="TEST:AAA", memo="US withholding",
            ),
        ]
    )
    positions = build_positions(ledger, date(2026, 2, 1))
    assert positions.cash["USD"] == Decimal("85.00")


def test_stock_split_multiplies_quantity():
    ledger = _ledger(
        trades=[_trade(quantity=Decimal("10"))],
        events=[
            Event(
                date=date(2026, 3, 1), instrument_id="TEST:AAA", type="SPLIT",
                details='{"ratio": "4:1"}', memo="4-for-1 split",
            )
        ],
    )
    positions = build_positions(ledger, date(2026, 3, 1))
    assert positions.quantities["TEST:AAA"] == Decimal("40")


def test_long_option_expiring_worthless_zeroes_the_position_with_no_cash_effect():
    ledger = _ledger(
        trades=[
            _trade(
                instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
                quantity=Decimal("1"),
                price=Decimal("2.50"),
                fees=Decimal("1.00"),
            )
        ],
        events=[
            Event(
                date=date(2026, 6, 19), instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
                type="OPTION_EXPIRED", details="{}", memo="Expired worthless.",
            )
        ],
    )
    positions = build_positions(ledger, date(2026, 6, 19))

    assert positions.quantities["OPT:TEST:AAA:2026-06-19:C:120"] == Decimal("0")
    # Only the original premium and fee were ever paid; expiry itself moves no cash.
    assert positions.cash["USD"] == Decimal("-251.00")


def test_short_call_assigned_sells_the_underlying_and_credits_strike_cash():
    ledger = _ledger(
        trades=[
            _trade(
                instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
                side="SELL",
                quantity=Decimal("1"),
                price=Decimal("2.50"),
            ),
        ],
        events=[
            Event(
                date=date(2026, 6, 19), instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
                type="OPTION_ASSIGNED", details="{}", memo="Assigned at expiry.",
            )
        ],
    )
    positions = build_positions(ledger, date(2026, 6, 19))

    # 100 shares delivered at the 120 strike.
    assert positions.quantities["TEST:AAA"] == Decimal("-100")
    assert positions.quantities["OPT:TEST:AAA:2026-06-19:C:120"] == Decimal("0")
    # Premium received (250) plus strike proceeds (120 * 100 = 12000).
    assert positions.cash["USD"] == Decimal("12250.00")


def test_short_put_assigned_buys_the_underlying_and_debits_strike_cash():
    ledger = _ledger(
        trades=[
            _trade(
                instrument_id="OPT:TEST:AAA:2026-06-19:P:80",
                side="SELL",
                quantity=Decimal("1"),
                price=Decimal("1.00"),
            ),
        ],
        events=[
            Event(
                date=date(2026, 6, 19), instrument_id="OPT:TEST:AAA:2026-06-19:P:80",
                type="OPTION_ASSIGNED", details="{}", memo="Assigned at expiry.",
            )
        ],
    )
    positions = build_positions(ledger, date(2026, 6, 19))

    assert positions.quantities["TEST:AAA"] == Decimal("100")
    assert positions.quantities["OPT:TEST:AAA:2026-06-19:P:80"] == Decimal("0")
    # Premium received (100) less strike paid (80 * 100 = 8000).
    assert positions.cash["USD"] == Decimal("-7900.00")
