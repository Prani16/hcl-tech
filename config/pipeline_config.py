"""Paths and run settings for pipeline.py."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    data_dir: str = "data"
    output_file: str = "chunks.jsonl"
    log_level: str = "INFO"


PIPELINE_CONFIG = PipelineConfig()
