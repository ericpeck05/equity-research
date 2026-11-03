"""Paragraph-level comparison of two versions of a filing section.

Analysts read "what changed" closely: new risk factors, removed language,
softened or strengthened wording. This produces a Markdown report of exactly that.
"""
from __future__ import annotations

import difflib


def _paras(text: str, min_len: int = 40) -> list[str]:
    return [p.strip() for p in text.splitlines() if len(p.strip()) >= min_len]


def _word_diff(old: str, new: str) -> str:
    a, b = old.split(), new.split()
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(" ".join(a[i1:i2]))
        if op in ("delete", "replace"):
            out.append("~~" + " ".join(a[i1:i2]) + "~~")
        if op in ("insert", "replace"):
            out.append("**" + " ".join(b[j1:j2]) + "**")
    return " ".join(out)


def compare(old_text: str, new_text: str, old_label: str, new_label: str) -> tuple[str, dict]:
    old, new = _paras(old_text), _paras(new_text)
    added, removed, modified = [], [], []
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        olds, news = old[i1:i2], new[j1:j2]
        # Pair up paragraphs that are edited versions of each other.
        used = set()
        for o in olds:
            best, best_r = None, 0.0
            for k, n in enumerate(news):
                if k in used:
                    continue
                r = difflib.SequenceMatcher(None, o, n, autojunk=False).ratio()
                if r > best_r:
                    best, best_r = k, r
            if best is not None and best_r >= 0.6:
                used.add(best)
                modified.append((o, news[best]))
            else:
                removed.append(o)
        added += [n for k, n in enumerate(news) if k not in used]

    stats = {"old_paragraphs": len(old), "new_paragraphs": len(new),
             "added": len(added), "removed": len(removed), "modified": len(modified)}
    md = [f"# What changed: {old_label} -> {new_label}", "",
          f"Paragraphs: {len(old)} -> {len(new)}. "
          f"**{len(added)} new**, **{len(removed)} removed**, **{len(modified)} edited**.", ""]
    md += ["## New paragraphs", ""] + [f"- {p}" for p in added] + [""]
    md += ["## Removed paragraphs", ""] + [f"- {p}" for p in removed] + [""]
    md += ["## Edited paragraphs", "", "(~~struck~~ = removed wording, **bold** = new wording)", ""]
    md += [f"- {_word_diff(o, n)}" for o, n in modified]
    return "\n".join(md), stats
