---
name: log-call
description: Record or update the owner's investment call (rating, price target, thesis, KPIs to watch) with a date stamp, or review the track record. Use for "log my call", "update my rating", "track record", "how are my calls doing".
---

# Log a call / review track record

## Logging
1. Ask the owner for: rating (Buy / Hold / Sell), price target and time horizon (default
   12 months), thesis in 2-3 sentences **in their own words**, the 2-3 KPIs that prove or
   disprove it, and what would make them change their mind.
2. Get the current price, and the benchmark's price (default XLK, the tech sector ETF):
   `python research.py market TICKER` and `python research.py market XLK`.
3. **Append** (never edit older entries) to `coverage/TICKER/thesis_log.md` using the format
   in `templates/thesis_log.md`, dated today.
4. Add or update the row for this ticker in `coverage/calls.csv`
   (columns: date,ticker,rating,price_at_call,target,horizon_months,benchmark,benchmark_price_at_call). Append a new row for
   each change; don't overwrite history.

## Track record review
For each row in `coverage/calls.csv`, get the current price, compute return since the call
and versus the target, and compare to the benchmark's return over the same period
(current benchmark price vs `benchmark_price_at_call`). Report hit rate and what the thesis log
says about why each call worked or didn't. Be honest about calls that went badly.
