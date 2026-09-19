from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portfolio.ledger import load_ledger
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


def _run_build(ledger_dir: Path) -> int:
    status = _run_validate(ledger_dir)
    if status != 0:
        return status
    print(
        "Valuation pipeline not yet implemented — see CLAUDE.md section 3 (data provider) "
        "and section 18 (build phases).",
        file=sys.stderr,
    )
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="portfolio")
    parser.add_argument(
        "--ledger-dir", type=Path, default=Path("data/ledger"), help="path to the CSV ledger"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the ledger without pricing it")
    subparsers.add_parser("build", help="recompute data/generated")

    args = parser.parse_args()
    if args.command == "validate":
        sys.exit(_run_validate(args.ledger_dir))
    elif args.command == "build":
        sys.exit(_run_build(args.ledger_dir))
