import asyncio
import json
import logging
from abc import ABC, abstractmethod

import whisper
from youtube_transcript_api import YouTubeTranscriptApi

from app.model_config import MODEL_CONFIG
from app.embedder import OpenRouterEmbedder
from app.summarizer import OpenRouterSummarizer
from app.rag import RAGPipeline
from app.video_to_audio import delete_temporary_audio_file, video_to_audio
from app.youtube import (
    YOUTUBE_ID_SQL_EXPR,
    extract_video_id,
    resolve_or_create_yt_video,
)


logger = logging.getLogger(__name__)


async def _run_rag_pipeline(
    db,
    transcription_id: str,
    embed_model: str,
    summary_model: str,
) -> None:
    logger.info(
        "Starting RAG indexing for transcription %s (embed=%s summary=%s)",
        transcription_id,
        embed_model,
        summary_model,
    )
    pipeline = RAGPipeline(
        db,
        embedder=OpenRouterEmbedder(model=embed_model),
        summarizer=OpenRouterSummarizer(model=summary_model),
        embed_batch_size=MODEL_CONFIG.rag_embed_batch_size,
    )
    await pipeline.process(transcription_id)


class BaseTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, source: str, db) -> dict:
        pass


class YouTubeTranscriber(BaseTranscriber):
    def __get_video_id(self, url: str) -> str | None:
        return extract_video_id(url)

    async def transcribe(
        self,
        source: str,
        db,
        embed_model: str = MODEL_CONFIG.embedding_model,
        summary_model: str = MODEL_CONFIG.phase2_summary_model,
    ) -> dict:
        video_id = self.__get_video_id(source)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        existing = await db.fetchrow(
            f"""SELECT t.*
                FROM transcriptions t
                JOIN yt_videos v ON t.video_id = v.id
                WHERE {YOUTUBE_ID_SQL_EXPR} = $1 AND t.status = 'ready'
                ORDER BY t.created_at DESC
                LIMIT 1""",
            video_id,
        )
        if existing:
            chunk_count = await db.fetchval(
                "SELECT COUNT(*) FROM transcript_chunks WHERE transcription_id = $1::uuid",
                existing["id"],
            )
            if int(chunk_count or 0) == 0:
                await _run_rag_pipeline(
                    db,
                    str(existing["id"]),
                    embed_model,
                    summary_model,
                )
                logger.info(
                    "Re-indexed existing YouTube transcription %s",
                    existing["id"],
                )
                existing = await db.fetchrow(
                    "SELECT * FROM transcriptions WHERE id = $1::uuid",
                    existing["id"],
                )
            return dict(existing)

        transcript = YouTubeTranscriptApi().fetch(video_id)
        full_text = " ".join(entry.text for entry in transcript)
        segments = [
            {"start": e.start, "end": e.start + e.duration, "text": e.text}
            for e in transcript
        ]

        video = await resolve_or_create_yt_video(db, source)

        row = await db.fetchrow(
            "INSERT INTO transcriptions (video_id, full_text, segments, model_version, status) "
            "VALUES ($1, $2, $3::jsonb, $4, 'pending') RETURNING *",
            video.yt_video_id,
            full_text,
            json.dumps(segments),
            f"youtube-transcript-api+{embed_model}+{summary_model}",
        )

        await _run_rag_pipeline(db, str(row["id"]), embed_model, summary_model)
        logger.info("Indexed new YouTube transcription %s", row["id"])
        row = await db.fetchrow(
            "SELECT * FROM transcriptions WHERE id = $1::uuid",
            row["id"],
        )

        return dict(row)


class VideoFileTranscriber(BaseTranscriber):
    def __init__(self, model_name: str = "base") -> None:
        self.__model_name = model_name
        self.__model = whisper.load_model(model_name)

    @property
    def model(self):
        return self.__model

    async def transcribe(
        self, source: str, db, user_video_id: str = None
    ) -> dict:
        wav_path = await asyncio.to_thread(video_to_audio, source)
        try:
            result = await asyncio.to_thread(self.__model.transcribe, wav_path)
            full_text = result["text"]
            segments = [
                {"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in result["segments"]
            ]
            language = result["language"]

            row = await db.fetchrow(
                "INSERT INTO transcriptions "
                "(user_video_id, full_text, segments, language, model_version, status) "
                "VALUES ($1, $2, $3::jsonb, $4, $5, 'ready') RETURNING *",
                user_video_id,
                full_text,
                json.dumps(segments),
                language,
                f"whisper-{self.__model_name}",
            )
        finally:
            await asyncio.to_thread(delete_temporary_audio_file, wav_path)

        return dict(row)


class TranscriberFactory:
    _yt = YouTubeTranscriber()
    _video = VideoFileTranscriber()

    @classmethod
    def get_transcriber(cls, source: str) -> BaseTranscriber:
        if extract_video_id(source):
            return cls._yt
        return cls._video


async def transcribe_video_yt(
    url: str,
    db,
    embed_model: str = MODEL_CONFIG.embedding_model,
    summary_model: str = MODEL_CONFIG.phase2_summary_model,
) -> dict:
    return await TranscriberFactory._yt.transcribe(
        url,
        db,
        embed_model=embed_model,
        summary_model=summary_model,
    )


async def transcribe_uploaded_video(
    video_path: str, user_video_id: str, db, file_hash: str = ""
) -> dict:
    if file_hash:
        cached = await db.fetchrow(
            "SELECT t.* FROM transcriptions t "
            "JOIN user_videos uv ON t.user_video_id = uv.id "
            "WHERE uv.file_hash = $1 AND t.status = 'ready' "
            "ORDER BY t.created_at DESC LIMIT 1",
            file_hash,
        )
        if cached:
            row = await db.fetchrow(
                "INSERT INTO transcriptions "
                "(user_video_id, full_text, segments, language, model_version, status) "
                "VALUES ($1, $2, $3, $4, $5, 'ready') RETURNING *",
                user_video_id, cached["full_text"], cached["segments"],
                cached["language"], cached["model_version"],
            )
            return dict(row)

    transcriber = TranscriberFactory.get_transcriber(video_path)
    return await transcriber.transcribe(video_path, db, user_video_id)
