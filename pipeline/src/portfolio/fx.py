"""FX conversion. Rate lookup depends on the data source (open decision in
CLAUDE.md); the conversion itself is pure."""

from __future__ import annotations

from datetime import date
from decimal import Decimal


def convert(amount: Decimal, rate: Decimal) -> Decimal:
    return amount * rate


def get_rate(from_currency: str, to_currency: str, as_of: date) -> Decimal:
    raise NotImplementedError("FX rate source not yet chosen — see CLAUDE.md section 3")
