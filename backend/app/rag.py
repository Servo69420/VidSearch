"""RAG pipeline: chunk → embed → store.

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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.openrouter_embedder import OpenRouterEmbedder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Segment:
    """Single transcript segment straight from the JSONB column."""
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Chunk:
    """A group of consecutive segments treated as one semantic unit."""
    idx: int
    start_s: float
    end_s: float
    text: str
    segments: tuple[Segment, ...] = field(repr=False)


@dataclass
class ProcessedChunk:
    """Chunk after embedding + summarization — ready for DB insert."""
    idx: int
    start_s: float
    end_s: float
    text: str
    summary: str | None = None
    role: str | None = None
    keywords: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    summary_embedding: list[float] | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    idx: int
    start_s: float
    end_s: float
    text: str
    score: float


# ---------------------------------------------------------------------------
# Abstract stage interfaces — swap implementations freely
# ---------------------------------------------------------------------------

class ChunkingStrategy(ABC):
    """Decides how raw segments are grouped into chunks."""

    @abstractmethod
    def chunk(self, segments: list[Segment]) -> list[Chunk]:
        ...


class Embedder(ABC):
    """Produces a dense vector from text.  Dimension must be 1024."""

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
                    start_s=batch[0].start,
                    end_s=batch[-1].end,
                    text=" ".join(s.text for s in batch),
                    segments=tuple(batch),
                )
            )
        return chunks


class PlaceholderEmbedder(Embedder):
    """Returns zero-vectors. Replace with a real model for production."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 1024 for _ in texts]


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
        embed_batch_size: int = 24,
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
            chunks = self._chunker.chunk(segments)
            logger.info(
                "RAG chunking complete for %s (segments=%s, chunks=%s)",
                transcription_id,
                len(segments),
                len(chunks),
            )

            await self._set_status(transcription_id, "summarizing")
            processed = await self._embed_and_summarize(chunks)

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
        row_set = await self._db.fetch(
            """SELECT idx, start_s, end_s, text,
                      (1 - (embedding <=> $2::vector)) AS score
               FROM transcript_chunks
               WHERE transcription_id = $1::uuid
                 AND embedding IS NOT NULL
               ORDER BY embedding <=> $2::vector
               LIMIT $3""",
            transcription_id,
            str(query_vector),
            top_k,
        )

        logger.info(
            "RAG search for %s returned %s chunks (top_k=%s)",
            transcription_id,
            len(row_set),
            top_k,
        )

        return [
            RetrievedChunk(
                idx=row["idx"],
                start_s=row["start_s"],
                end_s=row["end_s"],
                text=row["text"],
                score=float(row["score"]) if row["score"] is not None else 0.0,
            )
            for row in row_set
        ]

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

        return [Segment(start=s["start"], end=s["end"], text=s["text"]) for s in raw]

    async def _embed_and_summarize(
        self, chunks: list[Chunk]
    ) -> list[ProcessedChunk]:
        # Batch-embed chunk texts in provider-safe batches
        texts = [c.text for c in chunks]
        embeddings = await self._embed_texts(texts)

        processed: list[ProcessedChunk] = []
        for chunk, emb in zip(chunks, embeddings):
            summary: str | None = None
            role: str | None = None
            keywords: list[str] = []
            if self._summarizer:
                summary, role, keywords = await self._summarizer.summarize(chunk)

            processed.append(
                ProcessedChunk(
                    idx=chunk.idx,
                    start_s=chunk.start_s,
                    end_s=chunk.end_s,
                    text=chunk.text,
                    summary=summary,
                    role=role,
                    keywords=keywords,
                    embedding=emb,
                    summary_embedding=None,
                )
            )
        return processed

    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), self._embed_batch_size):
            batch = texts[i : i + self._embed_batch_size]
            vectors.extend(await self._embedder.embed(batch))
        return vectors

    async def _store_chunks(
        self, transcription_id: str, chunks: list[ProcessedChunk]
    ) -> None:
        # Clear any previous chunks for idempotency
        await self._db.execute(
            "DELETE FROM transcript_chunks WHERE transcription_id = $1::uuid",
            transcription_id,
        )
        for c in chunks:
            await self._db.execute(
                """INSERT INTO transcript_chunks
                   (transcription_id, idx, start_s, end_s, text,
                    summary, role, keywords, embedding, summary_embedding)
                   VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8,
                           $9::vector, $10::vector)""",
                transcription_id,
                c.idx,
                c.start_s,
                c.end_s,
                c.text,
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
