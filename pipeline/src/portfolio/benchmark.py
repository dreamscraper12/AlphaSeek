"""IVV total return in AUD, and the shadow benchmark (the owner's own
external flows applied to IVV instead). See CLAUDE.md section 9.

The IVV total-return index is a normal price-return chain, except that on
a distribution's ex-date the payout is added back before computing that
day's return — a real previous close exists for IVV before the portfolio's
own inception, unlike the portfolio's NAV series, which has no "before"
(see portfolio.engine's different treatment of day zero).

The shadow benchmark grows each of the owner's own external flows by the
benchmark index's return from the flow's date forward, which is
equivalent to buying IVV units with that flow and reinvesting
distributions, without needing to track units directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from portfolio.calendar_days import business_days
from portfolio.csvutil import read_rows
from portfolio.metrics import IndexPoint
from portfolio.performance import INCEPTION_INDEX
from portfolio.prices import price_with_carry_forward
from portfolio.sources import PriceSource

IVV_INSTRUMENT_ID = "ASX:IVV"


class Distribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    ex_date: date
    amount_per_unit: Decimal
    currency: str
    source: str
    note: str = ""


@dataclass(frozen=True)
class ShadowPoint:
    date: date
    value_aud: Decimal


def load_distributions(path: Path) -> list[Distribution]:
    return [Distribution(**row) for row in read_rows(path)]


def ivv_total_return_series(
    start: date, as_of: date, price_source: PriceSource, distributions: list[Distribution]
) -> list[IndexPoint]:
    """IVV total return indexed to 10,000 at the close before `start` — the
    same "prior close" moment the portfolio's own NAV series is indexed
    from (CLAUDE.md section 9)."""
    distribution_by_date = {d.ex_date: d.amount_per_unit for d in distributions}

    prior_day = start - timedelta(days=1)
    priced = price_with_carry_forward(price_source, IVV_INSTRUMENT_ID, prior_day)
    if priced is None:
        raise ValueError(f"missing IVV price before {start}, no fallback available")
    previous_price = priced[0]

    index = INCEPTION_INDEX
    points: list[IndexPoint] = []
    for d in business_days(start, as_of):
        priced = price_with_carry_forward(price_source, IVV_INSTRUMENT_ID, d)
        if priced is None:
            raise ValueError(f"missing IVV price on {d}, no fallback available")
        price = priced[0]
        distribution = distribution_by_date.get(d, Decimal(0))
        r = (price + distribution) / previous_price - 1
        index = index * (1 + r)
        points.append(IndexPoint(date=d, index=index))
        previous_price = price

    return points


def shadow_benchmark_series(
    flows_by_date: dict[date, Decimal], benchmark_series: list[IndexPoint], inception_date: date
) -> list[ShadowPoint]:
    """Applies the owner's own external flows to IVV. Every flow except the
    inception deposit is invested at the benchmark's close on its own date,
    matching how the same flow is treated as landing at end-of-day in
    portfolio.engine. The inception deposit is the one exception (CLAUDE.md
    section 9: "the inception deposit at the prior close"): it's invested
    at index 10,000, the state just before its own date's return, so it's
    exposed to that day's full move — mirroring portfolio.engine treating
    day zero's return as NAV_D0 / deposit - 1, not the general same-day
    formula."""
    index_by_date = {p.date: p.index for p in benchmark_series}
    points: list[ShadowPoint] = []
    for point in benchmark_series:
        value = Decimal(0)
        for flow_date, amount in flows_by_date.items():
            if flow_date > point.date:
                continue
            base_index = INCEPTION_INDEX if flow_date == inception_date else index_by_date[flow_date]
            value += amount * (point.index / base_index)
        points.append(ShadowPoint(date=point.date, value_aud=value))
    return points
