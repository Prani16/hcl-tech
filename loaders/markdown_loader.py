"""Markdown loader: splits on '#' headings (code blocks are left alone)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from config import LOADER_CONFIG, LoaderConfig
from schema import Section

from .base import SectionBuilder, read_text

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_MD_TABLE_SEP = re.compile(r"^[\s|:\-]+$")


def _md_inline(line: str) -> str:
    line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)          # links / images
    line = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), line)
    line = re.sub(r"(?<![*\w])\*(?!\s)([^*\n]+?)\*(?!\*)", r"\1", line)
    return line


def load_markdown(path, cfg: LoaderConfig = LOADER_CONFIG) -> List[Section]:
    path = Path(path)
    text = read_text(path).replace("\r\n", "\n")

    fm_title = ""
    if text.startswith("---\n"):                       # YAML front matter
        end = text.find("\n---", 4)
        if end != -1:
            m = re.search(r"^title:\s*(.+)$", text[4:end], re.M)
            fm_title = m.group(1).strip().strip("\"'") if m else ""
            text = text[end + 4:]

    lines = text.split("\n")
    title, in_code = fm_title, False
    if not title:
        for ln in lines:
            if ln.lstrip().startswith(("```", "~~~")):
                in_code = not in_code
            m = None if in_code else _MD_HEADING.match(ln)
            if m and len(m.group(1)) == 1:
                title = _md_inline(m.group(2)).strip()
                break
    title = title or path.stem

    b = SectionBuilder(path.name, title, "md")
    buf: List[str] = []
    in_code = False

    def flush():
        if buf:
            b.text("\n".join(buf))
            buf.clear()

    for ln in lines:
        if ln.lstrip().startswith(("```", "~~~")):
            in_code = not in_code
            buf.append(ln)
            continue
        if in_code:
            buf.append(ln)
            continue
        m = _MD_HEADING.match(ln)
        if m:
            flush()
            b.heading(len(m.group(1)), _md_inline(m.group(2)))
            continue
        if _MD_TABLE_SEP.match(ln) and "-" in ln and "|" in ln:
            continue                                   # |---|---| row
        ln = re.sub(r"^\s*>\s?", "", ln)               # blockquote marker
        if ln.strip().startswith("|"):
            ln = ln.strip().strip("|").strip()          # table row -> "a | b | c"
        buf.append(_md_inline(ln))
    flush()
    return b.result()
