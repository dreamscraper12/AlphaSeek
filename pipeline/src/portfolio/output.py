"""Writers for data/generated/*.json — the only place a Decimal becomes a
float and a date becomes a string, since JSON has neither natively. See
CLAUDE.md section 10 for the full set of outputs; holdings, closed_positions,
trades and attribution still need the average-cost and per-day attribution
work not yet built."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from portfolio.benchmark import ShadowPoint
from portfolio.engine import NavPoint
from portfolio.metrics import (
    Drawdown,
    IndexPoint,
    annualised_return,
    annualised_volatility,
    beta,
    correlation,
    current_drawdown,
    excess_return,
    max_drawdown,
    period_returns,
    returns_from_index,
)


def nav_daily_json(series: list[NavPoint]) -> list[dict]:
    return [
        {"date": p.date.isoformat(), "nav": float(p.nav_aud), "index": float(p.index)}
        for p in series
    ]


def benchmark_daily_json(shadow_series: list[ShadowPoint], benchmark_series: list[IndexPoint]) -> list[dict]:
    benchmark_index_by_date = {p.date: p.index for p in benchmark_series}
    return [
        {
            "date": p.date.isoformat(),
            "nav": float(p.value_aud),
            "index": float(benchmark_index_by_date[p.date]),
        }
        for p in shadow_series
    ]


def _optional_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _drawdown_json(drawdown: Drawdown | None) -> dict | None:
    if drawdown is None:
        return None
    return {
        "peak_date": drawdown.peak_date.isoformat(),
        "trough_date": drawdown.trough_date.isoformat(),
        "drawdown": _optional_float(drawdown.drawdown),
    }


def _side_metrics_json(series: list[IndexPoint], period_return_values: dict[str, Decimal | None]) -> dict:
    daily_returns = returns_from_index(series)
    return {
        "returns": {k: _optional_float(v) for k, v in period_return_values.items()},
        "annualised_return": _optional_float(annualised_return(series)),
        "annualised_volatility": _optional_float(annualised_volatility(daily_returns)),
        "max_drawdown": _drawdown_json(max_drawdown(series)),
        "current_drawdown": _optional_float(current_drawdown(series)),
    }


def metrics_json(portfolio_series: list[IndexPoint], benchmark_series: list[IndexPoint]) -> dict:
    if not portfolio_series or not benchmark_series:
        return {"portfolio": None, "benchmark": None}

    portfolio_periods = period_returns(portfolio_series)
    benchmark_periods = period_returns(benchmark_series)

    portfolio = _side_metrics_json(portfolio_series, portfolio_periods)
    benchmark = _side_metrics_json(benchmark_series, benchmark_periods)

    portfolio_returns = returns_from_index(portfolio_series)
    benchmark_returns = returns_from_index(benchmark_series)
    portfolio["beta"] = _optional_float(beta(portfolio_returns, benchmark_returns))
    portfolio["correlation"] = _optional_float(correlation(portfolio_returns, benchmark_returns))
    portfolio["excess_return"] = _optional_float(
        excess_return(portfolio_periods["since_inception"], benchmark_periods["since_inception"])
    )

    return {"portfolio": portfolio, "benchmark": benchmark}


def status_json(series: list[NavPoint]) -> dict:
    """Reflects the latest valuation only — a current-state snapshot, not a
    historical log of every warning ever raised."""
    if not series:
        return {"last_valuation_date": None, "stale_prices": [], "warnings": []}
    latest = series[-1]
    stale_prices = sorted(
        iv.instrument_id for iv in latest.valuation.positions if iv.stale_business_days > 0
    )
    return {
        "last_valuation_date": latest.date.isoformat(),
        "stale_prices": stale_prices,
        "warnings": latest.valuation.warnings,
    }


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
