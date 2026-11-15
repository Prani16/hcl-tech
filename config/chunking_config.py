"""Settings for the chunker. Edit values here, not in the chunking code."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkingConfig:
    target_tokens: int = 400
    overlap_ratio: float = 0.15        # ~15% of target
    min_tokens: int = 80               # smaller chunks are merged into a neighbour
    max_tokens_factor: float = 1.5     # hard ceiling = target * factor
    tokenizer_name: str = "cl100k_base"
    words_to_tokens: float = 1.3       # used only when tiktoken is not available

    @property
    def max_tokens(self) -> int:
        return int(self.target_tokens * self.max_tokens_factor)

    @property
    def overlap_tokens(self) -> int:
        return int(self.target_tokens * self.overlap_ratio)


CHUNKING_CONFIG = ChunkingConfig()
