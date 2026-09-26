# CLAUDE.md

This file is the project brief and working rules for Claude Code. It also serves as the initial build spec. After Phase 1 ships, move sections 7 to 18 into `docs/SPEC.md`, link to it from here, and keep this file to the rules, stack, layout, commands and decision log.

## 1. What this project is

A public website documenting a personal investment portfolio from inception, starting with A$10,000. The owner publishes anonymously (see ground rule 8).

- **Strategy:** high growth, high risk, unconstrained. Holdings may include ASX and US equities, ETFs, options (including short-dated contracts) and crypto.
- **Benchmark:** S&P 500 total return in AUD, using the ASX-listed iShares S&P 500 ETF (IVV).
- **Process:** "AI + Human". AI assists with research; the owner makes every judgement and decision. This is disclosed openly, site-wide and on every note.
- **Content:** performance vs benchmark, holdings, every trade, research notes (thesis, DCF, valuation, risks), method, disclaimer.
- **Style:** minimal, simple, clean.

The site's value rests on trust. When a choice is between making the record look more impressive and making it more verifiable, choose verifiable.

## 2. Ground rules

1. **The ledger is the source of truth.** Every displayed number is computed by the pipeline from `data/ledger/`. Never hand-edit `data/generated/`, and never hardcode a figure into a page or component.
2. **Nothing disappears.** Closed and losing positions stay on the site permanently. Any edit to an existing ledger row gets an entry in `data/ledger/corrections.csv` saying what changed and why. Git history is the audit trail.
3. **A journal, not advice.** Content describes what the owner owns and why. No ratings, no price targets, no instructions to readers. See section 12; CI enforces it.
4. **Never invent financial data.** Fixtures use obviously fake instruments (`TEST:AAA`, `TEST:BBB`) and live under `pipeline/tests/`. The production build must never read them. Don't seed the site with sample holdings, prices or returns.
5. **Ask the owner before** changing the performance methodology or benchmark, editing disclaimer text, adding a paid service or new data source, adding analytics or cookies, or doing anything that changes figures already published.
6. **Keep it static.** No server, database or user accounts. Client-side JavaScript only where it earns its place (charts, sensitivity tables).
7. **Secrets** live in GitHub Actions secrets and a local `.env` (gitignored). Never commit them or print them in logs.
8. **Keep the owner anonymous.** Refer to them only as "the owner" in the repo and "I" on the site. Never record their name, email, location, employer, job or professional credentials in files, commit messages, generated output or page copy, and don't infer or add any of these from context. Commits should use a GitHub noreply address, not a personal one. If something identifying turns up, flag it to the owner rather than working around it.
9. **Decimal arithmetic.** Parse ledger amounts as `Decimal`, never float. Round only for display.

## 3. Open decisions (owner to confirm)

When a task depends on an unchecked item, stop and ask instead of choosing.

- [x] Site name: AlphaSeek (confirmed 2026-09-20). Domain deferred — the site is served as a GitHub Pages project page (URL set in `astro.config.mjs`) until a custom domain is chosen
- [ ] Inception date
- [x] Broker: Interactive Brokers (confirmed 2026-09-19)
- [ ] Crypto venue: whether IBKR's own crypto offering is used, or a separate exchange
- [x] Data provider for ASX and US equities/ETFs, and for FX (confirmed 2026-09-19, ASX amended 2026-09-20): Twelve Data for **US** equities/ETFs, Yahoo Finance for **ASX**, Frankfurter (ECB rates) for FX, CoinGecko for crypto
- [x] `holdings.json` keeps publishing per-unit prices (confirmed 2026-09-20)
- [ ] Data source for option prices (US and ASX), or manual marks only
- [x] Trading policy: the owner sets and applies the disclosure window; it is not enforced or recorded in this repo (confirmed 2026-09-20). The Method page's trading policy section says so
- [x] Disclaimer: the owner accepted the section 15 draft wording as-is. No financial services lawyer review was obtained (confirmed 2026-09-20)
- [x] Employer compliance approval obtained (confirmed 2026-09-20)
- [ ] Analytics: none, or a cookieless option
- [ ] Where to back up the option quote archive (see section 8)

