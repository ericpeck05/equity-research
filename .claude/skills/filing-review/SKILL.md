---
name: filing-review
description: Read a 10-K or 10-Q in depth and produce cited notes. Use when the user asks to review/read/analyze a filing, annual report, 10-K or 10-Q, or asks a question that a filing answers.
---

# Filing review

## Steps
1. Find the filing: `python research.py filings TICKER --forms 10-K 10-Q`. Use the latest
   unless the owner names one (`--index N` picks older ones).
2. Extract sections: `python research.py section TICKER <section> --form 10-K|10-Q`
   for `business`, `risk_factors`, `mdna`, `market_risk`, `legal`. For a 10-Q, `business`
   doesn't exist; MD&A and risk factors are the core. If a section can't be found,
   `python research.py fetch ...` and read the full text file it prints.
3. Read the sections fully (big files: read in chunks; don't skim only the start).
4. Write `coverage/TICKER/notes/<form>_<period>_review.md`.

## What to pull out (each with a citation)
- **Segments and drivers**: what drove revenue and margin changes, in management's words
  (quote) and in numbers.
- **Guidance or outlook language**, and how hedged it is.
- **Capital allocation**: buybacks, dividends, capex plans, M&A.
- **Customer / supplier concentration**, backlog, remaining performance obligations,
  deferred revenue (big for software).
- **Accounting items**: revenue recognition changes, unusual one-offs, stock comp,
  non-GAAP adjustments.
- **Risks that are specific to this company**, not boilerplate. Note which are new
  (suggest running `what-changed`).
- **Red flags or things that don't add up** between MD&A and the financial table.
- **Open questions** for the owner to think about or ask management.

When the owner asks a question about the filing, answer from the text with a quote and
section reference. If the filing doesn't answer it, say so.
