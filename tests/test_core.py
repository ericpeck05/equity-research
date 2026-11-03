"""Offline tests using small synthetic inputs shaped like real SEC data."""
from ert import diff, financials, sec, sections


def _fact(start, end, val, form="10-K", filed="2025-11-01", accn="0000000000-25-000001"):
    f = {"end": end, "val": val, "form": form, "filed": filed, "accn": accn}
    if start:
        f["start"] = start
    return f


def _facts():
    rev = [
        _fact("2023-10-01", "2024-09-28", 1000),
        _fact("2024-09-29", "2025-09-27", 1200),
        _fact("2024-09-29", "2024-12-28", 280, "10-Q"),
        _fact("2024-12-29", "2025-03-29", 290, "10-Q"),
        _fact("2025-03-30", "2025-06-28", 300, "10-Q"),
    ]
    old_concept_rev = [_fact("2022-09-25", "2023-09-30", 900, filed="2023-11-01")]
    cfo = [_fact("2024-09-29", "2025-09-27", 400)]
    capex = [_fact("2024-09-29", "2025-09-27", 100)]
    cash = [_fact(None, "2025-09-27", 500), _fact(None, "2024-09-28", 450)]
    usd = lambda xs: {"units": {"USD": xs}}
    return {"facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": usd(rev),
        "Revenues": usd(old_concept_rev),
        "NetCashProvidedByUsedInOperatingActivities": usd(cfo),
        "PaymentsToAcquirePropertyPlantAndEquipment": usd(capex),
        "CashAndCashEquivalentsAtCarryingValue": usd(cash),
    }}}


def test_annual_merges_concepts_and_derives_metrics():
    a, q, src = financials.build(_facts())
    assert list(a.loc["Revenue"]) == [900, 1000, 1200]
    assert round(a.loc["Revenue growth YoY %"].iloc[-1], 6) == 20.0
    assert a.loc["Free cash flow"].iloc[-1] == 300
    assert a.loc["Cash & equivalents"].iloc[-1] == 500
    assert not src.empty and "accession" in src.columns


def test_q4_is_derived_from_full_year():
    _, q, src = financials.build(_facts())
    assert q.loc["Revenue", "2025-09-27"] == 1200 - 280 - 290 - 300
    assert src["note"].str.startswith("derived").any()


HTML = """<html><body>
<p>TABLE OF CONTENTS</p>
<table><tr><td>Item 1A.</td><td>Risk Factors</td><td>12</td></tr>
<tr><td>Item 7.</td><td>Management's Discussion and Analysis</td><td>30</td></tr></table>
<p>Item 1A. Risk Factors</p>
<p>Our business depends on a small number of customers and losing one would hurt results.</p>
<p>We rely on third-party foundries to manufacture our chips, mostly in one region.</p>
<p>Item 1B. Unresolved Staff Comments</p><p>None.</p>
<div><span>Item 7.</span></div><div>Management&#8217;s Discussion and Analysis of Financial Condition</div>
<p>Revenue grew 20% driven by data center demand from cloud customers this year.</p>
<p>Item 8. Financial Statements</p>
</body></html>"""


def test_html_to_text_and_section_extraction_skips_toc():
    text = sec.html_to_text(HTML)
    rf = sections.extract(text, "risk_factors")
    assert "third-party foundries" in rf and "Unresolved" not in rf
    md = sections.extract(text, "mdna")
    assert "data center demand" in md


def test_diff_classifies_changes():
    old = ("We rely on third-party foundries to manufacture our chips, mostly in one region.\n"
           "Currency fluctuations could affect our reported international results materially.")
    new = ("We rely on third-party foundries to manufacture our chips, mostly in Taiwan.\n"
           "New export controls on advanced chips could prevent sales to certain customers in China.")
    md, stats = diff.compare(old, new, "FY24", "FY25")
    assert stats == {"old_paragraphs": 2, "new_paragraphs": 2, "added": 1, "removed": 1, "modified": 1}
    assert "**Taiwan.**" in md


def test_stock_split_restates_older_eps_and_shares():
    def sh(start, end, val, filed):
        return _fact(start, end, val, filed=filed)
    facts = _facts()
    g = facts["facts"]["us-gaap"]
    g["WeightedAverageNumberOfDilutedSharesOutstanding"] = {"units": {"shares": [
        sh("2022-09-25", "2023-09-30", 100, "2023-11-01"),
        sh("2023-10-01", "2024-09-28", 101, "2024-11-01"),
        sh("2023-10-01", "2024-09-28", 1010, "2025-11-01"),   # 10:1 split restated
        sh("2024-09-29", "2025-09-27", 1020, "2025-11-01"),
    ]}}
    g["EarningsPerShareDiluted"] = {"units": {"USD/shares": [
        sh("2022-09-25", "2023-09-30", 9.0, "2023-11-01"),
        sh("2024-09-29", "2025-09-27", 1.2, "2025-11-01"),
    ]}}
    assert financials.split_events(facts) == [(financials.date(2025, 11, 1), 10.0)]
    a, _, _ = financials.build(facts)
    assert list(a.loc["Diluted shares"]) == [1000, 1010, 1020]
    assert round(a.loc["Diluted EPS"].iloc[0], 6) == 0.9


def test_page_headers_and_styled_headings():
    html = """<p>Item 1A.</p><p>Risk Factors</p><p>Item 1B.</p>
    <p>ITEM 1A. RIS<span>K FACTORS</span></p>
    <p>Competition in cloud and AI services is intense and could reduce our margins over time.</p>
    <p>Item 1A</p>
    <p>Our global operations subject us to export controls and sanctions in many countries.</p>
    <p>ITEM 1B. UNRESOLVED STAFF COMMENTS</p>"""
    text = sec.html_to_text(html)
    assert "ITEM 1A. RISK FACTORS" in text
    rf = sections.extract(text, "risk_factors")
    assert "Competition" in rf and "export controls" in rf and "UNRESOLVED" not in rf


def test_year_to_date_cash_flows_become_quarters():
    facts = _facts()
    facts["facts"]["us-gaap"]["NetCashProvidedByUsedInOperatingActivities"] = {"units": {"USD": [
        _fact("2024-09-29", "2024-12-28", 100, "10-Q"),
        _fact("2024-09-29", "2025-03-29", 210, "10-Q"),   # 6 months YTD
        _fact("2024-09-29", "2025-06-28", 330, "10-Q"),   # 9 months YTD
        _fact("2024-09-29", "2025-09-27", 460),           # full year
    ]}}
    _, q, _ = financials.build(facts)
    assert list(q.loc["Operating cash flow"]) == [100, 110, 120, 130]
