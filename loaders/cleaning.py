"""Text cleaning: unicode fixes, repeated header/footer removal, whitespace collapse."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import List

_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
DECOR_LINE = re.compile(r"^([=\-_*~#.])\1{2,}$")          # ====  ----  ****
_PAGE_LABEL = re.compile(r"^\s*page\s+\d+(\s+of\s+\d+)?\s*$", re.I)


def normalize_text(text: str) -> str:
    """Unicode normalisation, strip invisible/control characters, unify newlines."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_ZERO_WIDTH)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return _CONTROL.sub("", text)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs, drop decoration lines (=====), keep paragraph breaks."""
    lines = []
    for ln in text.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        lines.append("" if DECOR_LINE.match(ln) else ln)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_text(text: str) -> str:
    return collapse_whitespace(normalize_text(text))


def _norm_line(line: str) -> str:
    # digits -> '#', so "Page 1" and "Page 2" count as the same line
    return re.sub(r"\d+", "#", line.strip().lower())


def remove_repeating_lines(pages: List[str], zone: int = 3, min_ratio: float = 0.5) -> List[str]:
    """Remove running headers/footers from a list of page texts.

    A line is removed when, ignoring digits, it sits in the first or last `zone`
    lines of at least `min_ratio` of the pages (and at least 2 pages). Lines in
    the middle of a page are never touched. "Page N [of M]" lines always go.
    """
    split = [p.split("\n") for p in pages]

    def edge_indexes(lines):
        idx = [i for i, l in enumerate(lines) if l.strip()]
        return set(idx[:zone] + idx[-zone:])

    repeated = set()
    if len(pages) >= 2:
        counts = Counter()
        for lines in split:
            for i in edge_indexes(lines):
                counts[_norm_line(lines[i])] += 1
        need = max(2, math.ceil(min_ratio * len(pages)))
        repeated = {k for k, c in counts.items() if c >= need}

    out = []
    for lines in split:
        edges = edge_indexes(lines)
        kept = [
            l for i, l in enumerate(lines)
            if not _PAGE_LABEL.match(l) and not (i in edges and _norm_line(l) in repeated)
        ]
        out.append("\n".join(kept))
    return out
