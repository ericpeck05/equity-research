---
name: initiate
description: Guide the owner through writing a full initiation-of-coverage report on a company. Use for "initiate on", "write an initiation", "full report", "investment thesis for".
---

# Initiation of coverage

This is the flagship deliverable and a portfolio piece. **The owner does the thinking; you
do the legwork and coaching.** Work in stages and check in after each one.

## Stages
1. **Groundwork** (you): run `snapshot`, `filing-review` on the latest 10-K, and
   `what-changed` on risk factors if not already in `coverage/TICKER/`. Build comps:
   `python research.py comps --subsector <subsector>` (see `coverage/universe.csv`).
2. **Thesis interview** (owner): ask the owner, one at a time:
   - What does the market believe about this stock? (Have them find evidence: price action,
     multiple vs peers, news.)
   - Where do you disagree, and why? (variant perception)
   - What has to be true for you to be right, and how will you know? (KPIs)
   - What would make you wrong?
   Push back on vague answers. A thesis needs to be specific and testable.
3. **Model** (together): from `coverage/TICKER/financials.xlsx`, build a forecast sheet for
   3 years: revenue by driver, gross margin, opex, FCF. **The owner chooses every
   assumption**; you show the history next to each one and point out assumptions far from it.
   Add bull / base / bear cases.
4. **Valuation** (together): a multiple-based target (vs comps, explained) and a simple DCF
   as a cross-check. Show sensitivity to the 2 assumptions that matter most.
5. **Write** (you draft, owner edits): fill `templates/initiation_note.md` into
   `coverage/TICKER/initiation.md`. Every fact cited.
6. **Red team**: run the `red-team` skill on the draft before calling it done.
7. **Log it**: run `log-call` to record the rating, target and thesis with today's date.
