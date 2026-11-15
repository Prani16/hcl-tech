"""TXT loader: plain read. ALL-CAPS heading lines (e.g. 'KEY FACTS') are used as sections."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from config import LOADER_CONFIG, LoaderConfig
from schema import Section

from . import cleaning
from .base import SectionBuilder, read_text


def _caps_candidate(s: str, cfg: LoaderConfig) -> bool:
    letters = [c for c in s if c.isalpha()]
    return (3 <= len(s) <= cfg.txt_heading_max_chars and len(letters) >= 3 and s == s.upper()
            and not s.endswith(".") and s[0] not in "-•*" and not cleaning.DECOR_LINE.match(s))


def load_txt(path, cfg: LoaderConfig = LOADER_CONFIG) -> List[Section]:
    path = Path(path)
    lines = cleaning.normalize_text(read_text(path)).split("\n")

    title = ""
    for ln in lines[:cfg.txt_title_scan_lines]:
        m = re.match(r"^\s*SUBJECT:\s*(.+)$", ln, re.I)
        if m:
            title = m.group(1).strip()
            break
    if not title:
        title = next((l.strip() for l in lines
                      if l.strip() and not cleaning.DECOR_LINE.match(l.strip())), path.stem)

    b = SectionBuilder(path.name, title, "txt")
    buf: List[str] = []

    def flush():
        if buf:
            b.text("\n".join(buf))
            buf.clear()

    stripped = [l.strip() for l in lines]
    for i, s in enumerate(stripped):
        is_heading = False
        if cfg.txt_detect_caps_headings and _caps_candidate(s, cfg):
            # heading only if real text follows (a run of caps lines is just a letterhead)
            nxt = next((x for x in stripped[i + 1:] if x and not cleaning.DECOR_LINE.match(x)), None)
            is_heading = nxt is not None and not _caps_candidate(nxt, cfg)
        if is_heading:
            flush()
            b.heading(1, re.sub(r"^SUBJECT:\s*", "", s, flags=re.I))
        else:
            buf.append(s)
    flush()
    return b.result()
