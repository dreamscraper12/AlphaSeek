---
title: Method
---

Everything on this site is computed from a ledger of plain-text files in the [public repository](https://github.com/dreamscraper12/AlphaSeek). No figure on any page is typed in by hand. If you want to check a number, both the inputs and the code that turns them into that number are there.

## Strategy

High growth, high risk, unconstrained. Holdings may include ASX and US equities, ETFs, options including short-dated contracts, and crypto. The portfolio started with A$10,000 and is measured against the S&P 500 in Australian dollars.

Most of the portfolio, around 75%, sits in a core of 4–6 high-growth companies I've valued in depth and plan to hold for years. The rest is a satellite for higher-risk ideas, including early-stage companies, options and crypto, where I size small and expect big swings both ways. Every position, core or satellite, has a published thesis and the conditions that would prove me wrong.

## Position sizing and review rules

Before buying, I estimate how far a position could fall if my thesis is wrong, and I size it so that loss would cost no more than 5% of the portfolio. A stock whose bear case is −50% gets up to 10%; one that could fall 80% gets about 6%.

I review every position after each earnings report against the conditions in its note, and if one is met I sell, whatever the price. A 30% fall from cost doesn't force a sale; it forces a written re-underwrite in the journal within a week that answers one question: would I buy it today at this price? I trim when the price is more than 20% above my fair value estimate, and I sell when my updated estimate falls below the price.

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

Every trade is disclosed in the journal, with the date it was executed.

I set and apply my own rules on when I trade relative to publishing a note. Those rules are not published here, and nothing in this repository enforces or checks them.

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
