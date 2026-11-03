"""Market data (price, valuation multiples) from Yahoo Finance via yfinance.

Free but unofficial: fine for screening and comps, but double-check any number
that goes into a published note against a primary source.
"""
from __future__ import annotations

import pandas as pd

FIELDS = {
    "shortName": "Name",
    "currentPrice": "Price",
    "marketCap": "Market cap",
    "enterpriseValue": "Enterprise value",
    "trailingPE": "P/E (trailing)",
    "forwardPE": "P/E (forward)",
    "enterpriseToRevenue": "EV/Revenue",
    "enterpriseToEbitda": "EV/EBITDA",
    "revenueGrowth": "Revenue growth (yoy)",
    "grossMargins": "Gross margin",
    "operatingMargins": "Operating margin",
    "freeCashflow": "Free cash flow (ttm)",
    "beta": "Beta",
    "fiftyTwoWeekLow": "52w low",
    "fiftyTwoWeekHigh": "52w high",
}


def _yf():
    try:
        import yfinance as yf
    except ImportError:
        raise SystemExit("Run: pip install -r requirements.txt  (yfinance is missing)")
    return yf


def quote(ticker: str) -> dict:
    info = _yf().Ticker(ticker).info or {}
    out = {label: info.get(key) for key, label in FIELDS.items()}
    if out.get("Free cash flow (ttm)") and out.get("Market cap"):
        out["FCF yield"] = out["Free cash flow (ttm)"] / out["Market cap"]
    return out


def comps(tickers: list[str]) -> pd.DataFrame:
    rows = {}
    for t in tickers:
        try:
            rows[t.upper()] = quote(t)
        except Exception as e:  # one bad ticker shouldn't kill the table
            rows[t.upper()] = {"Name": f"error: {e}"}
    df = pd.DataFrame(rows).T
    return df


def history(ticker: str, period: str = "5y") -> pd.Series:
    return _yf().Ticker(ticker).history(period=period)["Close"]
