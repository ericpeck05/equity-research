---
name: what-changed
description: Compare a section (risk factors, MD&A, legal, etc.) between two filings and explain what the changes mean. Use for "what changed", "compare to last year", "new risk factors", "red-line the 10-K".
---

# What changed

## Steps
1. Run `python research.py diff TICKER <section> --form 10-K` (latest vs prior year).
   For quarters: `--form 10-Q` compares the latest 10-Q to the one before; use
   `--old 3` to compare to the same quarter last year (10-Qs come 3 per year).
2. Read the report it saves in `coverage/TICKER/diffs/`.
3. Ignore pure wording/formatting churn. Focus on changes that touch substance:
   new risks, removed risks, new numbers, changed tone ("may" -> "has", "expect" -> "may").
4. Write a summary at the top of the diff file under `## Analyst summary`, and tell the owner:
   - The 3-5 changes that matter most, each quoting old vs new wording.
   - Why each could matter for revenue, margins, or valuation.
   - Which ones are worth asking management about.
Mark interpretation as interpretation.
