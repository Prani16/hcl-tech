"""Merge tiny chunks into a neighbour."""
from __future__ import annotations

from typing import List

from .packer import RawChunk
from .tokens import count_tokens


def _union_pages(a: RawChunk, b: RawChunk):
    pages = [p for p in (a.page, b.page) if p is not None]
    ends = [p for p in (a.page_end, b.page_end) if p is not None]
    return (min(pages) if pages else None), (max(ends) if ends else None)


def merge_tiny(raws: List[RawChunk], min_tokens: int, max_tokens: int) -> List[RawChunk]:
    """Merge any chunk under min_tokens into a neighbour (same section preferred, else the
    smaller one) as long as the result stays under max_tokens. If the sections differ, the
    tiny piece's heading is written into the text so nothing is misattributed."""
    changed = True
    while changed and len(raws) > 1:
        changed = False
        for i, c in enumerate(raws):
            if c.tokens >= min_tokens:
                continue
            options = []
            for j in (i - 1, i + 1):
                if 0 <= j < len(raws) and raws[j].tokens + c.tokens <= max_tokens:
                    options.append((raws[j].section != c.section, raws[j].tokens, j))
            if not options:
                continue
            j = min(options)[2]
            host = raws[j]
            label = f"{c.section}\n" if c.section and c.section != host.section else ""
            host.text = (host.text + "\n\n" + label + c.text) if j < i else (label + c.text + "\n\n" + host.text)
            host.page, host.page_end = _union_pages(host, c)
            host.tokens = count_tokens(host.text)
            del raws[i]
            changed = True
            break
    return raws
