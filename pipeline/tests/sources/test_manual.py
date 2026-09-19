from datetime import date
from decimal import Decimal

from portfolio.ledger import ManualMark
from portfolio.sources.manual import ManualMarkSource


def test_returns_the_mark_for_that_instrument_and_date():
    mark = ManualMark(
        date=date(2026, 1, 5),
        instrument_id="OPT:NASDAQ:AAA:2026-12-18:C:250",
        price=Decimal("3.20"),
        currency="USD",
        source="broker screenshot",
        reason="No public quote for this option.",
    )
    source = ManualMarkSource([mark])

    quote = source.get_price("OPT:NASDAQ:AAA:2026-12-18:C:250", date(2026, 1, 5))
    assert quote is not None
    assert quote.price == Decimal("3.20")


def test_returns_none_when_no_mark_exists():
    source = ManualMarkSource([])
    assert source.get_price("OPT:NASDAQ:AAA:2026-12-18:C:250", date(2026, 1, 5)) is None
