"""Daily NAV: market value of every position plus cash, in AUD. See CLAUDE.md
section 8. Prices and FX rates are looked up for as_of and, failing that,
carried forward from the most recent available business day — sources stay
dumb (exact-date lookups only) and this is the one place that knows about
staleness and its warning threshold."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from portfolio.fx import rate_with_carry_forward
from portfolio.ledger import Ledger
from portfolio.positions import build_positions
from portfolio.prices import price_with_carry_forward
from portfolio.sources import FxRateSource, PriceSource

STALE_WARNING_BUSINESS_DAYS = 3


@dataclass(frozen=True)
class InstrumentValuation:
    instrument_id: str
    quantity: Decimal
    price: Decimal
    currency: str
    price_as_of: date
    stale_business_days: int
    market_value_local: Decimal
    market_value_aud: Decimal


@dataclass(frozen=True)
class DailyValuation:
    date: date
    nav_aud: Decimal
    positions: list[InstrumentValuation]
    cash_by_currency: dict[str, Decimal]
    cash_aud: Decimal
    warnings: list[str] = field(default_factory=list)


def value_day(
    ledger: Ledger, as_of: date, price_source: PriceSource, fx_source: FxRateSource
) -> DailyValuation:
    positions = build_positions(ledger, as_of)
    instruments_by_id = {i.instrument_id: i for i in ledger.instruments}
    warnings: list[str] = []
    valuations: list[InstrumentValuation] = []
    nav_aud = Decimal(0)

    for instrument_id, quantity in positions.quantities.items():
        if quantity == 0:
            continue
        instrument = instruments_by_id[instrument_id]
        priced = price_with_carry_forward(price_source, instrument_id, as_of)
        if priced is None:
            raise ValueError(f"missing price for {instrument_id} on {as_of}, no fallback available")
        price, currency, price_as_of, stale_days = priced
        if stale_days > STALE_WARNING_BUSINESS_DAYS:
            warnings.append(
                f"{instrument_id} price stale for {stale_days} business days (as of {price_as_of})"
            )

        multiplier = instrument.multiplier if instrument.type == "option" else Decimal(1)
        market_value_local = price * multiplier * quantity

        rate = rate_with_carry_forward(fx_source, currency, "AUD", as_of)
        if rate is None:
            raise ValueError(f"missing FX rate {currency}->AUD on {as_of}, no fallback available")
        market_value_aud = market_value_local * rate
        nav_aud += market_value_aud

        valuations.append(
            InstrumentValuation(
                instrument_id=instrument_id,
                quantity=quantity,
                price=price,
                currency=currency,
                price_as_of=price_as_of,
                stale_business_days=stale_days,
                market_value_local=market_value_local,
                market_value_aud=market_value_aud,
            )
        )

    cash_aud = Decimal(0)
    for currency, amount in positions.cash.items():
        if amount == 0:
            continue
        if amount < 0:
            # No margin is modelled (CLAUDE.md section 11): this is a hard
            # validation failure, not a warning.
            raise ValueError(f"negative cash in {currency} on {as_of}: {amount}")
        rate = rate_with_carry_forward(fx_source, currency, "AUD", as_of)
        if rate is None:
            raise ValueError(f"missing FX rate {currency}->AUD on {as_of}, no fallback available")
        cash_aud += amount * rate

    nav_aud += cash_aud

    return DailyValuation(
        date=as_of,
        nav_aud=nav_aud,
        positions=valuations,
        cash_by_currency=positions.cash,
        cash_aud=cash_aud,
        warnings=warnings,
    )
