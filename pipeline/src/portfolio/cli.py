from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portfolio import output
from portfolio.engine import build_nav_series
from portfolio.ledger import Ledger, load_ledger
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


def _build_sources(ledger: Ledger, cache_dir: Path) -> tuple[RoutedPriceSource, FrankfurterFxSource]:
    manual = ManualMarkSource(ledger.manual_marks)
    providers = {
        "twelvedata": TwelveDataSource(cache_dir),
        "coingecko": CoinGeckoSource(cache_dir),
    }
    price_source = RoutedPriceSource(ledger.instruments, manual, providers)
    fx_source = FrankfurterFxSource(cache_dir)
    return price_source, fx_source


def _run_build(ledger_dir: Path, cache_dir: Path, generated_dir: Path) -> int:
    status = _run_validate(ledger_dir)
    if status != 0:
        return status

    ledger = load_ledger(ledger_dir)
    price_source, fx_source = _build_sources(ledger, cache_dir)
    as_of = latest_closed_business_day()

    try:
        series = build_nav_series(ledger, as_of, price_source, fx_source)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    output.write_json(generated_dir / "nav_daily.json", output.nav_daily_json(series))
    output.write_json(generated_dir / "status.json", output.status_json(series))

    if series:
        print(f"Valued through {series[-1].date} ({len(series)} business days).")
    else:
        print("No deposit in the ledger yet — wrote an empty NAV series.")
    print(
        "The benchmark, attribution, and the holdings/closed_positions/trades/metrics "
        "writers (CLAUDE.md section 10) still aren't implemented.",
        file=sys.stderr,
    )
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
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the ledger without pricing it")
    subparsers.add_parser("build", help="recompute data/generated")

    args = parser.parse_args()
    if args.command == "validate":
        sys.exit(_run_validate(args.ledger_dir))
    elif args.command == "build":
        sys.exit(_run_build(args.ledger_dir, args.cache_dir, args.generated_dir))
