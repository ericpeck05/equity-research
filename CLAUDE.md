# Equity Research Workspace

This repo is a personal equity research system for the **technology sector**. The owner
is training for a career in sell-side/buy-side equity research and does not write code:
Claude does the coding and the data work, the owner does the judgment.

## How the pieces fit
- `python research.py <command>` pulls **free** data: SEC EDGAR (filings, XBRL financials)
  and Yahoo Finance via yfinance (prices, multiples). Run `python research.py -h`.
- `.claude/skills/` holds the research workflows (snapshot, filing review, what-changed,
  earnings update, initiation, red team, log a call). Claude is the analysis layer; there is
  no paid API.
- `coverage/<TICKER>/` is where all work on a company lives: financials.xlsx, extracted
  sections, diffs, notes, and `thesis_log.md`.
- `templates/` has the note formats. `coverage/universe.csv` is the tech coverage universe.

## Research rules (follow on every task)
1. **Cite everything.** Every factual claim gets a source: filing type + period + section
   (e.g. "10-K FY2025, Item 1A") or the Sources sheet row in financials.xlsx. Quote short
   passages for anything important. If you can't source it, say so.
2. **Never invent numbers.** Numbers come from the toolkit output or a filing you read. If a
   command fails (network, missing data), stop and report it; do not fill gaps from memory.
   Your training knowledge may be out of date: label it "background, unverified" if used.
3. **Separate facts, management's claims, and opinion.** Mark which is which.
4. **The owner makes the calls.** Ratings, price targets and forecast assumptions are the
   owner's. Suggest, challenge and stress-test, but ask for their view before writing a
   thesis or target, and record their reasoning in their words.
5. **Teach as you go.** The owner is building skills for interviews. Briefly explain why a
   metric or change matters for *this* business (one or two sentences, not lectures).
6. Yahoo data is unofficial; prefer SEC numbers when both exist and flag big mismatches.
7. Save outputs into `coverage/<TICKER>/` so work accumulates. Never edit past entries in a
   `thesis_log.md`; only append.

## Setup for a new machine/session
```
pip install -r requirements.txt
cp config.example.toml config.toml   # then put the owner's name + email in sec_user_agent
python -m pytest -q                  # offline tests
```
Network access to `www.sec.gov`, `data.sec.gov` and `query1/query2.finance.yahoo.com` is
required for live data.
