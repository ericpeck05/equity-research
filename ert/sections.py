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

_ITEM = re.compile(r"^\s*item\s*\d{1,2}[a-c]?\s*[\.:\-–—|]?", re.I)


def _is_item_heading(line: str) -> bool:
    return bool(_ITEM.match(line)) and len(line) < 200


def extract(text: str, section: str) -> str:
    """Return the section body. Picks the longest match so the table of contents is skipped."""
    if section not in SECTIONS:
        raise SystemExit(f"Unknown section {section!r}. Choose from: {', '.join(SECTIONS)}")
    kw = re.compile(SECTIONS[section], re.I)
    lines = text.splitlines()
    best: list[str] = []
    for i, line in enumerate(lines):
        if not _is_item_heading(line):
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        title_on_next = not kw.search(line) and kw.search(nxt) and len(nxt) < 120
        if not (kw.search(line) or title_on_next):
            continue
        start = i + (2 if title_on_next else 1)
        end = start
        while end < len(lines) and not _is_item_heading(lines[end]):
            end += 1
        body = lines[start:end]
        if sum(map(len, body)) > sum(map(len, best)):
            best = body
    return "\n".join(best)
