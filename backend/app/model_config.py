from __future__ import annotations

import os
from dataclasses import dataclass


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class ModelConfig:
    chat_model: str
    vision_model: str
    viz_model: str
    embedding_model: str
    phase2_summary_model: str
    phase3_summary_model: str
    openrouter_timeout_s: float
    embedding_dimensions: int
    rag_embed_batch_size: int
    rag_retrieval_top_k: int
    phase2_topic_min_leaf_chunks: int
    phase2_topic_max_leaf_chunks: int
    phase2_topic_break_similarity: float
    phase3_section_min_topic_chunks: int
    phase3_section_max_topic_chunks: int
    phase3_section_break_similarity: float


_phase3_section_min = max(1, _env_int("PHASE3_SECTION_MIN_TOPIC_CHUNKS", 2))
_phase3_section_max = max(
    _phase3_section_min,
    _env_int("PHASE3_SECTION_MAX_TOPIC_CHUNKS", 4),
)

MODEL_CONFIG = ModelConfig(
    chat_model=os.getenv("OPENROUTER_CHAT_MODEL", "google/gemma-4-31b-it:exacto"),
    vision_model=os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.0-flash-001"),
    # Dedicated model for the separate visualization-generation call. Defaults
    # to the chat model; point OPENROUTER_VIZ_MODEL at a stronger coding model
    # for richer artifacts without touching code.
    viz_model=os.getenv(
        "OPENROUTER_VIZ_MODEL",
        os.getenv("OPENROUTER_CHAT_MODEL", "qwen/qwen3.6-35b-a3b:exacto"),
    ),
    embedding_model=os.getenv(
        "OPENROUTER_EMBEDDING_MODEL",
        "perplexity/pplx-embed-v1-0.6b",
    ),
    phase2_summary_model=os.getenv(
        "OPENROUTER_PHASE2_SUMMARY_MODEL",
        "google/gemini-2.5-flash-lite:nitro",
    ),
    phase3_summary_model=os.getenv(
        "OPENROUTER_PHASE3_SUMMARY_MODEL",
        "google/gemini-2.5-flash-lite:nitro",
    ),
    openrouter_timeout_s=_env_float("OPENROUTER_TIMEOUT_S", 60.0),
    embedding_dimensions=_env_int("OPENROUTER_EMBEDDING_DIMENSIONS", 1024),
    rag_embed_batch_size=max(1, _env_int("RAG_EMBED_BATCH_SIZE", 24)),
    rag_retrieval_top_k=max(1, _env_int("RAG_RETRIEVAL_TOP_K", 6)),
    phase2_topic_min_leaf_chunks=max(1, _env_int("PHASE2_TOPIC_MIN_LEAF_CHUNKS", 2)),
    phase2_topic_max_leaf_chunks=max(1, _env_int("PHASE2_TOPIC_MAX_LEAF_CHUNKS", 6)),
    phase2_topic_break_similarity=_env_float("PHASE2_TOPIC_BREAK_SIMILARITY", 0.68),
    phase3_section_min_topic_chunks=_phase3_section_min,
    phase3_section_max_topic_chunks=_phase3_section_max,
    phase3_section_break_similarity=_env_float("PHASE3_SECTION_BREAK_SIMILARITY", 0.68),
)
