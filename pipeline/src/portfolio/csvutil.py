"""Shared CSV reading for the ledger (portfolio.ledger) and other
CSV-shaped data the owner maintains by hand, such as the benchmark's
distribution history (portfolio.benchmark)."""

from __future__ import annotations

import csv
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str | None]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = [row for row in csv.DictReader(f) if any(v.strip() for v in row.values())]
    return [{k: (v if v != "" else None) for k, v in row.items()} for row in rows]
