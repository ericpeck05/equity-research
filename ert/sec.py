"""Free data from SEC EDGAR: company lookup, filing lists, filing text and XBRL facts.

Endpoints (all free, no key, max 10 requests/second):
  https://www.sec.gov/files/company_tickers.json            ticker -> CIK
  https://data.sec.gov/submissions/CIK##########.json       filing history
  https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json  every reported number
  https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc} the filing itself
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from . import config

_last_request = 0.0


def _get(url: str, *, binary: bool = False, max_age_hours: float | None = None):
    """GET with polite rate limiting and an on-disk cache."""
    global _last_request
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    path = config.CACHE_DIR / key
    max_age = config.cache_max_age_hours() if max_age_hours is None else max_age_hours
    if path.exists() and (time.time() - path.stat().st_mtime) < max_age * 3600:
        return path.read_bytes() if binary else path.read_text(encoding="utf-8")

    wait = 0.15 - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = requests.get(url, headers={"User-Agent": config.sec_user_agent()}, timeout=60)
    _last_request = time.time()
    resp.raise_for_status()
    path.write_bytes(resp.content)
    return resp.content if binary else resp.content.decode("utf-8", errors="replace")


def _get_json(url: str, **kw) -> dict:
    return json.loads(_get(url, **kw))


@dataclass
class Company:
    ticker: str
    cik: int
    name: str

    @property
    def cik10(self) -> str:
        return f"{self.cik:010d}"


def lookup(ticker: str) -> Company:
    data = _get_json("https://www.sec.gov/files/company_tickers.json", max_age_hours=24 * 7)
    t = ticker.upper().replace(".", "-")
    for row in data.values():
        if row["ticker"].upper() == t:
            return Company(row["ticker"].upper(), int(row["cik_str"]), row["title"])
    raise SystemExit(f"Ticker {ticker!r} not found in SEC's list.")


@dataclass
class Filing:
    form: str
    filing_date: str
    report_date: str
    accession: str
    primary_document: str
    cik: int

    @property
    def url(self) -> str:
        acc = self.accession.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{acc}/{self.primary_document}"

    @property
    def index_url(self) -> str:
        acc = self.accession.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{acc}/"


def filings(company: Company, forms: tuple[str, ...] = ("10-K", "10-Q", "8-K"), limit: int = 20) -> list[Filing]:
    """Most recent filings first."""
    sub = _get_json(f"https://data.sec.gov/submissions/CIK{company.cik10}.json")
    recent = sub["filings"]["recent"]
    out = []
    for i, form in enumerate(recent["form"]):
        if forms and form not in forms:
            continue
        out.append(Filing(
            form=form,
            filing_date=recent["filingDate"][i],
            report_date=recent["reportDate"][i],
            accession=recent["accessionNumber"][i],
            primary_document=recent["primaryDocument"][i],
            cik=company.cik,
        ))
        if len(out) >= limit:
            break
    return out


def html_to_text(html: str) -> str:
    """Filing HTML -> readable plain text, one paragraph per line."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    # Inline XBRL hides metadata in <ix:header>; drop it.
    for tag in soup.find_all(re.compile(r"^ix:header$")):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    blocks = []
    for el in soup.find_all(["p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        # Only take leaf-ish blocks so text isn't duplicated.
        if el.find(["p", "div", "tr", "li", "table"]):
            continue
        if el.name == "tr":
            cells = [re.sub(r"\s+", " ", c.get_text("")).strip() for c in el.find_all(["td", "th"])]
            text = " | ".join(c for c in cells if c)
        else:
            # "" (not " ") so styled letters in headings aren't split ("RIS K FACTORS").
            text = el.get_text("")
        text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
        if text:
            blocks.append(text)
    return "\n".join(blocks)


def filing_text(filing: Filing) -> str:
    """Plain text of a filing, saved under data/filings/ for reuse and citation."""
    out_dir = config.DATA_DIR / "filings"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{filing.cik}_{filing.accession}_{filing.form.replace('/', '-')}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    html = _get(filing.url, max_age_hours=24 * 365)
    text = html_to_text(html)
    path.write_text(text, encoding="utf-8")
    return text


def filing_text_path(filing: Filing) -> Path:
    filing_text(filing)
    return config.DATA_DIR / "filings" / f"{filing.cik}_{filing.accession}_{filing.form.replace('/', '-')}.txt"


def company_facts(company: Company) -> dict:
    return _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{company.cik10}.json")