## 4. Stack

- **Site:** Astro (latest stable), TypeScript strict, content collections with Zod schemas, plain CSS with custom properties. No CSS framework.
- **Charts:** uPlot for time series, loaded as client islands. Every chart has a table alternative.
- **Pipeline:** Python 3.12+, managed with uv; pandas, pydantic, pytest.
- **Automation:** GitHub Actions.
- **Hosting:** GitHub Pages, deploying on push to `master` via `deploy.yml`. Served as a project page at `/AlphaSeek`, so internal links go through `src/lib/url.ts` rather than being written as raw absolute paths.
- **Fonts:** self-hosted via Fontsource. No runtime requests to third parties.

## 5. Repository layout

```
/
├── CLAUDE.md
├── README.md
├── .env.example              # names of the secrets a local build needs; no values
├── astro.config.mjs
├── package.json
├── src/
│   ├── content/
│   │   ├── notes/            # research notes (MDX)
│   │   └── pages/            # method, about, disclaimer (MD)
│   ├── components/           # EquityCurve, HoldingsTable, SnapshotPanel, SensitivityGrid, ...
│   ├── layouts/
│   ├── lib/                  # formatting, loading generated JSON
│   ├── pages/
│   └── styles/tokens.css
├── public/models/            # downloadable Excel models
├── data/
│   ├── ledger/               # maintained by the owner; the source of truth
│   │   ├── instruments.csv
│   │   ├── trades.csv
│   │   ├── fx.csv
│   │   ├── cashflows.csv
│   │   ├── events.csv
│   │   ├── manual_marks.csv
│   │   └── corrections.csv
│   ├── reconciliation/       # broker statement snapshots, YYYY-MM-DD.csv
│   ├── benchmark/            # IVV distribution history (owner-maintained, sourced from iShares)
│   ├── generated/            # pipeline output; committed; never hand-edited
│   └── cache/                # raw provider data; gitignored
├── pipeline/
│   ├── pyproject.toml
│   ├── src/portfolio/        # ledger, sources/, fx, valuation, performance,
│   │                         # benchmark, attribution, validate, cli
│   └── tests/                # fixtures use TEST: instruments only
├── scripts/lint-content.mjs  # advice-language lint (section 12)
└── .github/workflows/
    ├── daily.yml
    ├── deploy.yml
    └── ci.yml
```

## 6. Commands

Set these up in Phase 1 and keep this section accurate.

```
npm run dev                                   # local site
npm run build                                 # production build
npm run check                                 # astro check + content lint
uv run --project pipeline portfolio build     # recompute data/generated
uv run --project pipeline portfolio validate  # ledger and output checks only
uv run --project pipeline pytest
```

## 7. Ledger data model

Conventions: CSV with a header row; dates `YYYY-MM-DD`; datetimes ISO 8601 with offset, in Australia/Sydney; ISO currency codes; base currency AUD.

**Instrument IDs**
- Listed: `ASX:ABC`, `NASDAQ:ABCD`, `NYSE:ABC`
- Crypto: `CRYPTO:BTC`
- Options: `OPT:<underlying_id>:<expiry>:<C|P>:<strike>`, e.g. `OPT:NASDAQ:ABCD:2026-12-18:C:250`

**instruments.csv**
`instrument_id, type (equity|etf|option|crypto), name, exchange, currency, underlying_id, expiry, right, strike, multiplier, exercise_style (american|european), price_source`

