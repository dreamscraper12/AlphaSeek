"""Writers for data/generated/*.json — the only place a Decimal becomes a
float and a date becomes a string, since JSON has neither natively. See
CLAUDE.md section 10 for the full set of outputs."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from portfolio.attribution import Contribution, cumulative_contribution
from portfolio.benchmark import ShadowPoint
from portfolio.cost_basis import CostBasis
from portfolio.engine import NavPoint
from portfolio.ledger import Ledger
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
from portfolio.valuation import InstrumentValuation


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


def trades_json(ledger: Ledger) -> list[dict]:
    """Newest first, per CLAUDE.md section 13 (/journal)."""
    return [
        {
            "trade_id": t.trade_id,
            "executed_at": t.executed_at.isoformat(),
            "instrument_id": t.instrument_id,
            "side": t.side,
            "quantity": float(t.quantity),
            "price": float(t.price),
            "note_slug": t.note_slug,
        }
        for t in sorted(ledger.trades, key=lambda t: t.executed_at, reverse=True)
    ]


def _latest_note_slug(ledger: Ledger, instrument_id: str) -> str | None:
    trades = sorted(
        (t for t in ledger.trades if t.instrument_id == instrument_id and t.note_slug),
        key=lambda t: t.executed_at,
    )
    return trades[-1].note_slug if trades else None


def holdings_json(
    ledger: Ledger,
    latest_valuation_nav_aud: Decimal,
    positions: list[InstrumentValuation],
    cost_basis: dict[str, CostBasis],
    attribution_rows: list[Contribution],
) -> list[dict]:
    """`positions` is the latest day's DailyValuation.positions. Every
    figure is in AUD: `price` here is the per-unit AUD value implied by
    that day's market value, not the local-currency price shown elsewhere,
    so it lines up directly with `average_cost` for a simple return
    calculation, without a separate currency field."""
    instruments_by_id = {i.instrument_id: i for i in ledger.instruments}
    rows = []
    for p in positions:
        basis = cost_basis.get(p.instrument_id, CostBasis())
        price_aud = p.market_value_aud / p.quantity
        rows.append(
            {
                "instrument_id": p.instrument_id,
                "type": instruments_by_id[p.instrument_id].type,
                "weight": float(p.market_value_aud / latest_valuation_nav_aud),
                "average_cost": _optional_float(basis.average_cost_aud),
                "price": float(price_aud),
                "price_as_of": p.price_as_of.isoformat(),
                "return": _optional_float(price_aud / basis.average_cost_aud - 1)
                if basis.average_cost_aud
                else None,
                "contribution": float(cumulative_contribution(attribution_rows, p.instrument_id)),
                "note_slug": _latest_note_slug(ledger, p.instrument_id),
            }
        )
    return rows


def closed_positions_json(ledger: Ledger, cost_basis: dict[str, CostBasis]) -> list[dict]:
    """Instruments that were traded but are fully closed as of the build's
    valuation date (CLAUDE.md section 13: closed positions stay on the site
    permanently, with realised P&L)."""
    instruments_by_id = {i.instrument_id: i for i in ledger.instruments}
    return [
        {
            "instrument_id": instrument_id,
            "type": instruments_by_id[instrument_id].type,
            "realised_pnl": float(basis.realised_pnl_aud),
            "note_slug": _latest_note_slug(ledger, instrument_id),
        }
        for instrument_id, basis in cost_basis.items()
        if basis.quantity == 0
    ]


def attribution_json(rows: list[Contribution]) -> list[dict]:
    return [
        {"date": r.date.isoformat(), "instrument_id": r.instrument_id, "contribution": float(r.contribution)}
        for r in rows
    ]


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
