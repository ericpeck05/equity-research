---
name: snapshot
description: Build a company snapshot web page (business, financial trends, valuation vs peers, commitments, recent filings, debates, open questions). Use when the user says "snapshot", "tell me about $TICKER", "first look at", or starts work on a new company.
---

# Company snapshot

Goal: a one-screen-per-section research page that gets the owner oriented on a company.
The deliverable is `coverage/TICKER/snapshot.json` rendered to `docs/TICKER.html`.

## Gather (from the repo root)
1. `python research.py financials TICKER`
2. `python research.py market TICKER`
3. `python research.py filings TICKER --forms 10-K 10-Q 8-K --limit 12`
4. `python research.py section TICKER business` and `python research.py section TICKER mdna --form 10-Q`
5. Read every recent 8-K (`python research.py fetch TICKER --form 8-K --index N`). For the latest
   earnings 8-K (item 2.02), open the filing folder's `index.json` and read the press release and
   any CFO commentary exhibit for guidance.
If any command fails, stop and report the error; never substitute remembered numbers.

## Write coverage/TICKER/snapshot.json
Copy the structure of `coverage/NVDA/snapshot.json` exactly (same keys). Rules:
- `tag` is `F` (fact from a filing), `M` (management claim or guidance) or `I` (your inference).
  Every `F`/`M` item has a `src` naming the filing and section.
- `takeaways`: 4-6 items, the things a PM must know. `headline`: one sentence with the core tension.
- `exposures`: commitments, guarantees, receivables, debt or anything material outside the income
  statement, with values from the filings. Use what's relevant for this company (e.g. RPO and
  deferred revenue for software).
- `debates`: what the market is likely arguing about, as questions. `questions`: 3 for the owner.
- `subsector` must match `coverage/universe.csv` so the peer comps load.

## Build and show
1. `python research.py site TICKER` (writes `docs/TICKER.html` and refreshes `docs/index.html`).
2. In a cloud session, also pass `--fragments <scratchpad>/site` and publish
   `<scratchpad>/site/TICKER.html` with the Artifact tool so the owner can open it.
3. Commit and push. Summarize the 3 most important findings in chat and ask the owner the
   questions from the page.
