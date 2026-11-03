# Equity Research Workspace (Tech Sector)

A free, AI-assisted system for doing professional-style equity research on technology
companies. **You don't need to code.** You talk to Claude Code; Claude runs the tools,
reads the filings and drafts the work. You make the calls.

Costs nothing beyond your Claude subscription: data comes from SEC EDGAR (free, official)
and Yahoo Finance (free, unofficial). No API keys.

## What you can say to Claude

| You say | What happens |
|---|---|
| "Snapshot NVDA" | One-page overview: business, 6-year financial trends, valuation, open questions |
| "Review MSFT's latest 10-K" | Deep read of the annual report with cited notes on drivers, risks and red flags |
| "What changed in CRWD's risk factors?" | Red-lines this year's filing against last year's and explains what matters |
| "Comps for semiconductors" | Valuation table for the peer group |
| "AAPL just reported, do an earnings update" | Post-earnings note checked against your thesis |
| "Help me initiate on AMD" | Step-by-step full initiation report, with you making the calls |
| "Red team my thesis" / "Mock interview me on my AMD pitch" | A tough PM tears into your work |
| "Log my call on AMD" / "How's my track record?" | Date-stamped ratings and targets, scored over time |

## Where things go
```
coverage/
  universe.csv          tech companies by subsector (edit freely)
  calls.csv             every rating/target you've logged
  NVDA/
    financials.xlsx     annual + quarterly financials, with a Sources sheet tracing every number
    snapshot.md, initiation.md, notes/, diffs/, sections/
    thesis_log.md       your dated calls and reasoning (your track record)
templates/              note formats (initiation, earnings, thesis log)
.claude/skills/         the research workflows Claude follows
```

## A suggested path to get interview-ready
1. **Pick 1 subsector** (e.g. semiconductors or software) and 3-4 companies in it.
2. For each: snapshot → 10-K review → what-changed. Learn the KPIs that matter for that
   subsector (e.g. data center revenue for chips, net revenue retention for software).
3. **Initiate on one company** with a real thesis. Red-team it until you can defend it.
4. Log the call, then do an earnings update every quarter. After a year you'll have a
   real, dated track record and a writing portfolio to show employers.
5. Learn to rebuild the model in Excel yourself. Interviews test that you can, so use the
   tool to check your work, not to replace it.

## One-time setup (Claude can do this for you)
```bash
pip install -r requirements.txt
cp config.example.toml config.toml
```
Then put your name and email in `config.toml`. The SEC requires it to identify who is
downloading; it isn't shared anywhere else. `config.toml` is never uploaded to GitHub.

**Cloud sessions:** the environment's network access must allow `www.sec.gov`,
`data.sec.gov`, `query1.finance.yahoo.com` and `query2.finance.yahoo.com`.

## For Claude / developers
`python research.py -h` lists the commands (`filings`, `fetch`, `section`, `diff`,
`financials`, `market`, `comps`, `universe`). Tests: `python -m pytest -q` (offline).
Research rules live in `CLAUDE.md`.
