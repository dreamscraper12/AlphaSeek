# Portfolio site

A public record of a personal investment portfolio, built from a ledger of CSV files. See [CLAUDE.md](./CLAUDE.md) for the full project brief, rules and build phases.

## Commands

```
npm run dev                                   # local site
npm run build                                 # production build
npm run check                                 # astro check + content lint
uv run --project pipeline portfolio build     # recompute data/generated
uv run --project pipeline portfolio validate  # ledger and output checks only
uv run --project pipeline pytest
```

## Status

Phase 1 in progress. The site builds and the ledger validates. Price adapters (Twelve Data for ASX/US equities and ETFs, Frankfurter for FX, CoinGecko for crypto, manual marks for options) and single-day valuation are implemented and tested (`portfolio.valuation.value_day`), but `portfolio build` still isn't functional end to end — the daily NAV series, TWR, benchmark, shadow benchmark, metrics, attribution and `data/generated/*.json` writers described in CLAUDE.md section 10 aren't built yet. See the open decisions and decision log in CLAUDE.md.

Using the equity/ETF price adapter for real requires a free API key from [twelvedata.com](https://twelvedata.com/), set as `TWELVE_DATA_API_KEY` (see `.env.example`). Its exact ASX symbol coverage hasn't been verified against a live key yet.
