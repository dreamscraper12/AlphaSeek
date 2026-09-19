"""Performance statistics derived from a TWR index series. See CLAUDE.md
section 9. Beta, correlation and excess return need a paired benchmark
return series and aren't implemented yet — the benchmark itself needs a
distribution data source that hasn't been chosen (CLAUDE.md section 3)."""

from __future__ import annotations

import calendar
import statistics
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class IndexPoint:
    date: date
    index: Decimal


@dataclass(frozen=True)
class Drawdown:
    peak_date: date
    peak_index: Decimal
    trough_date: date
    trough_index: Decimal
    drawdown: Decimal  # negative, e.g. Decimal("-0.15") for a 15% drawdown


def _shift_months(d: date, months: int) -> date:
    month_index = d.month - 1 - months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def period_return(series: list[IndexPoint], start: date) -> Decimal | None:
    """Return from the first point on or after `start` to the last point in
    the series, or None if the series doesn't reach back that far."""
    window = [p for p in series if p.date >= start]
    if not window:
        return None
    return series[-1].index / window[0].index - 1


def since_inception_return(series: list[IndexPoint]) -> Decimal | None:
    if not series:
        return None
    return series[-1].index / series[0].index - 1


def period_returns(series: list[IndexPoint]) -> dict[str, Decimal | None]:
    if not series:
        return {"1M": None, "3M": None, "YTD": None, "1Y": None, "since_inception": None}
    as_of = series[-1].date
    return {
        "1M": period_return(series, _shift_months(as_of, 1)),
        "3M": period_return(series, _shift_months(as_of, 3)),
        "YTD": period_return(series, date(as_of.year, 1, 1)),
        "1Y": period_return(series, _shift_months(as_of, 12)),
        "since_inception": since_inception_return(series),
    }


def annualised_return(series: list[IndexPoint]) -> Decimal | None:
    """Only meaningful once there's at least a year of history (CLAUDE.md
    section 9)."""
    if len(series) < 2:
        return None
    days = (series[-1].date - series[0].date).days
    if days < 365:
        return None
    total_return_factor = series[-1].index / series[0].index
    return total_return_factor ** (Decimal(365) / Decimal(days)) - 1


def max_drawdown(series: list[IndexPoint]) -> Drawdown | None:
    if not series:
        return None
    peak = series[0]
    worst: Drawdown | None = None
    for point in series:
        if point.index > peak.index:
            peak = point
        dd = point.index / peak.index - 1
        if worst is None or dd < worst.drawdown:
            worst = Drawdown(
                peak_date=peak.date,
                peak_index=peak.index,
                trough_date=point.date,
                trough_index=point.index,
                drawdown=dd,
            )
    return worst


def current_drawdown(series: list[IndexPoint]) -> Decimal | None:
    if not series:
        return None
    peak_index = max(p.index for p in series)
    return series[-1].index / peak_index - 1


def annualised_volatility(daily_returns: list[Decimal]) -> Decimal | None:
    if len(daily_returns) < 2:
        return None
    return statistics.pstdev(daily_returns) * Decimal(252).sqrt()
