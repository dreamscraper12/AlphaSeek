"""Writers for data/generated/*.json — the only place a Decimal becomes a
float and a date becomes a string, since JSON has neither natively. See
CLAUDE.md section 10 for the full set of outputs; only nav_daily.json and
status.json are wired up so far. The rest (benchmark_daily.json, holdings,
closed_positions, trades, metrics, attribution) need the benchmark and
attribution work still to come."""

from __future__ import annotations

import json
from pathlib import Path

from portfolio.engine import NavPoint


def nav_daily_json(series: list[NavPoint]) -> list[dict]:
    return [
        {"date": p.date.isoformat(), "nav": float(p.nav_aud), "index": float(p.index)}
        for p in series
    ]


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
