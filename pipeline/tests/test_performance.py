from decimal import Decimal

from portfolio.performance import chain_link, daily_return


def test_daily_return_with_no_flow():
    # NAV rises 5% with no deposit or withdrawal.
    r = daily_return(Decimal("10500"), Decimal("10000"), Decimal("0"))
    assert r == Decimal("0.05")


def test_daily_return_with_mid_period_deposit():
    # Prior-day NAV of 10500 grows 2% in the market to 10710, then a same-day
    # $1000 deposit lands on top, for an ending NAV of 11710. The deposit
    # must not distort the reported 2% market return.
    r = daily_return(Decimal("11710"), Decimal("10500"), Decimal("1000"))
    assert r == Decimal("0.02")


def test_chain_link_builds_index_from_10000():
    series = chain_link([Decimal("0.05"), Decimal("0.02")])
    assert series == [Decimal("10500.00"), Decimal("10710.0000")]
