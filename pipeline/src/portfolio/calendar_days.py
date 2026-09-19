"""Business-day calendar shared by portfolio.engine (the NAV/TWR series) and
portfolio.benchmark (the IVV total-return series), so both walk exactly the
same set of dates. Business days are treated as Monday-Friday; AU/US public
holidays aren't modelled as a separate calendar, since a holiday behaves
exactly like a stale-price gap the valuation layer already carries forward
across. See CLAUDE.md section 8."""

from __future__ import annotations

from datetime import date, timedelta


def business_days(start: date, end: date) -> list[date]:
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days
