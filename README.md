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

Phase 1 scaffolding only: the site builds and the ledger validates, but no price source is wired up yet, so `portfolio build` and the daily valuation are not yet functional. See the open decisions and decision log in CLAUDE.md.
