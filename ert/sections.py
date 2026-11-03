"""Pull named sections (Risk Factors, MD&A, ...) out of 10-K / 10-Q plain text."""
from __future__ import annotations

import re

SECTIONS = {
    "business": r"\bbusiness\b",
    "risk_factors": r"risk\s+factors",
    "legal": r"legal\s+proceedings",
    "mdna": r"management.{0,3}s\s+discussion",
    "market_risk": r"quantitative\s+and\s+qualitative",
    "financials": r"financial\s+statements",
    "controls": r"controls\s+and\s+procedures",
}

_ITEM = re.compile(r"^\s*item\s*(\d{1,2}[a-c]?)\b\s*[\.:\-–—|,]?", re.I)


def _item_no(line: str) -> str | None:
    """'Item 1A. Risk Factors' -> '1a'. None if the line isn't an item heading."""
    m = _ITEM.match(line)
    return m.group(1).lower() if m and len(line) < 200 else None


def extract(text: str, section: str) -> str:
    """Return the section body. Picks the longest match so the table of contents is skipped."""
    if section not in SECTIONS:
        raise SystemExit(f"Unknown section {section!r}. Choose from: {', '.join(SECTIONS)}")
    kw = re.compile(SECTIONS[section], re.I)
    lines = text.splitlines()
    best: list[str] = []
    for i, line in enumerate(lines):
        item = _item_no(line)
        if item is None:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        title_on_next = (not kw.search(line) and _item_no(nxt) is None
                         and kw.search(nxt) and len(nxt) < 120)
        if not (kw.search(line) or title_on_next):
            continue
        start = i + (2 if title_on_next else 1)
        end = start
        # Stop at the next *different* item; repeated page headers ("Item 1A") don't end it.
        while end < len(lines) and _item_no(lines[end]) in (None, item):
            end += 1
        body = [l for l in lines[start:end] if _item_no(l) is None]
        if sum(map(len, body)) > sum(map(len, best)):
            best = body
    return "\n".join(best)
