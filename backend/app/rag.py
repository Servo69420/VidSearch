"""RAG pipeline: chunk → embed → summarize → store.

This module defines the processing stages and the orchestrator that
turns a raw transcription (full_text + segments JSONB) into searchable
transcript_chunks with vector embeddings.

Usage (called after transcription is complete)::

    pipeline = RAGPipeline(db)
    await pipeline.process(transcription_id)
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.model_config import MODEL_CONFIG
from app.embedder import OpenRouterEmbedder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Segment:
    """Single transcript segment straight from the JSONB column."""
    idx: int
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Chunk:
    """A group of consecutive segments treated as one semantic unit."""
    idx: int
    level: int
    start_s: float
    end_s: float
    text: str
    segment_start_idx: int | None = None
    segment_end_idx: int | None = None
    segments: tuple[Segment, ...] = field(default_factory=tuple, repr=False)


@dataclass
class ProcessedChunk:
    """Chunk after embedding + summarization — ready for DB insert."""
    chunk_id: str
    idx: int
    level: int
    start_s: float
    end_s: float
    text: str
    parent_chunk_id: str | None = None
    segment_start_idx: int | None = None
    segment_end_idx: int | None = None
    summary: str | None = None
    role: str | None = None
    keywords: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    summary_embedding: list[float] | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    idx: int
    level: int
    start_s: float
    end_s: float
    text: str
    score: float
    topic_summary: str | None = None


# ---------------------------------------------------------------------------
# Abstract stage interfaces — swap implementations freely
# ---------------------------------------------------------------------------

class ChunkingStrategy(ABC):
    """Decides how raw segments are grouped into chunks."""

    @abstractmethod
    def chunk(self, segments: list[Segment]) -> list[Chunk]:
        ...


class Embedder(ABC):
    """Produces a dense vector from text."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class Summarizer(ABC):
    """Produces a short summary + optional metadata for a chunk."""

    @abstractmethod
    async def summarize(self, chunk: Chunk) -> tuple[str, str | None, list[str]]:
        """Return (summary, role, keywords)."""
        ...


# ---------------------------------------------------------------------------
# Default / placeholder implementations
# ---------------------------------------------------------------------------

