---
title: Method
---

Everything on this site is computed from a ledger of plain-text files in the [public repository](https://github.com/dreamscraper12/AlphaSeek). No figure on any page is typed in by hand. If you want to check a number, both the inputs and the code that turns them into that number are there.

## Strategy

High growth, high risk, unconstrained. Holdings may include ASX and US equities, ETFs, options including short-dated contracts, and crypto. The portfolio started with A$10,000 and is measured against the S&P 500 in Australian dollars.

_A fuller description of what I look for is still to be written._

## Position sizing and review rules

_Still to be written._

## Performance methodology

**Value.** Each business day, the portfolio is worth the market value of every holding plus cash in every currency, converted to Australian dollars.

**Returns.** Returns are time-weighted. Each day's return removes any deposit or withdrawal before measuring, so paying more money in never shows up as performance. Those daily returns are chain-linked into an index starting at 10,000 on the close before the first deposit.

**Comparison.** The benchmark is the ASX-listed iShares S&P 500 ETF (IVV), measured as a total return in Australian dollars with distributions reinvested on the ex-date, and indexed from the same starting point in the same way. The dollar chart compares what the portfolio is actually worth against the same deposits put into IVV instead.

**What is included.** Returns are after trading costs and currency conversion costs, and before tax. Dividends, interest, fees and withholding tax change what the portfolio is worth, but are not treated as contributions.

**Timing.** ASX holdings use the close on the valuation day. US holdings use the close of the US session for that day. One daily AUD/USD rate is used throughout. Crypto uses the price at midnight UTC ending that day. The site revalues each weekday morning, Sydney time, once both markets have closed.

**Weekends.** There are no valuation points on weekends. Crypto trades continuously, so a weekend move appears in Monday's value.

**Gaps.** If a price is not available — a public holiday, say — the last available price is carried forward and marked stale, and the holding shows the date its price is actually from.

**Options.** There is no free source of historical option prices, so options are valued from marks recorded by hand in the ledger, each citing where it came from. A written option carries negative value, because closing it costs money.

## Trading policy

_Still to be written._ The disclaimer refers readers to a trading policy on this page. Until the disclosure window is set out here, that reference is incomplete.

## The AI + Human process

AI helps with research: summarising filings, drafting a first pass at a thesis, screening comparable companies. Every valuation input, every judgement and every trading decision is mine. Each research note sets out where AI was used and where it was not.

Both AI and human analysis can be wrong, and this arrangement does not make either less likely.

## Data sources

| What | Source |
| --- | --- |
| US equities and ETFs | Twelve Data |
| ASX equities and ETFs | Yahoo Finance |
| AUD/USD | Frankfurter, using European Central Bank reference rates |
| Crypto | CoinGecko |
| Options | marks recorded by hand in the ledger |
| IVV distributions | iShares' published distribution history, entered by hand |

All prices are end-of-day closes. Nothing here is intraday.

## Decision log

Every methodology and site decision is recorded, with its reason and its date, in section 19 of the [project brief](https://github.com/dreamscraper12/AlphaSeek/blob/master/CLAUDE.md). Rows are appended and never removed, including the decisions that turned out to be wrong.
