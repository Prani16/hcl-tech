"""Settings for the loaders and cleaning. Edit values here, not in the loader code."""
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class LoaderConfig:
    # --- file discovery / format detection
    extensions: Dict[str, str] = field(default_factory=lambda: {
        ".pdf": "pdf", ".html": "html", ".htm": "html", ".xhtml": "html",
        ".md": "md", ".markdown": "md", ".txt": "txt", ".text": "txt",
    })
    sniff_bytes: int = 4096            # bytes read to detect a file with no known extension
    recursive: bool = True
    skip_hidden_files: bool = True

    # --- cleaning (repeated headers/footers)
    header_footer_zone: int = 3        # look at the first/last N lines of each page
    repeat_ratio: float = 0.5          # line must repeat on this share of pages (and >= 2 pages)

    # --- PDF
    pdf_heading_max_chars: int = 70
    pdf_heading_max_words: int = 10
    pdf_title_max_lines: int = 3       # a wrapped title can use up to this many lines
    pdf_title_wrap_min_chars: int = 40 # a title line this long may continue on the next line
    pdf_width_percentile: float = 0.85 # "full line width" used to spot paragraph ends
    pdf_short_line_ratio: float = 0.7  # a sentence-ending line shorter than this ends the paragraph

    # --- HTML
    html_junk_tags: Tuple[str, ...] = ("script", "style", "noscript", "nav", "footer", "iframe",
                                       "form", "template", "svg", "canvas", "button")
    html_junk_classes: Tuple[str, ...] = ("ad", "ads", "advert", "advertisement",
                                          "cookie-banner", "newsletter", "sponsored")
    html_main_content_ratio: float = 0.6   # use <main>/<article> if it holds this share of the text

    # --- TXT
    txt_detect_caps_headings: bool = True
    txt_heading_max_chars: int = 80
    txt_title_scan_lines: int = 15     # where to look for a "SUBJECT:" line


LOADER_CONFIG = LoaderConfig()
