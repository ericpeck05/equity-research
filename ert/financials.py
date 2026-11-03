"""Turn SEC XBRL "company facts" into clean annual and quarterly financial tables.

Every number keeps a pointer to the filing it came from (accession number), so
any figure in a model or note can be traced back to the source document.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

# metric name -> (kind, candidate XBRL concepts in priority order)
# kind: "flow" = measured over a period (income/cash flow), "instant" = balance sheet
METRICS: dict[str, tuple[str, list[str]]] = {
    "Revenue": ("flow", [
        "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
    ]),
    "Cost of revenue": ("flow", [
        "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
    ]),
    "Gross profit": ("flow", ["GrossProfit"]),
    "R&D": ("flow", ["ResearchAndDevelopmentExpense",
                     "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"]),
    "SG&A": ("flow", ["SellingGeneralAndAdministrativeExpense"]),
    "Operating income": ("flow", ["OperatingIncomeLoss"]),
    "Net income": ("flow", ["NetIncomeLoss", "ProfitLoss"]),
    "Diluted EPS": ("flow", ["EarningsPerShareDiluted"]),
    "Diluted shares": ("flow", ["WeightedAverageNumberOfDilutedSharesOutstanding"]),
    "Operating cash flow": ("flow", ["NetCashProvidedByUsedInOperatingActivities"]),
    "Capex": ("flow", ["PaymentsToAcquirePropertyPlantAndEquipment",
                       "PaymentsToAcquireProductiveAssets"]),
    "Stock-based comp": ("flow", ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]),
    "D&A": ("flow", ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
                     "DepreciationAndAmortization"]),
    "Buybacks": ("flow", ["PaymentsForRepurchaseOfCommonStock"]),
    "Dividends paid": ("flow", ["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"]),
    "Cash & equivalents": ("instant", ["CashAndCashEquivalentsAtCarryingValue",
                                       "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
    "Short-term investments": ("instant", ["MarketableSecuritiesCurrent", "ShortTermInvestments",
                                           "AvailableForSaleSecuritiesDebtSecuritiesCurrent"]),
    "Total assets": ("instant", ["Assets"]),
    "Total liabilities": ("instant", ["Liabilities"]),
    "Long-term debt": ("instant", ["LongTermDebtNoncurrent", "LongTermDebt"]),
    "Deferred revenue (current)": ("instant", ["ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent"]),
    "Shareholders' equity": ("instant", ["StockholdersEquity"]),
}

# Flows that are per-share or averages can't be summed to derive Q4.
NOT_ADDITIVE = {"Diluted EPS", "Diluted shares"}


@dataclass
class Fact:
    value: float
    start: date | None
    end: date
    filed: date
    accession: str
    concept: str
    form: str


def _d(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def _facts_for(facts: dict, concepts: list[str]) -> list[tuple[int, Fact]]:
    """All facts for the candidate concepts, tagged with the concept's priority."""
    out = []
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for prio, concept in enumerate(concepts):
        node = gaap.get(concept)
        if not node:
            continue
        units = node["units"]
        unit = next((u for u in ("USD", "USD/shares", "shares") if u in units), next(iter(units)))
        for f in units[unit]:
            out.append((prio, Fact(
                value=float(f["val"]), start=_d(f.get("start")), end=_d(f["end"]),
                filed=_d(f["filed"]), accession=f.get("accn", ""), concept=concept, form=f.get("form", ""),
            )))
    return out


def _pick(cands: list[tuple[int, Fact]]) -> Fact:
    # Best concept first, then the most recently filed value (picks up restatements).
    return sorted(cands, key=lambda pf: (pf[0], -pf[1].filed.toordinal()))[0][1]


def _durations(facts: list[tuple[int, Fact]], lo: int, hi: int) -> dict[tuple[date, date], Fact]:
    groups: dict[tuple[date, date], list] = {}
    for prio, f in facts:
        if f.start is None:
            continue
        days = (f.end - f.start).days
        if lo <= days <= hi:
            groups.setdefault((f.start, f.end), []).append((prio, f))
    return {k: _pick(v) for k, v in groups.items()}


def _dedupe_by_end(periods: dict[tuple[date, date], Fact]) -> dict[date, Fact]:
    by_end: dict[date, list] = {}
    for (start, end), f in periods.items():
        by_end.setdefault(end, []).append(f)
    # If two periods share an end date (52/53-week quirks), keep the latest filed.
    return {end: max(fs, key=lambda f: f.filed) for end, fs in by_end.items()}


