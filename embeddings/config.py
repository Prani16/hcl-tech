"""Settings for the embedding step. Edit values here, not in the embedding code.

The backend MUST embed user queries with the same model and dimensionality
used here, otherwise similarity search returns garbage. The values used for
a build are also written to chroma_db/manifest.json.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingConfig:
    # --- Gemini embedding model
    model: str = "gemini-embedding-001"
    output_dimensionality: int = 768       # 768 / 1536 / 3072 supported; vectors below 3072 are re-normalised
    document_task_type: str = "RETRIEVAL_DOCUMENT"
    query_task_type: str = "RETRIEVAL_QUERY"
    batch_size: int = 50                   # texts per API call
    max_retries: int = 6                   # on 429 / 5xx, with exponential backoff
    api_key_env: str = "GEMINI_API_KEY"    # also read from a .env file in the repo root

    # --- Chroma vector store
    persist_dir: str = "chroma_db"
    collection_name: str = "police_complaints"
    distance: str = "cosine"


EMBEDDING_CONFIG = EmbeddingConfig()