**trades.csv**
`trade_id, executed_at, instrument_id, side (BUY|SELL), quantity, price, fees, fees_currency, note_slug, rationale`
- `quantity` is always positive; `side` sets direction. `price` is per unit in the instrument's currency (options: premium per share, before the multiplier).
- Selling an option not held opens a short (written) position. Short positions are valid only for options.
- `rationale` is one or two sentences, shown in the journal.

**fx.csv**
`converted_at, from_currency, from_amount, to_currency, to_amount, fees, fees_currency`
If the broker converts automatically at trade time, record the conversion here too. Conversion cost falls out of the executed rate versus the market rate.

**cashflows.csv**
`date, type (DEPOSIT|WITHDRAWAL|DIVIDEND|INTEREST|FEE|WITHHOLDING_TAX), amount, currency, instrument_id, memo`
Amounts are positive; `type` sets direction. Only DEPOSIT and WITHDRAWAL are external flows.

**events.csv**
`date, instrument_id, type (SPLIT|OPTION_EXPIRED|OPTION_EXERCISED|OPTION_ASSIGNED|SYMBOL_CHANGE|OTHER), details, memo`
`details` is JSON, e.g. `{"ratio": "4:1"}` or `{"new_id": "NASDAQ:NEW"}`. Exercise and assignment convert the option into the underlying at strike × multiplier, with the matching cash movement.

**manual_marks.csv**
`date, instrument_id, price, currency, source, reason`
Overrides provider data for that instrument and date.

**corrections.csv**
`date, file, key, change, reason`

**benchmark/ivv_distributions.csv**
`ex_date, amount_per_unit, currency, source, note`
IVV's distribution history, used to build the total-return benchmark index (section 9: distributions reinvested on the ex-date). Not part of the ledger — it's reference data about the benchmark instrument, not the owner's own activity — but maintained the same way as a manual mark: real, sourced figures the owner copies in from iShares' published distribution history (never invented; see ground rule 4), each row citing where it came from in `source`.

**reconciliation/YYYY-MM-DD.csv**
`instrument_id, quantity`, plus `CASH:<CCY>` rows, copied from a broker statement. Instrument IDs, quantities and cash balances only: never account numbers, names, addresses or statement images, because the repo is public.

## 8. Valuation rules

Valuation date D is a Sydney business day. The daily job runs the following morning, Sydney time, after the US close, and values D using:

- **ASX instruments:** close on D.
- **US instruments:** close of the US session dated D.
- **FX:** one consistent daily AUD/USD source for D.
- **Crypto:** close at 00:00 UTC ending UTC day D; the AUD quote if available, otherwise USD × FX.
- **Options:** closing bid/ask mid; otherwise last trade; otherwise a manual mark for D; otherwise the build fails. Market value = price × multiplier × signed quantity, so short options carry negative value.
- **Precedence:** manual mark over provider data.
- **Holidays and gaps:** carry the last price forward and flag it as stale. Stale for more than 3 business days is a build warning, and the site shows the "price as of" date for that instrument.
- **Weekends:** no NAV points. Crypto moves over a weekend land in Monday's value. State this on the Method page.

Options are the hardest part to price. Free sources rarely provide historical option prices, and ASX option data is patchy. So:
- `sources/` defines an adapter interface, and each instrument type (or individual instrument) can use a different source.
- Manual marks are a first-class fallback, not an afterthought.
- Option quotes usually can't be backfilled, so the daily job archives each day's quotes for open options in `data/cache/`. Back the archive up (see open decisions).

## 9. Performance methodology

