"""Pack units into chunks of about `target` tokens, with overlap."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .tokens import count_tokens
from .units import Unit, overlap_tail


@dataclass
class RawChunk:
    text: str
    section: str
    page: Optional[int]
    page_end: Optional[int]
    tokens: int


def to_raw(units: List[Unit], section: str) -> RawChunk:
    text = units[0].text
    for u in units[1:]:
        text += u.joiner + u.text
    fresh = [u for u in units if not u.overlap and u.page is not None]   # overlap text doesn't count for pages
    page = min((u.page for u in fresh), default=None)
    page_end = max((u.page_end or u.page for u in fresh), default=None)
    return RawChunk(text, section, page, page_end, count_tokens(text))


def pack(units: List[Unit], section: str, target: int, overlap_tokens: int,
         min_tokens: int, max_tokens: int) -> List[RawChunk]:
    chunks: List[List[Unit]] = []
    cur: List[Unit] = []
    cur_tokens = fresh = 0
    for u in units:
        if fresh and cur_tokens + u.tokens > target:
            chunks.append(cur)
            cur = overlap_tail(cur, overlap_tokens)
            cur_tokens = sum(x.tokens for x in cur)
            if cur and cur_tokens + u.tokens > max_tokens:
                cur, cur_tokens = [], 0                # overlap would make the chunk too big
            fresh = 0
        cur.append(u)
        cur_tokens += u.tokens
        fresh += 1
    if fresh:
        new_units = [x for x in cur if not x.overlap]
        new_tokens = sum(x.tokens for x in new_units)
        # a short leftover is appended to the previous chunk instead of becoming its own
        if chunks and new_tokens < min_tokens and sum(x.tokens for x in chunks[-1]) + new_tokens <= max_tokens:
            chunks[-1].extend(new_units)
        else:
            chunks.append(cur)
    return [to_raw(c, section) for c in chunks]
