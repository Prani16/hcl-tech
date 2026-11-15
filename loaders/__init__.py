from .smart_loader import load_file, load_directory, detect_format
from .pdf_loader import load_pdf
from .html_loader import load_html
from .markdown_loader import load_markdown
from .txt_loader import load_txt
from . import cleaning

__all__ = ["load_file", "load_directory", "detect_format",
           "load_pdf", "load_html", "load_markdown", "load_txt", "cleaning"]