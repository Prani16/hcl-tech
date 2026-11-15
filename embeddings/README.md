# Embeddings: chunks → Gemini → Chroma

This step comes after the ingestion pipeline (`pipeline.py`) and doesn't change it. It reuses
`pipeline.ingest()` as is and embeds each `Chunk.embedding_text()` (the `title > section` header plus the chunk text).

| Setting | Value (`embeddings/config.py`) |
|---|---|
| Model | `gemini-embedding-001`, 768 dimensions, L2-normalised |
| Task types | `RETRIEVAL_DOCUMENT` for chunks, `RETRIEVAL_QUERY` for questions |
| Store | Chroma, persisted in `chroma_db/`, collection `police_complaints`, cosine distance |
| Build info | `chroma_db/manifest.json` (model, dims, chunk count, chunker settings, build time) |

## Build

```bash
pip install -r requirements.txt
echo "GEMINI_API_KEY=your-key" > .env        # .env is already gitignored
python embed.py                               # data/ -> chroma_db/
python embed.py --query "Is FIR registration mandatory?"   # sanity check
```

Re-running `embed.py` rebuilds the collection from scratch, so stale chunks are never left behind.

## Backend usage

```python
from embeddings import search
hits = search("What must police do within 24 hours of a custodial death?", k=5)
# each hit: {"id", "text", "score" (cosine similarity), "metadata", "citation"}
# filter to one document: search(q, where={"source": "08_zero_fir_sop.md"})
```

Queries must be embedded with the same model and dimensionality as the stored chunks. `search()` does
this already. If the backend embeds queries itself, it must use the values in `chroma_db/manifest.json`.

Data provenance: see [`../DATA_SOURCES.md`](../DATA_SOURCES.md).