def build(facts: dict, years: int = 6) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (annual, quarterly, sources). Columns are period end dates, newest last."""
    annual: dict[str, dict[date, float]] = {}
    quarterly: dict[str, dict[date, float]] = {}
    sources: list[dict] = []

    def note(metric, freq, f: Fact, derived=""):
        sources.append({"metric": metric, "frequency": freq, "period_end": f.end.isoformat(),
                        "value": f.value, "xbrl_concept": f.concept, "accession": f.accession,
                        "form": f.form, "filed": f.filed.isoformat(), "note": derived})

    instants_raw: dict[str, list[tuple[int, Fact]]] = {}
    for metric, (kind, concepts) in METRICS.items():
        raw = _facts_for(facts, concepts)
        if not raw:
            continue
        if kind == "instant":
            instants_raw[metric] = raw
            continue
        yr = _dedupe_by_end(_durations(raw, 350, 380))
        qtr = _dedupe_by_end(_durations(raw, 80, 100))
        annual[metric] = {e: f.value for e, f in yr.items()}
        quarterly[metric] = {e: f.value for e, f in qtr.items()}
        for f in yr.values():
            note(metric, "annual", f)
        for f in qtr.values():
            note(metric, "quarterly", f)

        # Companies usually don't report Q4 alone: Q4 = full year - Q1 - Q2 - Q3.
        if metric not in NOT_ADDITIVE:
            for fy_end, fy in yr.items():
                if fy_end in qtr or fy.start is None:
                    continue
                inside = [f for e, f in qtr.items() if fy.start < e < fy_end]
                if len(inside) == 3:
                    val = fy.value - sum(f.value for f in inside)
                    quarterly[metric][fy_end] = val
                    note(metric, "quarterly", Fact(val, None, fy_end, fy.filed, fy.accession, fy.concept, fy.form),
                         "derived: FY minus Q1-Q3")

    ann_ends = sorted({e for m in annual.values() for e in m})[-years:]
    q_ends = sorted({e for m in quarterly.values() for e in m})[-years * 4:]

    for metric, raw in instants_raw.items():
        by_end: dict[date, list] = {}
        for prio, f in raw:
            by_end.setdefault(f.end, []).append((prio, f))
        picked = {e: _pick(v) for e, v in by_end.items()}
        annual[metric] = {e: picked[e].value for e in ann_ends if e in picked}
        quarterly[metric] = {e: picked[e].value for e in q_ends if e in picked}
        for e in set(ann_ends) | set(q_ends):
            if e in picked:
                note(metric, "annual" if e in ann_ends else "quarterly", picked[e])

    a = _frame(annual, ann_ends)
    q = _frame(quarterly, q_ends)
    _add_derived(a, lag=1)
    _add_derived(q, lag=4)
    a.columns = [f"FY{c.year} ({c:%b-%y})" for c in a.columns]
    q.columns = [c.isoformat() for c in q.columns]
    return a, q, pd.DataFrame(sources)


def _frame(data: dict[str, dict[date, float]], ends: list[date]) -> pd.DataFrame:
    rows = [m for m in METRICS if m in data]
    return pd.DataFrame([[data[m].get(e) for e in ends] for m in rows], index=rows, columns=ends, dtype="float")


def _add_derived(df: pd.DataFrame, lag: int) -> None:
    def has(*names):
        return all(n in df.index for n in names)

    if not has("Gross profit") and has("Revenue", "Cost of revenue"):
        df.loc["Gross profit"] = df.loc["Revenue"] - df.loc["Cost of revenue"]
    if has("Operating cash flow", "Capex"):
        df.loc["Free cash flow"] = df.loc["Operating cash flow"] - df.loc["Capex"]
    if has("Free cash flow", "Stock-based comp"):
        df.loc["FCF after SBC"] = df.loc["Free cash flow"] - df.loc["Stock-based comp"]
    if has("Cash & equivalents"):
        cash = df.loc["Cash & equivalents"] + (df.loc["Short-term investments"].fillna(0)
                                               if has("Short-term investments") else 0)
        debt = df.loc["Long-term debt"].fillna(0) if has("Long-term debt") else 0
        df.loc["Net cash (debt)"] = cash - debt
    if has("Revenue"):
        rev = df.loc["Revenue"]
        df.loc["Revenue growth YoY %"] = (rev / rev.shift(lag) - 1) * 100
        for name, label in [("Gross profit", "Gross margin %"), ("Operating income", "Operating margin %"),
                            ("R&D", "R&D % of revenue"), ("Stock-based comp", "SBC % of revenue"),
                            ("Free cash flow", "FCF margin %")]:
            if name in df.index:
                df.loc[label] = df.loc[name] / rev * 100


def to_excel(ticker: str, a: pd.DataFrame, q: pd.DataFrame, src: pd.DataFrame, path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, df in [("Annual", a), ("Quarterly", q)]:
            out = df.copy()
            millions = [i for i in out.index if "%" not in i and i != "Diluted EPS"]
            out.loc[millions] = out.loc[millions] / 1e6
            out.to_excel(xw, sheet_name=name, index_label=f"{ticker} ($M; shares in M; EPS in $)")
            ws = xw.sheets[name]
            ws.column_dimensions["A"].width = 34
            for col in ws.iter_cols(min_col=2):
                ws.column_dimensions[col[0].column_letter].width = 16
                for cell in col[1:]:
                    cell.number_format = "#,##0.0;(#,##0.0)"
        src.to_excel(xw, sheet_name="Sources", index=False)