- **NAV (AUD):** market value of every position × FX, plus cash in each currency × FX.
- **Daily return:** `r_D = (NAV_D − F_D) / NAV_{D−1} − 1`, where `F_D` is net external flows on D (deposits minus withdrawals), treated as end of day.
- **Inception:** the initial deposit arrives before the first trade, so the index is 10,000 at the prior close and the first return is `NAV_D0 / deposit − 1`.
- **Time-weighted return:** chain-link daily returns into an index starting at 10,000.
- Dividends, interest, fees and withholding tax are internal: they move NAV, not flows.
- All returns are net of trading and FX costs, and pre-tax.
- **Benchmark:** IVV total return in AUD (distributions reinvested on the ex-date), indexed to 10,000 at the same prior close.
- **Shadow benchmark:** apply the owner's external flows to IVV, each invested at the IVV close on its date (the inception deposit at the prior close). Dollar charts compare NAV with the shadow benchmark; percentage tables compare TWR with TWR. With no flows after inception, the two are identical.
- **Metrics** (`metrics.json`, for both portfolio and benchmark): 1M, 3M, YTD, 1Y and since-inception returns; annualised return only once there's at least a year of history; max drawdown with peak and trough dates; current drawdown; annualised volatility (daily returns, √252); beta and correlation to the benchmark after at least 60 observations; excess return.
- **Attribution:** daily contribution of position i = `(MV_i,D − MV_i,D−1 − net purchases_i,D + income_i,D) / NAV_{D−1}`, in AUD, so FX is included. FX on cash is its own line. Cumulative contribution is the sum; show the compounding residual against TWR.
- **Position P&L:** realised and unrealised, in AUD, average cost for display. Reported performance doesn't depend on the cost method.

Any change to this section needs owner approval and a row in the decision log. Never silently restate history.

## 10. Pipeline and automation

`portfolio build` runs: load ledger → validate → fetch prices (cache first) → value each day → NAV, TWR, benchmark, shadow benchmark, metrics, attribution → write `data/generated/*.json` → validate outputs.

Outputs: `nav_daily.json`, `benchmark_daily.json`, `holdings.json`, `closed_positions.json`, `trades.json`, `metrics.json`, `attribution.json`, `status.json` (last valuation date, stale prices, warnings).

**daily.yml**
- Schedule `0 23 * * 1-5` (UTC, about 9–10am Sydney, after both the ASX and US closes for that day), plus manual `workflow_dispatch`.
- Values the latest Sydney business day on which all markets have closed. Idempotent: rerunning produces the same output.
- Runs build and tests; if generated files changed, commits `data: valuation for YYYY-MM-DD` (the valuation date D, not the run date) and pushes, then deploys. A push made with the default `GITHUB_TOKEN` does not trigger other workflows, so the deploy must be started explicitly (e.g. `deploy.yml` on `workflow_run` or `workflow_call`), not left to the push.
- Logs options expiring within 5 business days.
- GitHub cron can run late, so the job must not depend on its exact run time.

**ci.yml:** on every push and pull request, run validate, pytest, `npm run check` and `npm run build`.

## 11. Validation

Fail the build on:
- Malformed rows, duplicate `trade_id`, unknown `instrument_id`
- Negative cash in any currency at the end of a day (no margin is modelled)
- A short position in anything other than an option
- An option with open quantity after expiry and no event row
- A `note_slug` that doesn't match a note
- A mismatch against the latest file in `data/reconciliation/`
- A missing price with no fallback

