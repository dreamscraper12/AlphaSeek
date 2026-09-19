"""IVV total return in AUD, and the shadow benchmark (owner's flows applied
to IVV). See CLAUDE.md section 9. Needs a chosen price source — see section 3."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from portfolio.ledger import Ledger


def ivv_total_return_index(as_of: date) -> Decimal:
    raise NotImplementedError("Requires a chosen price source — see CLAUDE.md section 3")


def shadow_benchmark(ledger: Ledger, as_of: date) -> Decimal:
    raise NotImplementedError("Requires a chosen price source — see CLAUDE.md section 3")
