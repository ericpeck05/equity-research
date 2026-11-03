---
name: snapshot
description: Build a one-page snapshot of a company (business, financial trends, valuation, recent filings, open questions). Use when the user says "snapshot", "tell me about $TICKER", "first look at", or starts work on a new company.
---

# Company snapshot

Goal: in ~1 page, get the owner oriented on a company they may cover. Ticker is in the request.

## Steps
1. Run, from the repo root:
   - `python research.py financials TICKER`
   - `python research.py market TICKER`
   - `python research.py filings TICKER --forms 10-K 10-Q 8-K --limit 10`
   - `python research.py section TICKER business` (latest 10-K, Item 1)
   If any command fails, stop and report the error; don't substitute remembered numbers.
2. Read the extracted business section (`coverage/TICKER/sections/`) and the annual table.
3. Write `coverage/TICKER/snapshot.md` with the structure below, then show the owner a short summary.

## Structure
- **What they sell and to whom**: segments, customers, how they make money (cite Item 1).
- **Financial trajectory** (5-6 yrs): revenue growth, gross and operating margin, FCF and FCF
  after stock comp, net cash. Point out the 2-3 trends that matter most and why.
- **Valuation now**: price, market cap, EV/Revenue, P/E fwd, FCF yield (Yahoo, label as such).
- **Recent filings**: last 10-K/10-Q dates; any notable 8-Ks.
- **What the market is probably debating**: list as *questions*, not answers. Mark these
  as your inference.
- **Questions for the owner**: 3 things they should form a view on before going deeper.

Close by asking whether to move on to `filing-review`, `what-changed`, or comps
(`python research.py comps --subsector <subsector from coverage/universe.csv>`).