Warn on:
- A price stale for more than 3 business days
- A daily NAV move greater than 20% (confirm it's real)
- Options expiring within 5 business days

## 12. Language rules (compliance)

The site is a personal journal, not advice to readers. `scripts/lint-content.mjs` fails `npm run check` if content or UI copy contains, case-insensitively: "buy rating", "sell rating", "hold rating", "strong buy", "price target", "target price", "you should buy", "you should sell", "guaranteed", "can't lose", "sure thing", "to the moon".

Use instead: "my fair value estimate", "I bought", "I own", "I sold", "what would prove me wrong". Quoting a third party is allowed with an allow comment on the preceding line that gives the reason (`{/* lint-allow: quoting X */}` in MDX).

## 13. Pages

- `/` Home: one plain sentence with the headline result, the equity curve (portfolio vs shadow benchmark), a compact holdings list, and the latest trades and notes.
- `/portfolio`: holdings (instrument, type, weight, average cost, price, return, contribution, link to note). Options also show underlying, strike, expiry and days to expiry. Cash by currency. Closed positions with realised P&L and a link to the exit post-mortem.
- `/performance`: returns table vs benchmark, drawdown chart, metrics, attribution, and a short methodology summary linking to `/method`.
- `/research` and `/research/[slug]`: notes, newest first, filterable by status.
- `/journal`: every trade, newest first, generated from `trades.json` and linked to notes.
- `/method`: strategy, position sizing and review rules, performance methodology in plain English, trading policy, the AI + Human process, data sources, and the decision log.
- `/about` and `/disclaimer`.

Every page footer has the short disclaimer, "Last valued {date}", and a link to the public repo as the audit trail.

The headline sentence must read naturally whether the portfolio is up or down ("is now worth", not "grew to").

Home wireframe (figures illustrative only):

```
AlphaSeek                      Portfolio  Performance  Research  Journal  Method

A$10,000 invested on 3 Nov 2026 is now worth A$11,420.
The same amount in the S&P 500 is worth A$10,860.

┌───────────────────────────────────────────────────────────────────────┐
│  Equity curve: portfolio in accent, benchmark in grey, each line       │
│  labelled at its right end, no legend.                1M  3M  YTD  All │
└───────────────────────────────────────────────────────────────────────┘

Holdings                                  Latest
TEST:AAA      22.1%     +34.2%            3 Jun    Bought TEST:AAA
TEST:BBB      14.8%      −6.3%            28 May   New note: Why I own TEST:BBB
...

General information only, not personal advice. Full disclaimer
Last valued 4 Jun 2027                    View the ledger
```

## 14. Research notes

Frontmatter, validated by a Zod schema in the content config (values below are illustrative):

```yaml
title: Why I own TEST:AAA
instrument_id: TEST:AAA
published_at: 2026-11-03T09:30:00+11:00
status: open                  # open | exited | passed (researched, didn't buy)
price_at_publication: 48.20
currency: USD
fair_value: 71.00             # the owner's estimate per share
valuation_method: DCF
key_assumptions:
  wacc: 0.095
  terminal_growth: 0.03
  forecast_years: 10
sensitivity:                  # fair value per share, taken from the owner's model
  wacc: [0.085, 0.095, 0.105]
  terminal_growth: [0.02, 0.03, 0.04]
  values:
    - [78.1, 84.9, 94.0]
    - [66.2, 71.0, 77.3]
    - [57.4, 60.9, 65.3]
kill_criteria:
  - Net revenue retention below 110% for two consecutive quarters
ai:
  used_for: [filing summaries, first-draft thesis, comparable companies screen]
  human: [model inputs, valuation, decision]
  ai_fair_value: 64.00        # optional: independent AI estimate, logged before the owner's
model_file: /models/test-aaa-2026-11.xlsx
updates:
  - date: 2027-02-10
    fair_value: 74.00
    summary: Result ahead on margins; raised long-run margin assumption.
exit:                         # required when status is exited
  date: 2027-05-02
  reason: ...
  kill_criteria_triggered: false
  lessons: ...
```

Body sections, in order: summary (three sentences at most), thesis, valuation (`SnapshotPanel`, DCF summary, `SensitivityGrid`), risks, what would prove me wrong (`KillCriteria`), AI disclosure (`AiDisclosure`), update log (`UpdateLog`).

The snapshot panel shows: published date, price at publication, current price with its "as of" date, the owner's fair value estimate, implied upside, current position size, and status. Label the estimate "My fair value estimate", never "target".

## 15. Disclaimer (owner-approved; not legally reviewed)

Do not change this wording without owner approval.

Footer version:

> General information only, not personal advice. This site isn't provided under an Australian financial services licence. I own the investments discussed. High risk. [Full disclaimer]

Full version for `/disclaimer`:

**General information only.** This website contains general information only. It does not take into account your objectives, financial situation or needs. Before acting on anything here, consider whether it's appropriate for you, read any relevant disclosure documents, and consider getting advice from a licensed financial adviser.

**Not licensed advice.** I don't hold an Australian financial services licence, and this site isn't provided under one. It is a record of my own investments and my own views.

**My views only.** Opinions here are mine and don't represent any employer or organisation I'm associated with.

**Conflicts.** I own the investments I write about and may buy or sell them. Every trade is disclosed in the journal.

**High risk.** This portfolio is deliberately concentrated and high risk. Options can expire worthless, written options can lose more than the premium received, and crypto is highly volatile. You could lose some or all of your money.

**Past performance.** Past performance is not a reliable indicator of future performance. Returns are pre-tax and net of trading costs, calculated as described on the Method page.

**Use of AI.** Research on this site is prepared with the help of AI tools and reviewed by me. Both AI and human analysis can contain errors.

**Accuracy.** Information may be incomplete, out of date or wrong. To the extent permitted by law, I accept no liability for any loss arising from use of this site.

## 16. Design

Direction: a research report, not a trading dashboard. Quiet, precise, left-aligned. The numbers and the chart do the work.

Principles:
- **The equity curve is the hero.** Home opens with one plain sentence and the chart. No stat cards or big-number tiles.
- **Colour carries meaning.** The single accent is reserved for the portfolio's own data: its line, its figures in comparisons, the owner's fair value estimates. The benchmark is always neutral grey.
- **Signs before colour.** Gains and losses always show + or − (U+2212). Green and red are secondary, so everything reads correctly without colour.
- **Tables are the main interface.** Right-aligned numbers, tabular figures, units in headers, light rules only where they help scanning.
- **One layout.** A single left-aligned column; prose at most about 68 characters wide; tables may extend to about 1040px and scroll horizontally on small screens.
- **Motion:** none on load. Chart hover shows a crosshair and values, nothing more.

Avoid: gradients, drop shadows, stat cards, stock photos, emoji, all-caps labels, eyebrow labels above headings, middle-dot separators in meta lines, arrows appended to link text, monospace for small labels, scroll-triggered animations.

Tokens (`src/styles/tokens.css`):

| Token      | Light   | Dark    |
|------------|---------|---------|
| `--bg`     | #FCFCFD | #0F141B |
| `--ink`    | #16202E | #E6E9EE |
| `--muted`  | #5E6875 | #97A1AE |
| `--rule`   | #E2E5EA | #26303C |
| `--accent` | #2346A0 | #8FA8F0 |
| `--gain`   | #17744A | #4CC38A |
| `--loss`   | #B42318 | #F97066 |

Dark mode follows `prefers-color-scheme`, with a manual toggle remembered in `localStorage`.

Type:
- IBM Plex Sans for UI, headings, labels and table headers.
- IBM Plex Mono for figures in tables and other data — prices, weights, returns, dates in tables — at 0.9em. Labels stay in Plex Sans, so data reads as data without the page becoming a terminal. This is the one place monospace is used; see the avoid list above.
- Source Serif 4 for long-form note body text: 18px, line-height 1.6.
- 16px base for UI, scale ratio 1.25, sentence case everywhere.
- `font-variant-numeric: tabular-nums` on the body, so any figure outside the mono face still aligns.

Links are ink with a quiet underline, never the accent: the accent belongs to the portfolio's own data, and spending it on navigation would stop it meaning anything.

Formatting:
- Currency: `A$` for AUD, `US$` for USD. Thousands separators. Percentages to one decimal place.
- Dates: `3 Nov 2026`. Times with AEST or AEDT.
- Negative numbers use the minus sign (U+2212), not a hyphen.

## 17. Quality bar

- Lighthouse 95+ in every category on home, portfolio and a note page.
- WCAG 2.2 AA; visible keyboard focus; `prefers-reduced-motion` respected; every chart has a table alternative.
- Works down to 360px wide.
- No cookies and no third-party requests at runtime.
- Pipeline tests with hand-calculated expected values for: TWR with a mid-period deposit; FX conversion cost; a US dividend with withholding tax; a stock split; a long option expiring worthless; a short option assigned; short option valuation; crypto over a weekend; stale price carry-forward.

## 18. Build phases

**Phase 1: MVP**
1. Scaffold the Astro site, pipeline package and CI.
2. Ledger schemas, validation, and tests with fixtures.
3. Price adapters: ASX and US equities/ETFs, FX, crypto. Options via manual marks.
4. Valuation, NAV, TWR, benchmark, shadow benchmark, metrics.
5. Pages from section 13, using the design system in section 16.
6. Content lint, daily workflow and deployment.

Done when: with only the inception deposit in the ledger, the site builds, deploys, and shows A$10,000 against the benchmark from the inception date, updating daily.

**Phase 2: trust and depth**
- Option price adapter and daily quote archive.
- Broker reconciliation, with "Reconciled with broker statement on {date}" on `/portfolio`.
- Disclosure lag: CI finds the commit that first added each trade and shows the gap between execution and disclosure in the journal. No policy window is stated in the repo (see the 2026-09-20 trading policy decision), so show the gap without flagging; add flagging only if the owner publishes a window. Commit times are self-reported, so present this as transparency, not proof.
- AI vs Human scoreboard on `/method`: for notes with `ai_fair_value`, compare both estimates with the price after 6 and 12 months. Say plainly that this is an imperfect measure of valuation quality.
- Attribution chart, interactive sensitivity grid, RSS feed, Open Graph images per note, email signup (ask the owner which provider).

**Phase 3: publishing**
- Monthly letters, video pages and social links.

## 19. Decision log

Append rows; never delete.

| Date       | Decision                                  | Reason                                                   |
|------------|-------------------------------------------|----------------------------------------------------------|
| 2026-09-19 | Benchmark: IVV total return in AUD        | Base currency is AUD; investable; net of fees            |
| 2026-09-19 | Time-weighted return, end-of-day flows    | Contributions shouldn't distort reported returns         |
| 2026-09-19 | Shadow benchmark for dollar comparisons   | Shows the same dollars in the S&P 500                    |
| 2026-09-19 | Static site, ledger in a public repo      | A verifiable record with nothing to run server-side      |
| 2026-09-19 | Broker: Interactive Brokers               | Owner's choice; covers ASX/US equities, options and multi-currency cash. IBKR's own market data feed is private-use only, so a separate provider is still needed for public prices |
| 2026-09-19 | Rejected Stooq as a price source           | Its CSV endpoints now require solving a client-side JavaScript proof-of-work challenge before responding (confirmed live on stooq.com and stooq.pl); scripting around that in an automated job means building a bot-detection bypass, which is fragile and likely against its terms |
| 2026-09-19 | Equities/ETFs: Twelve Data                | Free-tier API with a registered key; better reported ASX/global exchange coverage than the alternative considered (Alpha Vantage), which is US-focused and rate-limited to 25 requests/day on the free tier |
| 2026-09-19 | FX: Frankfurter (ECB reference rates)     | Free, keyless, no signup; confirmed live for both single-date and date-range AUD/USD lookups; no redistribution concern since only derived AUD figures are published |
| 2026-09-19 | Crypto: CoinGecko                          | Free public API works unauthenticated for current and recent (< 365 day) history, confirmed live; matches section 8's requirement for an AUD quote where available |
| 2026-09-19 | IVV distribution history: owner-maintained, sourced from iShares | Free APIs don't carry ASX ETF distribution history; iShares publishes it officially. Recorded in `data/benchmark/ivv_distributions.csv`, maintained like a manual mark rather than fetched automatically |
| 2026-09-20 | IBM Plex Mono for figures in tables      | Owner chose a deliberately technical read over the plainer alternative. Labels and headings stay in Plex Sans, so the avoid-list bar on monospace for labels still holds |
| 2026-09-20 | `status.json` carries the inception deposit and date | The home headline ("A$10,000 invested on … is now worth …") was hardcoding the deposit figure, against ground rule 1. It now reads both from the ledger |
| 2026-09-20 | ASX prices: Yahoo Finance, not Twelve Data | Verified against a live key: Twelve Data's free tier rejects ASX symbols ("available starting with the Pro or Venture plan"), and Pro is US$99/month — over 10% a year of a A$10,000 portfolio, for delayed AU data. Yahoo serves ASX free, in AUD, and answers ordinary requests, so unlike Stooq nothing is being circumvented. It is undocumented, so manual marks stay the fallback and the build fails loudly on a missing price |
| 2026-09-20 | Hosting: GitHub Pages, not Cloudflare Pages or Vercel | The site is a static build that already lives on GitHub, so Pages needs no third-party account or repo linking and publishes from the same Actions run as everything else — including the commits `daily.yml` makes, so a new valuation deploys itself. Trade-off accepted: no per-branch preview deploys |
| 2026-09-20 | Twelve Data kept for US equities/ETFs | Its free tier covers US markets properly, so the official API is used where it actually works and Yahoo is limited to where there is no free alternative. Routing is per-instrument via `price_source`, which the adapter design already supported |
| 2026-09-20 | Site name: AlphaSeek; domain deferred | Owner's choice, already matching the repo. Raised with the owner that Seeking Alpha is an established site in the same field and that the name would sit alongside the other compliance questions; owner confirmed regardless. No custom domain yet: GitHub Pages serves the site meanwhile, and `src/lib/url.ts` makes a later move a base-path change |
| 2026-09-20 | `holdings.json` keeps publishing per-unit prices | Owner's call. Showing the price a holding's return was computed from keeps each row checkable against the ledger, which is the standard section 1 sets when verifiability and caution pull apart |
| 2026-09-20 | Trading policy handled by the owner, not the repo | Owner sets and applies the disclosure window personally; no window is encoded, enforced or checked in this repo. Phase 2's disclosure-lag feature would measure against a stated window, so it needs one on the Method page before it can mean anything |
| 2026-09-20 | Disclaimer published without legal review | Owner judged the section 15 draft sufficient on the basis that it states the site is not financial advice and documents a personal portfolio. Recorded plainly because it is a departure from the original plan to have a financial services lawyer review the wording, and because a self-declared "not advice" notice does not by itself determine how the content is characterised |
| 2026-09-20 | Employer compliance approval obtained | Owner confirmed. Not evidenced in this repo, by design — nothing about the employer is recorded here (ground rule 8) |
| 2026-09-26 | Owner stays anonymous (ground rule 8 widened) | Owner's choice. Rule 8 previously covered only the employer; it now covers name, email, location, job and credentials |
| 2026-09-26 | Git history rewritten to remove identifying details | Owner's call. Earlier commits carried a personal author email and lines in this file that identified the owner. Commit emails were replaced with a GitHub noreply address and those lines removed from every past version; all other content, dates and messages are unchanged. Commit hashes changed as a result. A deliberate exception to git history as the audit trail, recorded here so it is not silent |
| 2026-09-26 | Section 15 synced to the published disclaimer | The owner had already edited `src/content/pages/disclaimer.md` (removing the trademark line and the trading-policy reference in the conflicts paragraph) without updating this file. No wording changed on the site |
| 2026-09-26 | "risk-free" removed from the content lint | Owner's call. "Risk-free rate" is a standard input to the WACC and CAPM figures every DCF note reports, so the ban blocked ordinary valuation language. The remaining phrases still catch promissory copy such as "guaranteed" and "can't lose" |
