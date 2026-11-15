"""PDF loader: pdfplumber, page by page. Repeated headers/footers are removed."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from config import LOADER_CONFIG, LoaderConfig
from schema import Section

from . import cleaning
from .base import TERMINAL, SectionBuilder

_BULLET = re.compile(r"^(?:[-•*–]\s+|\(?\d+[.)]\s+|\(?[a-zA-Z][.)]\s+)")


def _looks_like_heading(s: str, cfg: LoaderConfig) -> bool:
    """Heuristic for plain PDF text: short, no sentence punctuation at the end,
    starts with a capital (optionally numbered), not a bullet."""
    if not 3 <= len(s) <= cfg.pdf_heading_max_chars or len(s.split()) > cfg.pdf_heading_max_words or "|" in s:
        return False
    if s[0] in "-•*–" or re.match(r"^\(?[a-z]\)", s):
        return False
    if s[-1] in ".,;:!?)":
        return False
    return bool(re.match(r"^(\d+[.)]\s+)?[A-Z0-9]", s))


def _pdf_title(lines: List[str], cfg: LoaderConfig) -> Tuple[str, int]:
    """Title = first line, plus the next one(s) if the title wrapped."""
    k, title = 1, lines[0]
    while (k < min(cfg.pdf_title_max_lines, len(lines))
           and len(lines[k - 1]) >= cfg.pdf_title_wrap_min_chars and "|" not in lines[k]
           and not lines[k - 1].endswith((".", ":")) and not lines[k].endswith(".")):
        title += " " + lines[k]
        k += 1
    return title, k


def _pdf_blocks(text: str, width: int, cfg: LoaderConfig) -> List[Tuple[str, str]]:
    """Rebuild paragraphs from hard-wrapped PDF lines. Returns ('h'|'p', text)."""
    blocks: List[Tuple[str, str]] = []
    buf: List[str] = []

    def flush():
        if buf:
            blocks.append(("p", " ".join(buf)))
            buf.clear()

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            flush()
            continue
        prev_done = not buf or buf[-1].rstrip().endswith(TERMINAL)
        if prev_done and _looks_like_heading(s, cfg):
            flush()
            blocks.append(("h", s))
        elif _BULLET.match(s):
            flush()
            buf.append(s)
        else:
            # a short line that ends a sentence usually ends the paragraph too
            if buf and len(buf[-1]) < cfg.pdf_short_line_ratio * width \
                    and buf[-1].rstrip().endswith((".", "?", "!", ":")):
                flush()
            buf.append(s)
    flush()
    return blocks


def load_pdf(path, cfg: LoaderConfig = LOADER_CONFIG) -> List[Section]:
    import pdfplumber

    path = Path(path)
    with pdfplumber.open(path) as pdf:
        meta_title = ((pdf.metadata or {}).get("Title") or "").strip()
        pages = [page.extract_text() or "" for page in pdf.pages]

    pages = [cleaning.normalize_text(p) for p in pages]
    pages = cleaning.remove_repeating_lines(pages, cfg.header_footer_zone, cfg.repeat_ratio)
    pages = [cleaning.collapse_whitespace(p) for p in pages]
    if not any(p.strip() for p in pages):
        raise ValueError("no extractable text (scanned PDF? it needs OCR)")

    # title from the first lines of the first page with text
    first = next(i for i, p in enumerate(pages) if p.strip())
    first_lines = [l for l in pages[first].split("\n") if l.strip()]
    title, k = _pdf_title(first_lines, cfg)
    pages[first] = "\n".join(first_lines[k:])
    title = title or meta_title or path.stem

    lens = sorted(len(l) for p in pages for l in p.split("\n") if l.strip())
    width = lens[min(len(lens) - 1, int(len(lens) * cfg.pdf_width_percentile))] if lens else 80

    b = SectionBuilder(path.name, title, "pdf", split_on_page=True)
    for page_no, text in enumerate(pages, start=1):
        for kind, content in _pdf_blocks(text, width, cfg):
            if kind == "h":
                b.heading(1, content)
            else:
                b.text(content, page=page_no)
    return b.result()
