"""Command line: python research.py <command> ...  (run with -h for help)."""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

import pandas as pd

from . import config, diff, financials, sections, sec


def _out_dir(ticker: str) -> Path:
    d = config.COVERAGE_DIR / ticker.upper()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pick_filing(ticker: str, form: str, index: int) -> tuple[sec.Company, sec.Filing]:
    co = sec.lookup(ticker)
    fs = sec.filings(co, forms=(form,), limit=index + 1)
    if len(fs) <= index:
        raise SystemExit(f"Only {len(fs)} {form} filings found for {ticker}.")
    return co, fs[index]


def cmd_filings(a):
    co = sec.lookup(a.ticker)
    print(f"{co.name} ({co.ticker}), CIK {co.cik}\n")
    for i, f in enumerate(sec.filings(co, forms=tuple(a.forms), limit=a.limit)):
        print(f"[{i}] {f.form:<6} filed {f.filing_date}  period {f.report_date or '-':<10}  {f.url}")


def cmd_fetch(a):
    co, f = _pick_filing(a.ticker, a.form, a.index)
    path = sec.filing_text_path(f)
    print(f"{co.name} {f.form} filed {f.filing_date} (period {f.report_date})")
    print(f"Source: {f.url}")
    print(f"Text saved to: {path}")


def cmd_section(a):
    co, f = _pick_filing(a.ticker, a.form, a.index)
    body = sections.extract(sec.filing_text(f), a.section)
    if not body:
        raise SystemExit(f"Couldn't find '{a.section}' in this {f.form}. Read the full text with `fetch` instead.")
    out = _out_dir(a.ticker) / "sections" / f"{f.form}_{f.report_date}_{a.section}.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text(f"SOURCE: {co.name} {f.form} for period {f.report_date}, filed {f.filing_date}\n"
                   f"URL: {f.url}\n\n{body}", encoding="utf-8")
    print(f"{len(body.split()):,} words -> {out}")


def cmd_diff(a):
    co = sec.lookup(a.ticker)
    fs = sec.filings(co, forms=(a.form,), limit=max(a.old, a.new) + 1)
    if len(fs) <= max(a.old, a.new):
        raise SystemExit(f"Not enough {a.form} filings for that comparison.")
    old_f, new_f = fs[a.old], fs[a.new]
    old_t = sections.extract(sec.filing_text(old_f), a.section)
    new_t = sections.extract(sec.filing_text(new_f), a.section)
    if not old_t or not new_t:
        raise SystemExit(f"Couldn't find '{a.section}' in one of the filings.")
    md, stats = diff.compare(old_t, new_t, f"{a.form} {old_f.report_date}", f"{a.form} {new_f.report_date}")
    md = (f"Company: {co.name}  \nOld: {old_f.url}  \nNew: {new_f.url}\n\n" + md)
    out = _out_dir(a.ticker) / "diffs" / f"{a.section}_{old_f.report_date}_vs_{new_f.report_date}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(stats)
    print(f"Report -> {out}")


def cmd_financials(a):
    co = sec.lookup(a.ticker)
    ann, qtr, src = financials.build(sec.company_facts(co), years=a.years)
    d = _out_dir(a.ticker)
    ann.to_csv(d / "financials_annual.csv")
    qtr.to_csv(d / "financials_quarterly.csv")
    financials.to_excel(co.ticker, ann, qtr, src, d / "financials.xlsx")
    with_pct = ann.copy()
    print(f"{co.name}: annual ($M where money)\n")
    money = [i for i in with_pct.index if "%" not in i and i != "Diluted EPS"]
    with_pct.loc[money] = with_pct.loc[money] / 1e6
    print(with_pct.to_string(float_format=lambda v: f"{v:,.2f}" if abs(v) < 20 else f"{v:,.0f}"))
    print(f"\nSaved: {d / 'financials.xlsx'} (+ CSVs). Every number is traced on the 'Sources' sheet.")


def _fmt(v):
    if isinstance(v, float):
        return f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}"
    return "n/a" if v is None else str(v)


def cmd_market(a):
    from . import market
    for k, v in market.valuation(a.ticker, price=a.price).items():
        print(f"{k:<24} {_fmt(v)}")


