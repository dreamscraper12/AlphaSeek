"""Time-weighted return: daily returns and chain-linking into an index. See
CLAUDE.md section 9. Pure functions only — valuation.py supplies the NAV
series this operates on."""

from __future__ import annotations

from decimal import Decimal

INCEPTION_INDEX = Decimal(10000)


def daily_return(nav_today: Decimal, nav_yesterday: Decimal, net_flow: Decimal) -> Decimal:
    """r_D = (NAV_D - F_D) / NAV_{D-1} - 1, with F_D treated as end of day."""
    return (nav_today - net_flow) / nav_yesterday - 1


def chain_link(daily_returns: list[Decimal], base: Decimal = INCEPTION_INDEX) -> list[Decimal]:
    """Chain-link daily returns into an index series starting at `base`."""
    index = base
    series = []
    for r in daily_returns:
        index = index * (1 + r)
        series.append(index)
    return series
