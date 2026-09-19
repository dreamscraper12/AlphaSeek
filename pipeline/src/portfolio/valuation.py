"""Daily NAV: market value of every position plus cash, in AUD. See CLAUDE.md
section 8. Needs a chosen price source before it can run — see section 3."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from portfolio.ledger import Ledger


@dataclass(frozen=True)
class DailyValuation:
    date: date
    nav_aud: Decimal
    positions: dict[str, Decimal]
    cash_by_currency: dict[str, Decimal]


def value_day(ledger: Ledger, as_of: date) -> DailyValuation:
    raise NotImplementedError("Requires a chosen price source — see CLAUDE.md section 3")
