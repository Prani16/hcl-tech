"""HTML loader: BeautifulSoup. Removes script/style/nav/footer (and ads, hidden blocks) first,
then splits on <h1>-<h6>."""
from __future__ import annotations

from pathlib import Path
from typing import List

from config import LOADER_CONFIG, LoaderConfig
from schema import Section

from .base import SectionBuilder, read_text

_HEADINGS = {f"h{i}" for i in range(1, 7)}
_BLOCKS = _HEADINGS | {"p", "li", "pre", "blockquote", "dt", "dd", "figcaption", "caption"}
_CONTAINERS = {"div", "aside", "section", "article", "main", "address", "body"}
_STRUCT = {"ul", "ol", "table", "thead", "tbody", "tfoot", "tr", "dl", "figure", "details"}
_NOT_INLINE = _BLOCKS | _CONTAINERS | _STRUCT


def _is_hidden_or_ad(tag, junk_classes) -> bool:
    attrs = tag.attrs or {}
    if "hidden" in attrs or attrs.get("aria-hidden") == "true":
        return True
    style = (attrs.get("style") or "").replace(" ", "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    classes = attrs.get("class") or []
    if isinstance(classes, str):
        classes = classes.split()
    return bool({c.lower() for c in classes} & set(junk_classes))


def _own_text(el) -> str:
    """Text of an element, leaving out nested block elements (those are emitted on their own)."""
    from bs4 import NavigableString, Tag
    from bs4.element import Comment

    parts = []
    for ch in el.children:
        if isinstance(ch, Comment):
            continue
        if isinstance(ch, NavigableString):
            parts.append(str(ch))
        elif isinstance(ch, Tag) and ch.name not in _NOT_INLINE:
            parts.append(ch.get_text(""))
    return " ".join("".join(parts).split())


def load_html(path, cfg: LoaderConfig = LOADER_CONFIG) -> List[Section]:
    from bs4 import BeautifulSoup, Tag

    path = Path(path)
    soup = BeautifulSoup(read_text(path), "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""

    # 1) remove noise: script, style, nav, footer, ads, hidden blocks, header bars without a heading
    for tag in soup.find_all(list(cfg.html_junk_tags)):
        tag.extract()
    junk = [t for t in soup.find_all(True) if isinstance(t, Tag) and _is_hidden_or_ad(t, cfg.html_junk_classes)]
    junk += [h for h in soup.find_all("header") if not h.find(["h1", "h2"])]
    for tag in junk:
        tag.extract()
    for br in soup.find_all("br"):
        br.replace_with(" ")

    h1 = soup.find("h1")
    title = (h1.get_text(" ", strip=True) if h1 else "") or page_title or path.stem

    # 2) pick the main content area if it holds most of the text
    body = soup.body or soup
    body_len = len(body.get_text(" ", strip=True)) or 1
    root = body
    for cand in (soup.find("main"), soup.find("article")):
        if cand is not None and len(cand.get_text(" ", strip=True)) >= cfg.html_main_content_ratio * body_len:
            root = cand
            break

    # 3) walk blocks in document order, split on headings
    b = SectionBuilder(path.name, title, "html")
    for el in root.descendants:
        if not isinstance(el, Tag):
            continue
        name = el.name
        if name == "tr":
            cells = [" ".join(c.get_text("").split()) for c in el.find_all(["th", "td"])]
            row = " | ".join(c for c in cells if c)
            if row:
                b.text(row, joiner="\n")
            continue
        if el.find_parent("tr"):
            continue
        if name in _HEADINGS:
            b.heading(int(name[1]), el.get_text(""))
        elif name == "pre":
            b.text(el.get_text())
        elif name == "li":
            t = _own_text(el)
            if t:
                b.text("- " + t, joiner="\n")
        elif name == "dd":
            t = _own_text(el)
            if t:
                b.text(t, joiner="\n")
        elif name in _BLOCKS or name in _CONTAINERS:
            t = _own_text(el)
            if t:
                b.text(t)

    sections = b.result()
    if not sections:                                  # odd markup: fall back to all text
        fallback = root.get_text("\n")
        if fallback.strip():
            sections = [Section(fallback, path.name, title, "Introduction", doc_type="html")]
    return sections
