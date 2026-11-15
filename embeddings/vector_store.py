"""Chroma vector store: build from chunks, and search (the function the backend calls)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from schema import Chunk

from .config import EMBEDDING_CONFIG, EmbeddingConfig


def _client(cfg: EmbeddingConfig):
    import chromadb
    return chromadb.PersistentClient(path=cfg.persist_dir)


def build_store(chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]],
                cfg: EmbeddingConfig = EMBEDDING_CONFIG, extra_manifest: Optional[Dict] = None):
    """Replace the collection with these chunks (a rebuild never leaves stale chunks behind)."""
    client = _client(cfg)
    if cfg.collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(cfg.collection_name)
    col = client.create_collection(cfg.collection_name, configuration={"hnsw": {"space": cfg.distance}})
    col.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=[list(v) for v in vectors],
        documents=[c.text for c in chunks],
        metadatas=[{**c.metadata(), "citation": c.citation()} for c in chunks],
    )
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embedding_model": cfg.model,
        "dimensions": cfg.output_dimensionality,
        "document_task_type": cfg.document_task_type,
        "query_task_type": cfg.query_task_type,
        "collection": cfg.collection_name,
        "distance": cfg.distance,
        "chunk_count": len(chunks),
        "sources": sorted({c.source for c in chunks}),
        **(extra_manifest or {}),
    }
    Path(cfg.persist_dir, "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return col


def search(query: str, k: int = 5, embedder=None, cfg: EmbeddingConfig = EMBEDDING_CONFIG,
           where: Optional[Dict] = None) -> List[Dict]:
    """Top-k chunks for a question. Each hit: id, text, score (cosine similarity), metadata, citation.

    Backend usage:
        from embeddings import search
        hits = search("Is registration of an FIR mandatory?", k=5)
    """
    if embedder is None:
        from .gemini_embedder import GeminiEmbedder
        embedder = GeminiEmbedder(cfg)
    col = _client(cfg).get_collection(cfg.collection_name)
    res = col.query(query_embeddings=[embedder.embed_query(query)], n_results=k, where=where,
                    include=["documents", "metadatas", "distances"])
    return [{"id": i, "text": d, "score": round(1 - dist, 4), "metadata": m, "citation": m.get("citation", "")}
            for i, d, m, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0])]
