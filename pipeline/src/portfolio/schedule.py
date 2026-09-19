"""When the daily job should value. CLAUDE.md section 10: "Values the latest
Sydney business day on which all markets have closed" and "GitHub cron can
run late, so the job must not depend on its exact run time."

Sydney is far enough ahead of the US that the US session for "yesterday
Sydney date" always finishes before "today" begins in Sydney — so simply
targeting the most recent business day strictly before today (in Sydney)
is safe regardless of what hour the job actually runs, without needing to
reason about exact market close times."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

SYDNEY = ZoneInfo("Australia/Sydney")


def latest_closed_business_day(now: datetime | None = None) -> date:
    now = now.astimezone(SYDNEY) if now else datetime.now(SYDNEY)
    d = now.date() - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d
