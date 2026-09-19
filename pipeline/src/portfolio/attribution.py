"""Per-position daily contribution to portfolio return. See CLAUDE.md
section 9. Needs daily valuations to already exist."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Contribution:
    date: date
    instrument_id: str
    contribution: Decimal


def daily_contribution(
    mv_today: Decimal,
    mv_yesterday: Decimal,
    net_purchases: Decimal,
    income: Decimal,
    nav_yesterday: Decimal,
) -> Decimal:
    return (mv_today - mv_yesterday - net_purchases + income) / nav_yesterday
