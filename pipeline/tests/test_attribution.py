from datetime import date
from decimal import Decimal

from portfolio.attribution import CASH_AND_FX_LINE, Contribution, build_attribution, cumulative_contribution
from portfolio.engine import build_nav_series, external_flow_aud
from portfolio.ledger import Cashflow, Instrument, Ledger, Trade
from portfolio.performance import daily_return
from portfolio.sources import PriceQuote

AAA = Instrument(
    instrument_id="TEST:AAA", type="equity", name="Test Company AAA",
    exchange="NASDAQ", currency="USD", price_source="manual",
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
        return Decimal(1) if from_currency == to_currency else self._rate


def _trade(**overrides) -> Trade:
    defaults = dict(
        trade_id="T1", executed_at="2026-01-05T10:00:00+11:00", instrument_id="TEST:AAA",
        side="BUY", quantity=Decimal("5"), price=Decimal("100.00"), fees=Decimal("0"),
        fees_currency="USD", rationale="Test.",
    )
    defaults.update(overrides)
    return Trade(**defaults)


def _ledger(**overrides) -> Ledger:
    defaults = dict(
        instruments=[AAA], trades=[], fx=[], cashflows=[], events=[],
        manual_marks=[], corrections=[],
    )
    defaults.update(overrides)
    return Ledger(**defaults)


def _build_scenario():
    ledger = _ledger(
        trades=[_trade()],
        cashflows=[
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("10000.00"), currency="AUD"),
            Cashflow(date=date(2026, 1, 5), type="DEPOSIT", amount=Decimal("1000.00"), currency="USD"),
            Cashflow(date=date(2026, 1, 6), type="DIVIDEND", amount=Decimal("10.00"), currency="USD", instrument_id="TEST:AAA"),
            Cashflow(date=date(2026, 1, 6), type="DEPOSIT", amount=Decimal("2000.00"), currency="AUD"),
            Cashflow(date=date(2026, 1, 7), type="INTEREST", amount=Decimal("5.00"), currency="AUD"),
        ],
    )
    prices = _FixedPriceSource(
        {
            ("TEST:AAA", date(2026, 1, 5)): Decimal("100.00"),
            ("TEST:AAA", date(2026, 1, 6)): Decimal("110.00"),
            ("TEST:AAA", date(2026, 1, 7)): Decimal("120.00"),
        }
    )
    fx = _FixedFxSource(Decimal("1.5"))
    nav_series = build_nav_series(ledger, date(2026, 1, 7), prices, fx)
    return ledger, fx, nav_series


def test_daily_contributions_sum_to_the_portfolio_daily_return():
    ledger, fx, nav_series = _build_scenario()
    rows = build_attribution(ledger, nav_series, fx)

    for i in range(1, len(nav_series)):
        d = nav_series[i].date
        total = sum((r.contribution for r in rows if r.date == d), Decimal(0))
        expected_flow = external_flow_aud(ledger, d, fx)
        expected_r = daily_return(nav_series[i].nav_aud, nav_series[i - 1].nav_aud, expected_flow)
        # Summing several independently-rounded Decimal divisions can differ
        # from one division by a unit or two in the last (28th) significant
        # digit; the identity holds well within any figure that's ever shown.
        assert abs(total - expected_r) < Decimal("1E-20")


def test_dividend_is_attributed_to_the_paying_instrument_not_cash():
    ledger, fx, nav_series = _build_scenario()
    rows = build_attribution(ledger, nav_series, fx)

    jan6_aaa = next(r for r in rows if r.date == date(2026, 1, 6) and r.instrument_id == "TEST:AAA")
    # Price return (100 -> 110, *1.5 FX) plus the $10 dividend (*1.5 FX),
    # over 5 shares, relative to the prior day's NAV.
    nav_jan5 = nav_series[0].nav_aud
    expected = (Decimal("5") * Decimal("110") * Decimal("1.5") - Decimal("5") * Decimal("100") * Decimal("1.5")
                + Decimal("10") * Decimal("1.5")) / nav_jan5
    assert jan6_aaa.contribution == expected


def test_cumulative_contribution_sums_across_days():
    rows = [
        Contribution(date(2026, 1, 6), "TEST:AAA", Decimal("0.01")),
        Contribution(date(2026, 1, 7), "TEST:AAA", Decimal("0.02")),
        Contribution(date(2026, 1, 6), CASH_AND_FX_LINE, Decimal("-0.001")),
    ]
    assert cumulative_contribution(rows, "TEST:AAA") == Decimal("0.03")
    assert cumulative_contribution(rows, CASH_AND_FX_LINE) == Decimal("-0.001")
    assert cumulative_contribution(rows, "TEST:ZZZ") == Decimal("0")
