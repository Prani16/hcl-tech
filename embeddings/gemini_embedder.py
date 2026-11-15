"""Gemini embeddings (google-genai SDK) with batching, retries and L2 normalisation."""
from __future__ import annotations

import logging
import math
import os
import time
from pathlib import Path
from typing import List, Sequence

from .config import EMBEDDING_CONFIG, EmbeddingConfig

log = logging.getLogger(__name__)


def _load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env reader (KEY=VALUE lines) so python-dotenv is not needed."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _normalise(vec: Sequence[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


class GeminiEmbedder:
    def __init__(self, cfg: EmbeddingConfig = EMBEDDING_CONFIG, api_key: str | None = None):
        from google import genai  # imported here so --dry-run works without the SDK

        _load_dotenv()
        key = api_key or os.environ.get(cfg.api_key_env)
        if not key:
            raise RuntimeError(f"Set {cfg.api_key_env} in your environment or in a .env file.")
        self.cfg = cfg
        self.client = genai.Client(api_key=key)

    def _embed_batch(self, texts: List[str], task_type: str) -> List[List[float]]:
        from google.genai import errors, types

        conf = types.EmbedContentConfig(task_type=task_type,
                                        output_dimensionality=self.cfg.output_dimensionality)
        for attempt in range(self.cfg.max_retries + 1):
            try:
                res = self.client.models.embed_content(model=self.cfg.model, contents=texts, config=conf)
                return [_normalise(e.values) for e in res.embeddings]
            except errors.APIError as e:
                retryable = getattr(e, "code", None) in (429, 500, 502, 503, 504)
                if not retryable or attempt == self.cfg.max_retries:
                    raise
                wait = min(60, 2 ** attempt)
                log.warning("Gemini API %s, retrying in %ss", e.code, wait)
                time.sleep(wait)
        raise RuntimeError("unreachable")

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        out: List[List[float]] = []
        bs = self.cfg.batch_size
        for i in range(0, len(texts), bs):
            out.extend(self._embed_batch(list(texts[i:i + bs]), self.cfg.document_task_type))
            log.info("embedded %d/%d", min(i + bs, len(texts)), len(texts))
        return out

    def embed_query(self, text: str) -> List[float]:
        return self._embed_batch([text], self.cfg.query_task_type)[0]


class FakeEmbedder:
    """Deterministic offline stand-in (hash-based). For --dry-run tests only; not semantic."""

    def __init__(self, cfg: EmbeddingConfig = EMBEDDING_CONFIG):
        self.cfg = cfg

    def _vec(self, text: str) -> List[float]:
        import hashlib
        dim, v = self.cfg.output_dimensionality, [0.0] * self.cfg.output_dimensionality
        for w in text.lower().split():
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            v[h % dim] += 1.0
        return _normalise(v)

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vec(text)
