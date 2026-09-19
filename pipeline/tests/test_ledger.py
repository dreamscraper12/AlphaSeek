from decimal import Decimal
from pathlib import Path

from portfolio.ledger import load_ledger

FIXTURES = Path(__file__).parent / "fixtures" / "ledger"


def test_load_ledger_parses_all_files():
    ledger = load_ledger(FIXTURES)

    assert {i.instrument_id for i in ledger.instruments} == {"TEST:AAA", "TEST:BBB"}
    assert len(ledger.trades) == 2
    assert len(ledger.fx) == 0
    assert len(ledger.cashflows) == 1
    assert len(ledger.events) == 0
    assert len(ledger.manual_marks) == 0
    assert len(ledger.corrections) == 0


def test_trade_amounts_are_decimal_not_float():
    ledger = load_ledger(FIXTURES)
    trade = next(t for t in ledger.trades if t.trade_id == "T1")

    assert trade.price == Decimal("100.00")
    assert trade.quantity == Decimal("10")
    assert isinstance(trade.price, Decimal)
