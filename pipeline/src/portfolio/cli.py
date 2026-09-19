from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portfolio import output
from portfolio.attribution import build_attribution
from portfolio.benchmark import ivv_total_return_series, load_distributions, shadow_benchmark_series
from portfolio.cost_basis import compute_cost_basis
from portfolio.engine import (
    build_nav_series,
    external_flows_by_date,
    inception_deposit_aud,
    inception_start_date,
)
from portfolio.ledger import Ledger, load_ledger
from portfolio.metrics import IndexPoint
from portfolio.schedule import latest_closed_business_day
from portfolio.sources.coingecko import CoinGeckoSource
from portfolio.sources.frankfurter import FrankfurterFxSource
from portfolio.sources.manual import ManualMarkSource
from portfolio.sources.router import RoutedPriceSource
from portfolio.sources.twelvedata import TwelveDataSource
from portfolio.validate import validate_ledger


def _run_validate(ledger_dir: Path) -> int:
    ledger = load_ledger(ledger_dir)
    errors = validate_ledger(ledger)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Ledger valid: {len(ledger.instruments)} instruments, {len(ledger.trades)} trades.")
    return 0


def _build_sources(ledger: Ledger, cache_dir: Path) -> tuple[RoutedPriceSource, FrankfurterFxSource, TwelveDataSource]:
    manual = ManualMarkSource(ledger.manual_marks)
    twelvedata = TwelveDataSource(cache_dir)
    providers = {"twelvedata": twelvedata, "coingecko": CoinGeckoSource(cache_dir)}
    price_source = RoutedPriceSource(ledger.instruments, manual, providers)
    fx_source = FrankfurterFxSource(cache_dir)
    # IVV isn't a ledger instrument (it's the benchmark, not something owned),
    # so it can't go through the router, which looks up price_source by
    # instrument — it's always priced directly via Twelve Data.
    return price_source, fx_source, twelvedata


def _write_empty_outputs(generated_dir: Path) -> None:
    output.write_json(generated_dir / "nav_daily.json", [])
    output.write_json(generated_dir / "status.json", output.status_json([]))
    output.write_json(generated_dir / "benchmark_daily.json", [])
    output.write_json(generated_dir / "metrics.json", {"portfolio": None, "benchmark": None})
    output.write_json(generated_dir / "holdings.json", [])
    output.write_json(generated_dir / "closed_positions.json", [])
    output.write_json(generated_dir / "attribution.json", [])


def _run_build(ledger_dir: Path, cache_dir: Path, generated_dir: Path, benchmark_dir: Path) -> int:
    status = _run_validate(ledger_dir)
    if status != 0:
        return status

    ledger = load_ledger(ledger_dir)
    output.write_json(generated_dir / "trades.json", output.trades_json(ledger))

    start = inception_start_date(ledger)
    if start is None:
        _write_empty_outputs(generated_dir)
        print("No deposit in the ledger yet — wrote empty output.")
        return 0

    price_source, fx_source, ivv_price_source = _build_sources(ledger, cache_dir)
    as_of = latest_closed_business_day()

    try:
        nav_series = build_nav_series(ledger, as_of, price_source, fx_source)
        distributions = load_distributions(benchmark_dir / "ivv_distributions.csv")
        benchmark_series = ivv_total_return_series(start, as_of, ivv_price_source, distributions)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    deposit = inception_deposit_aud(ledger, fx_source)
    output.write_json(generated_dir / "nav_daily.json", output.nav_daily_json(nav_series))
    output.write_json(generated_dir / "status.json", output.status_json(nav_series, deposit))

    flows = external_flows_by_date(ledger, fx_source)
    shadow_series = shadow_benchmark_series(flows, benchmark_series, inception_date=start)
    output.write_json(
        generated_dir / "benchmark_daily.json", output.benchmark_daily_json(shadow_series, benchmark_series)
    )

    portfolio_index_series = [IndexPoint(date=p.date, index=p.index) for p in nav_series]
    output.write_json(generated_dir / "metrics.json", output.metrics_json(portfolio_index_series, benchmark_series))

    attribution_rows = build_attribution(ledger, nav_series, fx_source)
    output.write_json(generated_dir / "attribution.json", output.attribution_json(attribution_rows))

    cost_basis = compute_cost_basis(ledger, as_of, fx_source)
    latest = nav_series[-1]
    output.write_json(
        generated_dir / "holdings.json",
        output.holdings_json(ledger, latest.nav_aud, latest.valuation.positions, cost_basis, attribution_rows),
    )
    output.write_json(generated_dir / "closed_positions.json", output.closed_positions_json(ledger, cost_basis))

    print(f"Valued through {latest.date} ({len(nav_series)} business days).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="portfolio")
    parser.add_argument(
        "--ledger-dir", type=Path, default=Path("data/ledger"), help="path to the CSV ledger"
    )
    parser.add_argument(
        "--cache-dir", type=Path, default=Path("data/cache"), help="path to the raw provider cache"
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=Path("data/generated"),
        help="path to write pipeline output",
    )
    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        default=Path("data/benchmark"),
        help="path to the IVV distribution history",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the ledger without pricing it")
    subparsers.add_parser("build", help="recompute data/generated")

    args = parser.parse_args()
    if args.command == "validate":
        sys.exit(_run_validate(args.ledger_dir))
    elif args.command == "build":
        sys.exit(_run_build(args.ledger_dir, args.cache_dir, args.generated_dir, args.benchmark_dir))
