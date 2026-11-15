"""Embed the chunks from the ingestion pipeline into a Chroma vector store.

Reuses pipeline.ingest() unchanged (load -> clean -> chunk), then:
embed each chunk with Gemini -> store in chroma_db/ -> write chroma_db/manifest.json.

    python embed.py                         # data/ -> chroma_db/
    python embed.py --chunks chunks.jsonl   # embed an existing chunks.jsonl instead of re-chunking
    python embed.py --query "Is FIR registration mandatory?"   # test search on the built store
    python embed.py --dry-run               # offline test with a fake embedder (no API key)
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from dataclasses import replace

from config import CHUNKING_CONFIG, PIPELINE_CONFIG
from embeddings import EMBEDDING_CONFIG, FakeEmbedder, GeminiEmbedder, build_store, search
from pipeline import ingest
from schema import Chunk


def chunks_from_jsonl(path: str):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            m = d["metadata"]
            out.append(Chunk(chunk_id=d["id"], text=d["text"], source=m["source"], title=m.get("title", ""),
                             section=m.get("section", ""), page=m.get("page"), page_end=m.get("page_end"),
                             chunk_index=m["chunk_index"], tokens=m["tokens"]))
    return out


def tokenizer_used() -> str:
    try:
        import tiktoken
        tiktoken.get_encoding(CHUNKING_CONFIG.tokenizer_name)
        return CHUNKING_CONFIG.tokenizer_name
    except Exception:
        return f"word estimate x{CHUNKING_CONFIG.words_to_tokens}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=PIPELINE_CONFIG.data_dir)
    ap.add_argument("--chunks", help="embed this chunks.jsonl instead of running the chunker")
    ap.add_argument("--db", default=EMBEDDING_CONFIG.persist_dir)
    ap.add_argument("--query", help="only run a test search against the existing store")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true", help="fake embeddings, no API calls")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = replace(EMBEDDING_CONFIG, persist_dir=args.db)
    embedder = FakeEmbedder(cfg) if args.dry_run else GeminiEmbedder(cfg)

    if args.query:
        for h in search(args.query, k=args.k, embedder=embedder, cfg=cfg):
            print(f"{h['score']:.3f}  {h['id']}  {h['citation']}\n       {h['text'][:160]!r}\n")
        return

    if args.chunks:
        chunks, errors = chunks_from_jsonl(args.chunks), []
    else:
        chunks, errors = ingest(args.path)
    for path, err in errors:
        print(f"SKIPPED {path}: {err}")
    if not chunks:
        raise SystemExit("No chunks to embed.")
    dupes = [i for i, n in Counter(c.chunk_id for c in chunks).items() if n > 1]
    if dupes:
        raise SystemExit(f"Duplicate chunk ids: {dupes[:5]}")

    vectors = embedder.embed_documents([c.embedding_text() for c in chunks])
    build_store(chunks, vectors, cfg, extra_manifest={
        "chunker": {"tokenizer": tokenizer_used(), "target_tokens": CHUNKING_CONFIG.target_tokens,
                    "overlap_ratio": CHUNKING_CONFIG.overlap_ratio, "min_tokens": CHUNKING_CONFIG.min_tokens},
        "embedded_text": "Chunk.embedding_text() = 'title > section' header + chunk text",
        "fake_embeddings": args.dry_run,
    })
    per = Counter(c.source for c in chunks)
    for src, n in per.items():
        print(f"{src:55s} {n:3d} chunks")
    print(f"\n{len(chunks)} chunks embedded ({cfg.model}, {cfg.output_dimensionality}d) "
          f"-> {cfg.persist_dir}/ collection '{cfg.collection_name}'")


if __name__ == "__main__":
    main()
