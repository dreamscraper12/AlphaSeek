"""On-disk cache for raw provider price data, under data/cache/ (gitignored
per CLAUDE.md section 5). It's a speed-up and a way to stay under free-tier
rate limits, not the record of truth — safe to delete and rebuild by calling
the providers again."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path


def _safe_name(key: str) -> str:
    return key.replace(":", "_").replace("/", "_")


class PriceCache:
    def __init__(self, cache_dir: Path, provider: str) -> None:
        self._dir = cache_dir / "prices" / provider
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._dir / f"{_safe_name(key)}.csv"

    def load(self, key: str) -> dict[date, tuple[Decimal, str]]:
        path = self._path(key)
        if not path.exists():
            return {}
        rows: dict[date, tuple[Decimal, str]] = {}
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[date.fromisoformat(row["date"])] = (Decimal(row["price"]), row["currency"])
        return rows

    def save(self, key: str, rows: dict[date, tuple[Decimal, str]]) -> None:
        if not rows:
            return
        merged = self.load(key)
        merged.update(rows)
        with self._path(key).open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "price", "currency"])
            for d in sorted(merged):
                price, currency = merged[d]
                writer.writerow([d.isoformat(), str(price), currency])