def _universe() -> list[dict]:
    with open(config.COVERAGE_DIR / "universe.csv", newline="") as f:
        return list(csv.DictReader(f))


def cmd_comps(a):
    from . import market
    tickers = a.tickers
    if a.subsector:
        tickers = [r["ticker"] for r in _universe() if r["subsector"].lower() == a.subsector.lower()]
        if not tickers:
            subs = sorted({r["subsector"] for r in _universe()})
            raise SystemExit(f"No tickers in subsector {a.subsector!r}. Options: {', '.join(subs)}")
    if not tickers:
        raise SystemExit("Give tickers (comps NVDA AMD AVGO) or --subsector Semiconductors")
    df = market.comps(tickers)
    out = config.COVERAGE_DIR / "_comps" / f"comps_{(a.subsector or 'custom').replace(' ', '_')}_{date.today()}.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out)
    cols = [c for c in df.columns if c not in ("Company", "Sources")]
    show = df[cols].apply(pd.to_numeric, errors="coerce")
    print(show.to_string(float_format=lambda v: f"{v:,.1f}"))
    errors = df[df["Company"].astype(str).str.startswith("error")]
    for t, row in errors.iterrows():
        print(f"{t}: {row['Company']}")
    print("\nPrice from Yahoo; everything else from SEC filings (TTM = last 4 quarters).")
    print(f"\nSaved -> {out}")


def cmd_universe(a):
    for r in _universe():
        print(f"{r['ticker']:<6} {r['subsector']:<22} {r['name']}")


def cmd_site(a):
    from . import site
    frag = Path(a.fragments) if a.fragments else None
    tickers = [t.upper() for t in a.tickers] or sorted(
        d.name for d in config.COVERAGE_DIR.iterdir() if (d / "snapshot.json").exists())
    for t in tickers:
        print(f"Built {site.build_company(t, fragment_dir=frag)}")
    print(f"Built {site.build_index(fragment_dir=frag)}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="research.py", description="Free equity research data toolkit (SEC EDGAR + Yahoo).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("filings", help="list recent filings")
    s.add_argument("ticker"); s.add_argument("--forms", nargs="+", default=["10-K", "10-Q", "8-K"])
    s.add_argument("--limit", type=int, default=15); s.set_defaults(fn=cmd_filings)

    s = sub.add_parser("fetch", help="download a filing as plain text")
    s.add_argument("ticker"); s.add_argument("--form", default="10-K")
    s.add_argument("--index", type=int, default=0, help="0 = latest, 1 = the one before, ...")
    s.set_defaults(fn=cmd_fetch)

    s = sub.add_parser("section", help="extract one section of a filing")
    s.add_argument("ticker"); s.add_argument("section", choices=list(sections.SECTIONS))
    s.add_argument("--form", default="10-K"); s.add_argument("--index", type=int, default=0)
    s.set_defaults(fn=cmd_section)

    s = sub.add_parser("diff", help="what changed in a section between two filings")
    s.add_argument("ticker"); s.add_argument("section", choices=list(sections.SECTIONS))
    s.add_argument("--form", default="10-K")
    s.add_argument("--old", type=int, default=1); s.add_argument("--new", type=int, default=0)
    s.set_defaults(fn=cmd_diff)

    s = sub.add_parser("financials", help="build annual + quarterly financials (Excel)")
    s.add_argument("ticker"); s.add_argument("--years", type=int, default=6); s.set_defaults(fn=cmd_financials)

    s = sub.add_parser("market", help="price and valuation multiples")
    s.add_argument("ticker"); s.add_argument("--price", type=float, help="use this price instead of Yahoo's")
    s.set_defaults(fn=cmd_market)

    s = sub.add_parser("comps", help="comparable-company table")
    s.add_argument("tickers", nargs="*"); s.add_argument("--subsector")
    s.set_defaults(fn=cmd_comps)

    s = sub.add_parser("universe", help="list the tech coverage universe"); s.set_defaults(fn=cmd_universe)

    s = sub.add_parser("site", help="build the research website in docs/ (all snapshots if no tickers)")
    s.add_argument("tickers", nargs="*")
    s.add_argument("--fragments", help="also write body-only pages here (for publishing as artifacts)")
    s.set_defaults(fn=cmd_site)

    a = p.parse_args(argv)
    a.fn(a)
