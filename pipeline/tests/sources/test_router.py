from datetime import date
from decimal import Decimal

from portfolio.ledger import Instrument, ManualMark
from portfolio.sources import PriceQuote
from portfolio.sources.manual import ManualMarkSource
from portfolio.sources.router import RoutedPriceSource

AAA = Instrument(
    instrument_id="TEST:AAA",
    type="equity",
    name="Test Company AAA",
    exchange="NASDAQ",
    currency="USD",
    price_source="fake-provider",
)


class _FakeProvider:
    def __init__(self, price: Decimal) -> None:
        self._price = price

    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        return PriceQuote(price=self._price, currency="USD", as_of=as_of)


def test_falls_through_to_the_instrument_provider_with_no_manual_mark():
    router = RoutedPriceSource(
        instruments=[AAA],
        manual=ManualMarkSource([]),
        providers={"fake-provider": _FakeProvider(Decimal("100.00"))},
    )
    quote = router.get_price("TEST:AAA", date(2026, 1, 5))
    assert quote.price == Decimal("100.00")


def test_manual_mark_overrides_the_provider():
    manual = ManualMarkSource(
        [
            ManualMark(
                date=date(2026, 1, 5),
                instrument_id="TEST:AAA",
                price=Decimal("999.00"),
                currency="USD",
                source="owner override",
                reason="Provider price looked wrong.",
            )
        ]
    )
    router = RoutedPriceSource(
        instruments=[AAA],
        manual=manual,
        providers={"fake-provider": _FakeProvider(Decimal("100.00"))},
    )
    quote = router.get_price("TEST:AAA", date(2026, 1, 5))
    assert quote.price == Decimal("999.00")


def test_no_provider_registered_for_price_source_returns_none():
    router = RoutedPriceSource(instruments=[AAA], manual=ManualMarkSource([]), providers={})
    assert router.get_price("TEST:AAA", date(2026, 1, 5)) is None
