from datetime import date
from decimal import Decimal

from portfolio.cost_basis import compute_cost_basis
from portfolio.ledger import Instrument, Ledger, Trade

AAA = Instrument(
    instrument_id="TEST:AAA", type="equity", name="Test Company AAA",
    exchange="NASDAQ", currency="USD", price_source="manual",
)

SHORT_CALL = Instrument(
    instrument_id="OPT:TEST:AAA:2026-06-19:C:120", type="option", name="AAA Jun-26 120 Call",
    exchange="NASDAQ", currency="USD", underlying_id="TEST:AAA", expiry=date(2026, 6, 19),
    right="C", strike=Decimal("120"), multiplier=Decimal("100"), exercise_style="american",
    price_source="manual",
)


class _FixedFxSource:
    def __init__(self, rate: Decimal = Decimal("1")) -> None:
        self._rate = rate

    def get_rate(self, from_currency, to_currency, as_of):
        return Decimal(1) if from_currency == to_currency else self._rate


def _trade(**overrides) -> Trade:
    defaults = dict(
        trade_id="T1", executed_at="2026-01-05T10:00:00+11:00", instrument_id="TEST:AAA",
        side="BUY", quantity=Decimal("10"), price=Decimal("100.00"), fees=Decimal("0"),
        fees_currency="USD", rationale="Test.",
    )
    defaults.update(overrides)
    return Trade(**defaults)


def _ledger(trades: list[Trade], instruments=None) -> Ledger:
    return Ledger(
        instruments=instruments or [AAA, SHORT_CALL], trades=trades, fx=[], cashflows=[],
        events=[], manual_marks=[], corrections=[],
    )


def test_weighted_average_across_two_buys():
    ledger = _ledger([
        _trade(trade_id="T1", quantity=Decimal("10"), price=Decimal("100")),
        _trade(trade_id="T2", quantity=Decimal("10"), price=Decimal("120")),
    ])
    basis = compute_cost_basis(ledger, date(2026, 1, 6), _FixedFxSource())["TEST:AAA"]
    assert basis.quantity == Decimal("20")
    assert basis.average_cost_aud == Decimal("110")
    assert basis.realised_pnl_aud == Decimal("0")


def test_partial_sell_realises_pnl_without_moving_average_cost():
    ledger = _ledger([
        _trade(trade_id="T1", side="BUY", quantity=Decimal("10"), price=Decimal("100")),
        _trade(trade_id="T2", side="SELL", quantity=Decimal("4"), price=Decimal("150")),
    ])
    basis = compute_cost_basis(ledger, date(2026, 1, 6), _FixedFxSource())["TEST:AAA"]
    assert basis.quantity == Decimal("6")
    assert basis.average_cost_aud == Decimal("100")
    assert basis.realised_pnl_aud == Decimal("200")  # (150-100)*4


def test_fx_conversion_is_applied_to_cost_basis():
    ledger = _ledger([_trade(trade_id="T1", quantity=Decimal("10"), price=Decimal("100"))])
    basis = compute_cost_basis(ledger, date(2026, 1, 6), _FixedFxSource(Decimal("1.5")))["TEST:AAA"]
    assert basis.average_cost_aud == Decimal("150")  # 100 USD * 1.5


def test_short_option_opened_and_closed_realises_pnl_the_short_way():
    ledger = _ledger([
        _trade(
            trade_id="T1", instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
            side="SELL", quantity=Decimal("1"), price=Decimal("2.50"),
        ),
        _trade(
            trade_id="T2", instrument_id="OPT:TEST:AAA:2026-06-19:C:120",
            side="BUY", quantity=Decimal("1"), price=Decimal("1.00"),
        ),
    ])
    basis = compute_cost_basis(ledger, date(2026, 1, 6), _FixedFxSource())["OPT:TEST:AAA:2026-06-19:C:120"]
    assert basis.quantity == Decimal("0")
    # Sold at 2.50 * 100 = 250, bought back at 1.00 * 100 = 100: profit 150.
    assert basis.realised_pnl_aud == Decimal("150")


def test_flip_through_zero_opens_a_fresh_average_on_the_other_side():
    ledger = _ledger([
        _trade(trade_id="T1", side="BUY", quantity=Decimal("5"), price=Decimal("100")),
        _trade(trade_id="T2", side="SELL", quantity=Decimal("8"), price=Decimal("110")),
    ])
    basis = compute_cost_basis(ledger, date(2026, 1, 6), _FixedFxSource())["TEST:AAA"]
    # Closes the long 5 @ realised (110-100)*5 = 50, then opens a fresh short 3 @ 110.
    assert basis.realised_pnl_aud == Decimal("50")
    assert basis.quantity == Decimal("-3")
    assert basis.average_cost_aud == Decimal("110")
