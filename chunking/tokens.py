"""Token counting. Uses tiktoken when available, else a word-count estimate."""
from __future__ import annotations

import logging
import math

from config import CHUNKING_CONFIG

log = logging.getLogger("rag_ingest.chunking")
_enc = None


def _encoder():
    global _enc
    if _enc is None:
        try:
            import tiktoken
            _enc = tiktoken.get_encoding(CHUNKING_CONFIG.tokenizer_name)
        except Exception as exc:                       # not installed, or no network for the vocab
            log.info("tiktoken unavailable (%s); using word-count estimate", exc)
            _enc = False
    return _enc


def count_tokens(text: str) -> int:
    enc = _encoder()
    if enc:
        return len(enc.encode(text, disallowed_special=()))
    return max(1, math.ceil(len(text.split()) * CHUNKING_CONFIG.words_to_tokens))


def tail_words(text: str, n_tokens: int) -> str:
    """The last words of `text`, up to about n_tokens tokens (used for overlap)."""
    words = text.split()
    if n_tokens <= 0 or not words:
        return ""
    k = min(len(words), max(1, int(n_tokens / CHUNKING_CONFIG.words_to_tokens)))
    while k > 1 and count_tokens(" ".join(words[-k:])) > n_tokens:
        k = int(k * 0.9)
    return " ".join(words[-k:])
