"""RAG pipeline: chunk → embed → summarize → store.

This module defines the processing stages and the orchestrator that
turns a raw transcription (full_text + segments JSONB) into searchable
transcript_chunks with vector embeddings.

Usage (called after transcription is complete)::

    pipeline = RAGPipeline(db)
    await pipeline.process(transcription_id)
"""
#TODO: INCOMPLETE
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

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


# ---------------------------------------------------------------------------
# Abstract stage interfaces — swap implementations freely
# ---------------------------------------------------------------------------

class ChunkingStrategy(ABC):
    """Decides how raw segments are grouped into chunks."""

    @abstractmethod
    def chunk(self, segments: list[Segment]) -> list[Chunk]:
        ...


class Embedder(ABC):
    """Produces a dense vector from text.  Dimension must be 384."""

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
    """Returns zero-vectors.  Replace with a real model (e.g. sentence-
    transformers ``all-MiniLM-L6-v2`` or ``bge-small-en-v1.5``).
    """

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


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
    ) -> None:
        self._db = db
        self._chunker = chunker or FixedWindowChunker()
        self._embedder = embedder or PlaceholderEmbedder()
        self._summarizer = summarizer or PlaceholderSummarizer()

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

            await self._set_status(transcription_id, "summarizing")
            processed = await self._embed_and_summarize(chunks)

            await self._store_chunks(transcription_id, processed)
            await self._set_status(transcription_id, "ready")
            return processed

        except Exception:
            logger.exception("RAG pipeline failed for %s", transcription_id)
            await self._set_status(transcription_id, "failed")
            raise

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
        # Batch-embed all chunk texts at once
        texts = [c.text for c in chunks]
        embeddings = await self._embedder.embed(texts)

        processed: list[ProcessedChunk] = []
        for chunk, emb in zip(chunks, embeddings):
            summary, role, keywords = await self._summarizer.summarize(chunk)

            # Embed the summary too (for summary-level search)
            summary_emb = (await self._embedder.embed([summary]))[0] if summary else None

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
                    summary_embedding=summary_emb,
                )
            )
        return processed

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
