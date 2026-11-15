"""Turn section text into small units (paragraphs, or sentences for long paragraphs)."""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import List, Optional

from schema import Section

from .tokens import count_tokens, tail_words

TERMINAL = (".", ":", ";", "?", "!", ")", '"', "”")
LIST_START = re.compile(r"^(?:[-•*–]\s|\(?\d+[.)]\s|\(?[a-zA-Z][.)]\s)")


@dataclass
class Unit:
    text: str
    joiner: str                       # what goes between the previous unit and this one
    tokens: int
    page: Optional[int]
    page_end: Optional[int]
    overlap: bool = False


def split_words(text: str, target: int) -> List[str]:
    words, out, cur = text.split(), [], []
    for w in words:
        cur.append(w)
        if len(cur) % 10 == 0 and count_tokens(" ".join(cur)) >= target:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def paragraph_units(sec: Section, target: int) -> List[Unit]:
    """Paragraphs are the unit. A paragraph bigger than `target` is split at line breaks,
    then sentences, then (for a giant sentence) words."""
    units: List[Unit] = []
    for para in re.split(r"\n\s*\n", sec.text):
        para = para.strip()
        if not para:
            continue
        t = count_tokens(para)
        if t <= target:
            units.append(Unit(para, "\n\n", t, sec.page, sec.page_end))
            continue
        first = True
        for li, line in enumerate(para.split("\n")):
            for si, sent in enumerate(re.split(r"(?<=[.!?])\s+", line.strip())):
                if not sent:
                    continue
                joiner = "\n\n" if first else ("\n" if si == 0 and li > 0 else " ")
                pieces = [sent] if count_tokens(sent) <= target else split_words(sent, target)
                for pi, piece in enumerate(pieces):
                    units.append(Unit(piece, joiner if pi == 0 else " ", count_tokens(piece),
                                      sec.page, sec.page_end))
                first = False
    return units


def overlap_tail(units: List[Unit], n_tokens: int) -> List[Unit]:
    """Trailing units of a finished chunk, up to ~n_tokens, to start the next chunk with."""
    tail: List[Unit] = []
    total = 0
    for u in reversed(units):
        if total + u.tokens > n_tokens:
            break
        tail.insert(0, replace(u, overlap=True))
        total += u.tokens
    if not tail and units:                             # last unit is longer than the overlap
        txt = tail_words(units[-1].text, n_tokens)
        if txt:
            tail = [replace(units[-1], text=txt, joiner="\n\n", tokens=count_tokens(txt), overlap=True)]
    return tail
