"""Run the whole ingestion: load -> clean -> chunk -> JSONL.

    python pipeline.py                      # uses config/pipeline_config.py
    python pipeline.py ./data --out chunks.jsonl --target 400 --overlap 0.15 --min 80
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from dataclasses import replace
from typing import List, Tuple

from chunking import chunk_corpus
from config import CHUNKING_CONFIG, LOADER_CONFIG, PIPELINE_CONFIG, ChunkingConfig, LoaderConfig
from loaders import load_directory
from schema import Chunk


def ingest(root=None, chunk_cfg: ChunkingConfig = CHUNKING_CONFIG,
           loader_cfg: LoaderConfig = LOADER_CONFIG) -> Tuple[List[Chunk], List[Tuple[str, str]]]:
    sections, errors = load_directory(root or PIPELINE_CONFIG.data_dir, loader_cfg)
    return chunk_corpus(sections, chunk_cfg), errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=PIPELINE_CONFIG.data_dir, help="folder or single file")
    ap.add_argument("--out", default=PIPELINE_CONFIG.output_file)
    ap.add_argument("--target", type=int, default=CHUNKING_CONFIG.target_tokens)
    ap.add_argument("--overlap", type=float, default=CHUNKING_CONFIG.overlap_ratio)
    ap.add_argument("--min", type=int, default=CHUNKING_CONFIG.min_tokens, dest="min_tokens")
    args = ap.parse_args()
    logging.basicConfig(level=getattr(logging, PIPELINE_CONFIG.log_level), format="%(levelname)s %(message)s")

    cfg = replace(CHUNKING_CONFIG, target_tokens=args.target, overlap_ratio=args.overlap, min_tokens=args.min_tokens)
    chunks, errors = ingest(args.path, cfg)
    with open(args.out, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

    per = defaultdict(list)
    for c in chunks:
        per[c.source].append(c.tokens)
    for src, toks in per.items():
        print(f"{src:55s} {len(toks):3d} chunks  avg {sum(toks)//len(toks):3d}  max {max(toks):3d} tokens")
    print(f"\n{len(chunks)} chunks from {len(per)} files -> {args.out}")
    for path, err in errors:
        print(f"SKIPPED {path}: {err}")


if __name__ == "__main__":
    main()
