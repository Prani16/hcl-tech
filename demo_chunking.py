import sys
from dataclasses import replace

from config import CHUNKING_CONFIG
from loaders import load_file
from chunking import chunk_document

path = sys.argv[1] if len(sys.argv) > 1 else "data/01_lalita_kumari_fir_guidelines.pdf"
target = int(sys.argv[2]) if len(sys.argv) > 2 else CHUNKING_CONFIG.target_tokens

# Step 1: load the file (loader gives sections split on headings)
sections = load_file(path)
print(f"\nSTEP 1: {len(sections)} sections loaded from {path}")
for s in sections:
    print(f"  - {s.section!r:55} page={s.page}  {len(s.text)} chars")

# Step 2: chunk with your chosen size
cfg = replace(CHUNKING_CONFIG, target_tokens=target)
chunks = chunk_document(sections, cfg)
print(f"\nSTEP 2: {len(chunks)} chunks (target={target} tokens, "
      f"overlap={cfg.overlap_tokens}, min={cfg.min_tokens})\n")

# Step 3: show each chunk with its metadata
for c in chunks:
    print("=" * 70)
    print(f"{c.chunk_id}   tokens={c.tokens}")
    print(f"citation : {c.citation()}")
    print(f"metadata : {c.metadata()}")
    print("-" * 70)
    print(c.text)
print("=" * 70)