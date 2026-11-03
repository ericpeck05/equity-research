"""Valuation: share price (Yahoo via yfinance) combined with SEC-reported fundamentals.

Everything except the price comes from SEC filings, so each multiple can be traced to a
source. Trailing-twelve-month (TTM) figures = the last four reported quarters.
If the price feed is unavailable, pass a price yourself (research.py market NVDA --price 200).
"""
from __future__ import annotations

import logging

import pandas as pd

from . import financials, sec

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def price_history(ticker: str, period: str = "1y") -> pd.Series:
    try:
        import yfinance as yf
    except ImportError:
        raise SystemExit("Run: pip install -r requirements.txt  (yfinance is missing)")
    h = yf.Ticker(ticker).history(period=period)
    if h.empty:
        raise RuntimeError(f"No price data returned for {ticker}")
    return h["Close"]


def _shares_outstanding(facts: dict, q: pd.DataFrame) -> tuple[float, str]:
    dei = facts.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding", {})
    rows = dei.get("units", {}).get("shares", [])
    if rows:
        latest = max(r["end"] for r in rows)
        # Companies with several share classes (e.g. GOOGL) report one row per class.
        same = {(r["accn"], r["val"]) for r in rows if r["end"] == latest}
        return float(sum(v for _, v in same)), f"shares outstanding as of {latest} (SEC cover page)"
    if "Diluted shares" in q.index:
        s = q.loc["Diluted shares"].dropna()
        return float(s.iloc[-1]), f"diluted weighted shares, quarter ending {s.index[-1]} (fallback)"
    raise RuntimeError("No share count found in SEC data")


def _last(q: pd.DataFrame, row: str) -> float:
    if row not in q.index:
        return 0.0
    s = q.loc[row].dropna()
    return float(s.iloc[-1]) if len(s) else 0.0


def valuation(ticker: str, price: float | None = None) -> dict:
    co = sec.lookup(ticker)
    facts = sec.company_facts(co)
    _, q, _ = financials.build(facts, years=3)

    price_note = "manual input"
    hist = None
    if price is None:
        try:
            hist = price_history(ticker)
            price = float(hist.iloc[-1])
            price_note = f"Yahoo close {hist.index[-1]:%Y-%m-%d}"
        except Exception as e:
            raise SystemExit(f"Couldn't get a price for {ticker} ({e}). Re-run with --price <price>.")

    shares, shares_note = _shares_outstanding(facts, q)
    rev = q.loc["Revenue"]
    if rev.iloc[-4:].isna().any():
        raise SystemExit(f"{ticker}: last four quarters of revenue aren't all available in SEC data.")

    def ttm(row, back=0):
        if row not in q.index:
            return None
        cols = q.columns[-4 - back: len(q.columns) - back]
        vals = q.loc[row, cols]
        return None if vals.isna().any() else float(vals.sum())

    mcap = price * shares
    cash = _last(q, "Cash & equivalents") + _last(q, "Short-term investments")
    debt = _last(q, "Long-term debt")
    ev = mcap + debt - cash
    r, r_prior = ttm("Revenue"), ttm("Revenue", back=4)
    gp, oi, ni, fcf = ttm("Gross profit"), ttm("Operating income"), ttm("Net income"), ttm("Free cash flow")
    da = ttm("D&A")
    ebitda = oi + da if oi is not None and da is not None else None

    def ratio(a, b):
        return a / b if a is not None and b not in (None, 0) else None

    out = {
        "Company": co.name,
        "Price": price,
        "Market cap ($M)": mcap / 1e6,
        "Enterprise value ($M)": ev / 1e6,
        "TTM revenue ($M)": r / 1e6,
        "Revenue growth TTM %": (r / r_prior - 1) * 100 if r_prior else None,
        "Gross margin TTM %": ratio(gp, r) * 100 if gp else None,
        "Operating margin TTM %": ratio(oi, r) * 100 if oi is not None else None,
        "P/E TTM": ratio(mcap, ni) if ni and ni > 0 else None,
        "EV/Revenue TTM": ratio(ev, r),
        "EV/EBITDA TTM": ratio(ev, ebitda) if ebitda and ebitda > 0 else None,
        "FCF yield TTM %": ratio(fcf, mcap) * 100 if fcf is not None else None,
    }
    if hist is not None:
        out["52w high"], out["52w low"] = float(hist.max()), float(hist.min())
        out["1y return %"] = (float(hist.iloc[-1]) / float(hist.iloc[0]) - 1) * 100
    out["Sources"] = (f"price: {price_note}; {shares_note}; TTM = 4 quarters to {q.columns[-1]} "
                      f"(SEC XBRL); EV = mkt cap + long-term debt - cash - ST investments")
    return out


def comps(tickers: list[str]) -> pd.DataFrame:
    rows = {}
    for t in tickers:
        try:
            rows[t.upper()] = valuation(t)
        except (Exception, SystemExit) as e:  # one bad ticker shouldn't kill the table
            rows[t.upper()] = {"Company": f"error: {e}"}
    df = pd.DataFrame(rows).T
    sources = df.pop("Sources") if "Sources" in df else None
    if sources is not None:
        df["Sources"] = sources
    return df
