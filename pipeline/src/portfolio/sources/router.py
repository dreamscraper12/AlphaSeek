"""Routes each instrument to its price source by instruments.csv's
price_source field, with manual marks always checked first — CLAUDE.md
section 8: "Precedence: manual mark over provider data.\""""

from __future__ import annotations

from datetime import date

from portfolio.ledger import Instrument
from portfolio.sources import PriceQuote, PriceSource
from portfolio.sources.manual import ManualMarkSource


class RoutedPriceSource:
    def __init__(
        self,
        instruments: list[Instrument],
        manual: ManualMarkSource,
        providers: dict[str, PriceSource],
    ) -> None:
        self._instrument_by_id = {i.instrument_id: i for i in instruments}
        self._manual = manual
        self._providers = providers

    def get_price(self, instrument_id: str, as_of: date) -> PriceQuote | None:
        manual_hit = self._manual.get_price(instrument_id, as_of)
        if manual_hit is not None:
            return manual_hit
        instrument = self._instrument_by_id[instrument_id]
        provider = self._providers.get(instrument.price_source)
        if provider is None:
            return None
        return provider.get_price(instrument_id, as_of)
