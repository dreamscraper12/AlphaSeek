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

Phase 1 pipeline complete. `portfolio build` computes the full daily NAV/TWR series, the
IVV total-return benchmark and shadow benchmark, metrics, attribution, holdings, closed
positions and trades, and writes every file in CLAUDE.md section 10. The site renders all
of it.

Not done yet: there is no real ledger data (no inception deposit), the site is not
deployed anywhere, and `daily.yml` has never run.

Price sources, all verified live on 2026-09-20:

| Data | Source | Key needed |
|---|---|---|
| US equities and ETFs | Twelve Data (free tier) | `TWELVE_DATA_API_KEY`, see `.env.example` |
| ASX equities and ETFs | Yahoo Finance | no |
| AUD/USD | Frankfurter (ECB rates) | no |
| Crypto | CoinGecko | no |
| Options | manual marks in the ledger | no |

Twelve Data's free tier excludes the ASX and its cheapest ASX plan is US$99/month, so ASX
instruments — including the IVV benchmark — are priced via Yahoo Finance instead. That is
an undocumented endpoint, so manual marks remain a first-class fallback.
