"""Chunker: headings first (sections come split already), then pack paragraphs to ~target
tokens with ~overlap, then merge tiny pieces. All sizes come from config/chunking_config.py."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from config import CHUNKING_CONFIG, ChunkingConfig
from schema import Chunk, Section

from .merger import merge_tiny
from .packer import RawChunk, pack
from .units import LIST_START, TERMINAL, Unit, paragraph_units


def _slug(source: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", Path(source).stem.lower()).strip("-") or "doc"


def chunk_document(sections: List[Section], cfg: ChunkingConfig = CHUNKING_CONFIG) -> List[Chunk]:
    """Chunk the sections of ONE document (in order)."""
    if not sections:
        return []

    # consecutive sections with the same heading (a PDF section running over a page) are packed together
    runs: List[List[Section]] = []
    for s in sections:
        if runs and runs[-1][0].section == s.section:
            runs[-1].append(s)
        else:
            runs.append([s])

    raws: List[RawChunk] = []
    for run in runs:
        units: List[Unit] = []
        for i, sec in enumerate(run):
            us = paragraph_units(sec, cfg.target_tokens)
            if i and units and us and not units[-1].text.rstrip().endswith(TERMINAL) \
                    and not LIST_START.match(us[0].text):
                us[0].joiner = " "                      # sentence continues on the next page
            units.extend(us)
        if units:
            raws.extend(pack(units, run[0].section, cfg.target_tokens, cfg.overlap_tokens,
                             cfg.min_tokens, cfg.max_tokens))

    raws = merge_tiny(raws, cfg.min_tokens, cfg.max_tokens)
    src, title, slug = sections[0].source, sections[0].title, _slug(sections[0].source)
    return [Chunk(chunk_id=f"{slug}-{i:03d}", text=r.text, source=src, title=title, section=r.section,
                  page=r.page, page_end=r.page_end, chunk_index=i, tokens=r.tokens)
            for i, r in enumerate(raws)]


def chunk_corpus(sections: List[Section], cfg: ChunkingConfig = CHUNKING_CONFIG) -> List[Chunk]:
    """Chunk sections from many documents (grouped by source, order kept)."""
    by_source: Dict[str, List[Section]] = {}
    for s in sections:
        by_source.setdefault(s.source, []).append(s)
    out: List[Chunk] = []
    for secs in by_source.values():
        out.extend(chunk_document(secs, cfg))
    return out