class FixedWindowChunker(ChunkingStrategy):
    """Group every `window` consecutive segments into one chunk.

    Good enough baseline — replace with a semantic or sentence-boundary
    chunker later.
    """

    def __init__(self, window: int = 10) -> None:
        self._window = window

    def chunk(self, segments: list[Segment]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for i in range(0, len(segments), self._window):
            batch = segments[i : i + self._window]
            chunks.append(
                Chunk(
                    idx=len(chunks),
                    level=1,
                    start_s=batch[0].start,
                    end_s=batch[-1].end,
                    text=" ".join(s.text for s in batch),
                    segment_start_idx=batch[0].idx,
                    segment_end_idx=batch[-1].idx,
                    segments=tuple(batch),
                )
            )
        return chunks


class PlaceholderEmbedder(Embedder):
    """Returns zero-vectors. Replace with a real model for production."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * MODEL_CONFIG.embedding_dimensions for _ in texts]


class PlaceholderSummarizer(Summarizer):
    """Returns the first 120 chars as "summary".  Replace with an LLM call."""

    async def summarize(self, chunk: Chunk) -> tuple[str, str | None, list[str]]:
        summary = chunk.text[:120].strip()
        role = None
        keywords: list[str] = []
        return summary, role, keywords


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class RAGPipeline:
    """Orchestrates chunk → embed → summarize → store.

    Parameters
    ----------
    db : asyncpg connection / pool acquired connection
    chunker, embedder, summarizer : plug-in strategy objects
    """

    def __init__(
        self,
        db,
        *,
        chunker: ChunkingStrategy | None = None,
        embedder: Embedder | None = None,
        summarizer: Summarizer | None = None,
        embed_batch_size: int = MODEL_CONFIG.rag_embed_batch_size,
    ) -> None:
        self._db = db
        self._chunker = chunker or FixedWindowChunker()
        self._embedder = embedder or OpenRouterEmbedder()
        self._summarizer = summarizer
        self._embed_batch_size = max(embed_batch_size, 1)

    # -- public entry point -------------------------------------------------

    async def process(self, transcription_id: str) -> list[ProcessedChunk]:
        """Run the full pipeline for one transcription.

        Updates ``transcriptions.status`` as it progresses through
        ``chunking → summarizing → ready`` (or ``failed``).
        """
        try:
            await self._set_status(transcription_id, "chunking")
            segments = await self._load_segments(transcription_id)
            leaf_chunks = self._chunker.chunk(segments)
            logger.info(
                "RAG chunking complete for %s (segments=%s, leaf_chunks=%s)",
                transcription_id,
                len(segments),
                len(leaf_chunks),
            )

            await self._set_status(transcription_id, "summarizing")

            processed_leaves = await self._embed_leaf_chunks(leaf_chunks)
            processed_topics: list[ProcessedChunk] = []

            if self._summarizer and processed_leaves:
                topic_ranges = self._build_topic_ranges(processed_leaves)
                topic_chunks = self._build_topic_chunks(leaf_chunks, topic_ranges)
                processed_topics = await self._summarize_topic_chunks(topic_chunks)
                self._attach_topic_parents(
                    processed_leaves,
                    processed_topics,
                    topic_ranges,
                )
                logger.info(
                    "RAG phase-2 topics complete for %s (topic_chunks=%s)",
                    transcription_id,
                    len(processed_topics),
                )

            processed = processed_topics + processed_leaves

            await self._store_chunks(transcription_id, processed)
            await self._set_status(transcription_id, "ready")
            logger.info(
                "RAG indexing ready for %s (chunks=%s)",
                transcription_id,
                len(processed),
            )
            return processed

        except Exception:
            logger.exception("RAG pipeline failed for %s", transcription_id)
            await self._set_status(transcription_id, "failed")
            raise

    async def search(
        self,
        transcription_id: str,
        query: str,
        *,
        top_k: int = 6,
    ) -> list[RetrievedChunk]:
        if not query.strip() or top_k <= 0:
            return []

        query_vector = (await self._embedder.embed([query]))[0]
        query_vector_literal = str(query_vector)

        topic_hits = await self._search_topic_first(
            transcription_id,
            query_vector_literal,
            top_k,
        )
        logger.info(
            "RAG topic-first search for %s returned %s chunks (top_k=%s)",
            transcription_id,
            len(topic_hits),
            top_k,
        )
        return topic_hits[:top_k]

    async def _search_topic_first(
        self,
        transcription_id: str,
        query_vector_literal: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        topic_rows = await self._db.fetch(
            """SELECT id, idx, start_s, end_s, summary,
                      (1 - (summary_embedding <=> $2::vector)) AS score
               FROM transcript_chunks
               WHERE transcription_id = $1::uuid
                 AND level = 2
                 AND summary_embedding IS NOT NULL
               ORDER BY summary_embedding <=> $2::vector
               LIMIT $3""",
            transcription_id,
            query_vector_literal,
            max(1, top_k),
        )
        if not topic_rows:
            return []

        hits: list[RetrievedChunk] = []
        for topic in topic_rows:
            child_rows = await self._db.fetch(
                """SELECT idx, start_s, end_s, text,
                          (1 - (embedding <=> $3::vector)) AS score
                   FROM transcript_chunks
                   WHERE transcription_id = $1::uuid
                     AND level = 1
                     AND parent_chunk_id = $2::uuid
                     AND embedding IS NOT NULL
                   ORDER BY embedding <=> $3::vector
                   LIMIT 2""",
                transcription_id,
                topic["id"],
                query_vector_literal,
            )

            topic_score = float(topic["score"] or 0.0)
            topic_summary = topic["summary"] or ""

            if child_rows:
                for child in child_rows:
                    hits.append(
                        RetrievedChunk(
                            idx=child["idx"],
                            level=1,
                            start_s=child["start_s"],
                            end_s=child["end_s"],
                            text=child["text"],
                            score=float(child["score"] or topic_score),
                            topic_summary=topic_summary,
                        )
                    )
            else:
                hits.append(
                    RetrievedChunk(
                        idx=topic["idx"],
                        level=2,
                        start_s=topic["start_s"],
                        end_s=topic["end_s"],
                        text=topic_summary,
                        score=topic_score,
                        topic_summary=topic_summary,
                    )
                )

        hits.sort(key=lambda item: item.score, reverse=True)
        return hits

    # -- internal helpers ---------------------------------------------------

    async def _load_segments(self, transcription_id: str) -> list[Segment]:
        row = await self._db.fetchrow(
            "SELECT segments FROM transcriptions WHERE id = $1::uuid",
            transcription_id,
        )
        if row is None:
            raise ValueError(f"Transcription {transcription_id} not found")

        raw = row["segments"]
        if isinstance(raw, str):
            raw = json.loads(raw)

        return [
            Segment(
                idx=i,
                start=s["start"],
                end=s["end"],
                text=s["text"],
            )
            for i, s in enumerate(raw)
        ]

    async def _embed_leaf_chunks(self, chunks: list[Chunk]) -> list[ProcessedChunk]:
        texts = [c.text for c in chunks]
        embeddings = await self._embed_texts(texts)

        processed: list[ProcessedChunk] = []
        for chunk, emb in zip(chunks, embeddings):
            processed.append(
                ProcessedChunk(
                    chunk_id=str(uuid.uuid4()),
                    idx=chunk.idx,
                    level=1,
                    start_s=chunk.start_s,
                    end_s=chunk.end_s,
                    text=chunk.text,
                    segment_start_idx=chunk.segment_start_idx,
                    segment_end_idx=chunk.segment_end_idx,
                    embedding=emb,
                    summary_embedding=None,
                )
            )
        return processed

    def _build_topic_ranges(self, leaves: list[ProcessedChunk]) -> list[tuple[int, int]]:
        if not leaves:
            return []

        min_leaves = MODEL_CONFIG.phase2_topic_min_leaf_chunks
        max_leaves = max(min_leaves, MODEL_CONFIG.phase2_topic_max_leaf_chunks)
        break_similarity = MODEL_CONFIG.phase2_topic_break_similarity

        ranges: list[tuple[int, int]] = []
        start = 0

        for idx in range(1, len(leaves)):
            prev = leaves[idx - 1].embedding or []
            curr = leaves[idx].embedding or []
            similarity = self._vector_similarity(prev, curr)
            current_size = idx - start

            should_break = current_size >= max_leaves or (
                current_size >= min_leaves and similarity < break_similarity
            )
            if should_break:
                ranges.append((start, idx - 1))
                start = idx

        ranges.append((start, len(leaves) - 1))

        if len(ranges) >= 2:
            last_start, last_end = ranges[-1]
            if last_end - last_start + 1 < min_leaves:
                prev_start, _ = ranges[-2]
                ranges[-2] = (prev_start, last_end)
                ranges.pop()

        return ranges

    def _vector_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 1.0

        dot = 0.0
        norm_left = 0.0
        norm_right = 0.0
        for a, b in zip(left, right):
            dot += a * b
            norm_left += a * a
            norm_right += b * b

        if norm_left <= 0.0 or norm_right <= 0.0:
            return 0.0
        return dot / (math.sqrt(norm_left) * math.sqrt(norm_right))

    def _build_topic_chunks(
        self,
        leaves: list[Chunk],
        topic_ranges: list[tuple[int, int]],
    ) -> list[Chunk]:
        topics: list[Chunk] = []
        for idx, (start_leaf_idx, end_leaf_idx) in enumerate(topic_ranges):
            batch = leaves[start_leaf_idx : end_leaf_idx + 1]
            topics.append(
                Chunk(
                    idx=idx,
                    level=2,
                    start_s=batch[0].start_s,
                    end_s=batch[-1].end_s,
                    text=" ".join(item.text for item in batch),
                    segment_start_idx=batch[0].segment_start_idx,
                    segment_end_idx=batch[-1].segment_end_idx,
                )
            )
        return topics

    async def _summarize_topic_chunks(
        self,
        topic_chunks: list[Chunk],
    ) -> list[ProcessedChunk]:
        if not self._summarizer:
            return []

        processed: list[ProcessedChunk] = []
        for topic in topic_chunks:
            summary, role, keywords = await self._summarizer.summarize(topic)
            summary_vector = None
            if summary:
                summary_vector = (await self._embed_texts([summary]))[0]

            processed.append(
                ProcessedChunk(
                    chunk_id=str(uuid.uuid4()),
                    idx=topic.idx,
                    level=2,
                    start_s=topic.start_s,
                    end_s=topic.end_s,
                    text=topic.text,
                    segment_start_idx=topic.segment_start_idx,
                    segment_end_idx=topic.segment_end_idx,
                    summary=summary,
                    role=role,
                    keywords=keywords,
                    embedding=None,
                    summary_embedding=summary_vector,
                )
            )

        return processed

    def _attach_topic_parents(
        self,
        leaves: list[ProcessedChunk],
        topics: list[ProcessedChunk],
        topic_ranges: list[tuple[int, int]],
    ) -> None:
        for topic, (start_idx, end_idx) in zip(topics, topic_ranges):
            for leaf_idx in range(start_idx, end_idx + 1):
                leaves[leaf_idx].parent_chunk_id = topic.chunk_id

    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self._embed_batch_size):
            batch = texts[i : i + self._embed_batch_size]
            vectors.extend(await self._embedder.embed(batch))
        return vectors

    async def _store_chunks(
        self,
        transcription_id: str,
        chunks: list[ProcessedChunk],
    ) -> None:
        await self._db.execute(
            "DELETE FROM transcript_chunks WHERE transcription_id = $1::uuid",
            transcription_id,
        )

        for c in chunks:
            await self._db.execute(
                """INSERT INTO transcript_chunks
                   (id, transcription_id, idx, level, parent_chunk_id,
                    start_s, end_s, text, segment_start_idx, segment_end_idx,
                    summary, role, keywords, embedding, summary_embedding)
                   VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid,
                           $6, $7, $8, $9, $10, $11, $12, $13,
                           $14::vector, $15::vector)""",
                c.chunk_id,
                transcription_id,
                c.idx,
                c.level,
                c.parent_chunk_id,
                c.start_s,
                c.end_s,
                c.text,
                c.segment_start_idx,
                c.segment_end_idx,
                c.summary,
                c.role,
                c.keywords,
                str(c.embedding) if c.embedding else None,
                str(c.summary_embedding) if c.summary_embedding else None,
            )

    async def _set_status(self, transcription_id: str, status: str) -> None:
        await self._db.execute(
            "UPDATE transcriptions SET status = $1 WHERE id = $2::uuid",
            status,
            transcription_id,
        )
        logger.info("Transcription %s → %s", transcription_id, status)
