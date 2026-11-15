"""Smart parser: detects the file format and calls the right loader. Never raises."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from config import LOADER_CONFIG, LoaderConfig
from schema import Section

from . import cleaning
from .html_loader import load_html
from .markdown_loader import load_markdown
from .pdf_loader import load_pdf
from .txt_loader import load_txt

log = logging.getLogger("rag_ingest.loaders")

LOADERS: Dict[str, Callable[..., List[Section]]] = {
    "pdf": load_pdf, "html": load_html, "md": load_markdown, "txt": load_txt,
}


def detect_format(path, cfg: LoaderConfig = LOADER_CONFIG) -> Optional[str]:
    """pdf | html | md | txt, or None if unsupported. Content wins over the extension for PDFs."""
    path = Path(path)
    with open(path, "rb") as f:
        head = f.read(cfg.sniff_bytes)
    if head.startswith(b"%PDF-"):
        return "pdf"
    ext = cfg.extensions.get(path.suffix.lower())
    if ext:
        return ext
    if b"\x00" in head:
        return None                                    # binary
    snippet = head.decode("utf-8", errors="ignore").lstrip().lower()
    if snippet.startswith(("<!doctype html", "<html")) or "<body" in snippet:
        return "html"
    if re.search(r"^#{1,6}\s+\S", snippet, re.M):
        return "md"
    return "txt"


def load_file(path, errors: Optional[list] = None, cfg: LoaderConfig = LOADER_CONFIG) -> List[Section]:
    """Detect the format, parse, clean. Never raises: a failing file is skipped."""
    path = Path(path)
    try:
        fmt = detect_format(path, cfg)
        if fmt is None:
            raise ValueError("unsupported or binary file")
        out = []
        for sec in LOADERS[fmt](path, cfg):
            sec.text = cleaning.clean_text(sec.text)
            if sec.text:
                out.append(sec)
        if not out:
            raise ValueError("no text extracted")
        return out
    except Exception as exc:                           # noqa: BLE001 - skip, don't crash
        log.warning("Skipping %s: %s: %s", path.name, type(exc).__name__, exc)
        if errors is not None:
            errors.append((str(path), f"{type(exc).__name__}: {exc}"))
        return []


def load_directory(root, cfg: LoaderConfig = LOADER_CONFIG) -> Tuple[List[Section], List[Tuple[str, str]]]:
    """Load every file under `root`. Returns (sections, [(path, error), ...])."""
    root = Path(root)
    if root.is_file():
        paths = [root]
    else:
        paths = sorted(root.rglob("*") if cfg.recursive else root.glob("*"))
    sections: List[Section] = []
    errors: List[Tuple[str, str]] = []
    for p in paths:
        if not p.is_file() or (cfg.skip_hidden_files and p.name.startswith(".")):
            continue
        sections.extend(load_file(p, errors, cfg))
    return sections, errors
