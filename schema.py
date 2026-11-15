"""Shared data shapes. Every loader returns list[Section]; the chunker returns list[Chunk]."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Section:
    """One heading-bounded piece of a document (for PDFs: one heading on one page)."""
    text: str
    source: str                      # file name, e.g. "01_lalita_kumari_fir_guidelines.pdf"
    title: str                       # document title
    section: str = ""                # heading path, e.g. "Origins" or "Guidelines > Rule 2"
    page: Optional[int] = None       # PDFs only (1-based)
    page_end: Optional[int] = None
    doc_type: str = ""               # pdf | html | md | txt


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    title: str
    section: str
    page: Optional[int]
    page_end: Optional[int]
    chunk_index: int
    tokens: int

    def metadata(self) -> dict:
        """Flat metadata for a vector store. Keys with no value are left out
        (Chroma and some other stores reject None)."""
        md = {
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "chunk_index": self.chunk_index,
            "tokens": self.tokens,
        }
        if self.page is not None:
            md["page"] = self.page
            md["page_end"] = self.page_end if self.page_end is not None else self.page
        return {k: v for k, v in md.items() if v not in (None, "")}

    def embedding_text(self) -> str:
        """Text to embed: title and section help short chunks match the right questions."""
        header = " > ".join(x for x in (self.title, self.section) if x)
        return f"{header}\n\n{self.text}" if header else self.text

    def citation(self) -> str:
        label = " — ".join(x for x in (self.title, self.section) if x)
        if self.page is not None:
            if self.page_end and self.page_end != self.page:
                label += f" (pp. {self.page}-{self.page_end})"
            else:
                label += f" (p. {self.page})"
        return f"{label} [{self.source}]"

    def to_dict(self) -> dict:
        return {"id": self.chunk_id, "text": self.text, "metadata": self.metadata()}
