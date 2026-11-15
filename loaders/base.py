"""Helpers shared by all loaders: file reading and the SectionBuilder."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from schema import Section

TERMINAL = (".", ":", ";", "?", "!", ")", '"', "”")


def read_text(path) -> str:
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


class SectionBuilder:
    """Keeps a heading stack and turns (heading, text) events into Sections."""

    def __init__(self, source: str, title: str, doc_type: str, split_on_page: bool = False):
        self.source, self.title, self.doc_type = source, title, doc_type
        self.split_on_page = split_on_page
        self.sections: List[Section] = []
        self._stack: List[Tuple[int, str]] = []
        self._cur: Optional[Section] = None

    def heading(self, level: int, text: str) -> None:
        text = " ".join(text.split())
        if not text:
            return
        while self._stack and self._stack[-1][0] >= level:
            self._stack.pop()
        self._stack.append((level, text))
        self._cur = None

    def _path(self) -> str:
        names = [t for _, t in self._stack]
        if names and names[0].lower() == self.title.lower():
            names = names[1:]                       # don't repeat the document title
        return " > ".join(names)

    def text(self, text: str, page: Optional[int] = None, joiner: str = "\n\n") -> None:
        text = text.strip()
        if not text:
            return
        if self._cur is not None and self.split_on_page and page != self._cur.page:
            self._cur = None                        # keep page numbers exact
        if self._cur is None:
            self._cur = Section(text="", source=self.source, title=self.title,
                                section=self._path() or "Introduction",
                                page=page, page_end=page, doc_type=self.doc_type)
            self.sections.append(self._cur)
        self._cur.text = self._cur.text + joiner + text if self._cur.text else text

    def result(self) -> List[Section]:
        return [s for s in self.sections if s.text.strip()]
