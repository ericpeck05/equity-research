---
name: earnings-update
description: Produce a post-earnings note after a company reports a quarter (10-Q / 8-K earnings release). Use for "earnings update", "they just reported", "how was the quarter".
---

# Earnings update

## Steps
1. `python research.py filings TICKER --forms 8-K 10-Q --limit 6`. The earnings press
   release is usually an 8-K (Item 2.02) filed on the report date; its exhibit 99.1 holds
   the release. Fetch it with `python research.py fetch TICKER --form 8-K --index N` and if
   the primary document is only a cover page, open the filing index URL listed by
   `filings` (replace the doc name with the folder) and read exhibit 99.1.
2. `python research.py financials TICKER` to refresh the quarterly table (if the 10-Q is
   out). Compare the latest quarter to the same quarter last year and the prior quarter.
3. Read `coverage/TICKER/thesis_log.md` if it exists. The point of the note is: **does
   this quarter support or hurt the owner's thesis?**
4. Ask the owner what consensus expected (they can get it from free sources such as Yahoo
   Finance's analysis tab, the company's IR site, or news). Don't guess consensus.
5. Write `coverage/TICKER/notes/earnings_<period>.md` using `templates/earnings_note.md`.

Keep it to what a PM would read in 2 minutes: headline numbers vs last year and vs
expectations, guidance change, the 2-3 things that matter, thesis impact, questions.
