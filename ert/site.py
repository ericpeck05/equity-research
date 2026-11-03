"""Build the research website: one self-contained HTML page per company plus an index.

Output goes to docs/ so GitHub Pages can serve it straight from the repo
(Settings -> Pages -> Deploy from branch -> main /docs).
"""
from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path

from . import config, financials, market, sec

WEB = Path(__file__).resolve().parent / "web"
OUT = config.ROOT / "docs"


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _table(df) -> dict:
    return {"periods": [str(c) for c in df.columns],
            "rows": {m: [_clean(float(x)) if x == x else None for x in df.loc[m]] for m in df.index}}


def _universe() -> list[dict]:
    with open(config.COVERAGE_DIR / "universe.csv", newline="") as f:
        return list(csv.DictReader(f))


def _render(template: str, data: dict, ticker: str = "") -> str:
    """Page body as a fragment (title, styles, markup, script)."""
    css = (WEB / "base.css").read_text(encoding="utf-8")
    payload = json.dumps(data, default=str).replace("</", "<\\/")
    return ((WEB / template).read_text(encoding="utf-8").replace("/*__CSS__*/", css)
            .replace("__TICKER__", ticker).replace("__DATA__", payload))


def _document(fragment: str) -> str:
    """Wrap a fragment as a full HTML document for GitHub Pages / opening locally."""
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
            f'</head>\n<body>\n{fragment}\n</body>\n</html>\n')


def _write(name: str, fragment: str, fragment_dir: Path | None) -> Path:
    OUT.mkdir(exist_ok=True)
    out = OUT / name
    out.write_text(_document(fragment), encoding="utf-8")
    if fragment_dir:
        fragment_dir.mkdir(parents=True, exist_ok=True)
        (fragment_dir / name).write_text(fragment, encoding="utf-8")
    return out


def build_company(ticker: str, with_comps: bool = True, fragment_dir: Path | None = None) -> Path:
    t = ticker.upper()
    snap_path = config.COVERAGE_DIR / t / "snapshot.json"
    snap = json.loads(snap_path.read_text(encoding="utf-8")) if snap_path.exists() else {}

    co = sec.lookup(t)
    ann, qtr, _ = financials.build(sec.company_facts(co), years=6)
    val = market.valuation(t)
    hist = market.price_history(t, "1y")
    price = [[d.strftime("%Y-%m-%d"), round(float(c), 2)] for d, c in hist.items()]

    uni = {r["ticker"]: r for r in _universe()}
    sub = snap.get("subsector") or uni.get(t, {}).get("subsector", "")
    comps = []
    if with_comps and sub:
        peers = [r["ticker"] for r in uni.values() if r["subsector"] == sub]
        if t not in peers:
            peers.insert(0, t)
        df = market.comps(peers)
        for tk, row in df.iterrows():
            if str(row.get("Company", "")).startswith("error"):
                continue
            entry = {"ticker": tk, **{k: _clean(v) for k, v in row.items() if k != "Sources"}}
            entry["Company"] = uni.get(tk, {}).get("name", entry.get("Company"))
            comps.append(entry)

    data = {
        "ticker": t, "company": co.name, "subsector": sub, "generated": date.today().isoformat(),
        "snap": snap, "val": {k: _clean(v) for k, v in val.items()}, "price": price,
        "annual": _table(ann), "quarterly": _table(qtr.iloc[:, -12:]), "comps": comps,
        "secUrl": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={co.cik}&type=10-K",
    }
    return _write(f"{t}.html", _render("company.html", data, t), fragment_dir)


def build_index(fragment_dir: Path | None = None) -> Path:
    covered = []
    for d in sorted(config.COVERAGE_DIR.iterdir()):
        s = d / "snapshot.json"
        if d.is_dir() and s.exists() and (OUT / f"{d.name}.html").exists():
            j = json.loads(s.read_text(encoding="utf-8"))
            covered.append({"ticker": d.name, "name": j.get("name", d.name), "subsector": j.get("subsector", ""),
                            "headline": j.get("headline", ""), "prepared": j.get("prepared", "")})
    calls = []
    calls_path = config.COVERAGE_DIR / "calls.csv"
    if calls_path.exists():
        with open(calls_path, newline="") as f:
            calls = list(csv.DictReader(f))
    data = {"covered": covered, "universe": _universe(), "calls": calls, "generated": date.today().isoformat()}
    return _write("index.html", _render("index.html", data), fragment_dir)
