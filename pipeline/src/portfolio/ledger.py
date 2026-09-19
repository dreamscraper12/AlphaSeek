"""Load and parse the CSV ledger in data/ledger/ into typed rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from portfolio.csvutil import read_rows

InstrumentType = Literal["equity", "etf", "option", "crypto"]
Side = Literal["BUY", "SELL"]
CashflowType = Literal["DEPOSIT", "WITHDRAWAL", "DIVIDEND", "INTEREST", "FEE", "WITHHOLDING_TAX"]
EventType = Literal[
    "SPLIT", "OPTION_EXPIRED", "OPTION_EXERCISED", "OPTION_ASSIGNED", "SYMBOL_CHANGE", "OTHER"
]
ExerciseStyle = Literal["american", "european"]
Right = Literal["C", "P"]


class Instrument(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    type: InstrumentType
    name: str
    exchange: str
    currency: str
    underlying_id: str | None = None
    expiry: date | None = None
    right: Right | None = None
    strike: Decimal | None = None
    multiplier: Decimal | None = None
    exercise_style: ExerciseStyle | None = None
    price_source: str


class Trade(BaseModel):
    model_config = ConfigDict(frozen=True)

    trade_id: str
    executed_at: datetime
    instrument_id: str
    side: Side
    quantity: Decimal
    price: Decimal
    fees: Decimal
    fees_currency: str
    note_slug: str | None = None
    rationale: str


class FxConversion(BaseModel):
    model_config = ConfigDict(frozen=True)

    converted_at: datetime
    from_currency: str
    from_amount: Decimal
    to_currency: str
    to_amount: Decimal
    fees: Decimal
    fees_currency: str


class Cashflow(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    type: CashflowType
    amount: Decimal
    currency: str
    instrument_id: str | None = None
    memo: str = ""


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    instrument_id: str
    type: EventType
    details: str
    memo: str = ""


class ManualMark(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    instrument_id: str
    price: Decimal
    currency: str
    source: str
    reason: str


class Correction(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    file: str
    key: str
    change: str
    reason: str


@dataclass(frozen=True)
class Ledger:
    instruments: list[Instrument]
    trades: list[Trade]
    fx: list[FxConversion]
    cashflows: list[Cashflow]
    events: list[Event]
    manual_marks: list[ManualMark]
    corrections: list[Correction]


def load_ledger(ledger_dir: Path) -> Ledger:
    return Ledger(
        instruments=[Instrument(**row) for row in read_rows(ledger_dir / "instruments.csv")],
        trades=[Trade(**row) for row in read_rows(ledger_dir / "trades.csv")],
        fx=[FxConversion(**row) for row in read_rows(ledger_dir / "fx.csv")],
        cashflows=[Cashflow(**row) for row in read_rows(ledger_dir / "cashflows.csv")],
        events=[Event(**row) for row in read_rows(ledger_dir / "events.csv")],
        manual_marks=[ManualMark(**row) for row in read_rows(ledger_dir / "manual_marks.csv")],
        corrections=[Correction(**row) for row in read_rows(ledger_dir / "corrections.csv")],
    )
