from decimal import Decimal

from portfolio.ledger import Instrument, Ledger, Trade
from portfolio.validate import validate_ledger

AAA = Instrument(
    instrument_id="TEST:AAA",
    type="equity",
    name="Test Company AAA",
    exchange="NASDAQ",
    currency="USD",
    price_source="manual",
)


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


def _empty_ledger(instruments=None, trades=None) -> Ledger:
    return Ledger(
        instruments=instruments or [AAA],
        trades=trades or [],
        fx=[],
        cashflows=[],
        events=[],
        manual_marks=[],
        corrections=[],
    )


def test_valid_ledger_has_no_errors():
    ledger = _empty_ledger(trades=[_trade()])
    assert validate_ledger(ledger) == []


def test_duplicate_trade_id_is_an_error():
    ledger = _empty_ledger(trades=[_trade(trade_id="T1"), _trade(trade_id="T1")])
    errors = validate_ledger(ledger)
    assert any("duplicate trade_id" in e for e in errors)


def test_unknown_instrument_id_is_an_error():
    ledger = _empty_ledger(trades=[_trade(instrument_id="TEST:ZZZ")])
    errors = validate_ledger(ledger)
    assert any("unknown instrument_id" in e for e in errors)


def test_short_position_in_non_option_is_an_error():
    ledger = _empty_ledger(trades=[_trade(side="SELL", quantity=Decimal("5"))])
    errors = validate_ledger(ledger)
    assert any("short position in non-option" in e for e in errors)
