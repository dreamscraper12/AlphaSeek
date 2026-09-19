from datetime import date, datetime
from zoneinfo import ZoneInfo

from portfolio.schedule import latest_closed_business_day

SYDNEY = ZoneInfo("Australia/Sydney")


def test_tuesday_morning_targets_monday():
    now = datetime(2026, 1, 6, 9, 0, tzinfo=SYDNEY)  # a Tuesday
    assert latest_closed_business_day(now) == date(2026, 1, 5)


def test_monday_morning_targets_last_friday():
    now = datetime(2026, 1, 5, 9, 0, tzinfo=SYDNEY)  # a Monday
    assert latest_closed_business_day(now) == date(2026, 1, 2)


def test_sunday_targets_last_friday():
    now = datetime(2026, 1, 4, 15, 0, tzinfo=SYDNEY)  # a Sunday
    assert latest_closed_business_day(now) == date(2026, 1, 2)


def test_a_naive_or_differently_zoned_datetime_is_converted_to_sydney_first():
    # 2026-01-06 00:30 UTC is already 2026-01-06 11:30 in Sydney (a Tuesday),
    # so this must not be read as "Monday" just because the UTC date is.
    utc_early_tuesday = datetime(2026, 1, 6, 0, 30, tzinfo=ZoneInfo("UTC"))
    assert latest_closed_business_day(utc_early_tuesday) == date(2026, 1, 5)
