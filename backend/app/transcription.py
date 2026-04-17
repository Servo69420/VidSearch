import asyncio
import json
from abc import ABC, abstractmethod
from urllib.parse import parse_qs, urlparse

import whisper
from youtube_transcript_api import YouTubeTranscriptApi

from app.video_to_audio import delete_temporary_audio_file, video_to_audio


class BaseTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, source: str, db) -> dict:
        pass


class YouTubeTranscriber(BaseTranscriber):
    def __get_video_id(self, url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.hostname in ["www.youtube.com", "youtube.com"]:
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.hostname == "youtu.be":
            return parsed.path.lstrip("/")
        return None

    async def transcribe(self, source: str, db) -> dict:
        video_id = self.__get_video_id(source)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        existing = await db.fetchrow(
            "SELECT t.* FROM transcriptions t "
            "JOIN yt_videos v ON t.video_id = v.id "
            "WHERE v.source_url = $1",
            source,
        )
        if existing:
            return dict(existing)

        transcript = YouTubeTranscriptApi().fetch(video_id)
        full_text = " ".join(entry.text for entry in transcript)
        segments = [
            {"start": e.start, "end": e.start + e.duration, "text": e.text}
            for e in transcript
        ]

        video = await db.fetchrow(
            "INSERT INTO yt_videos (source_type, source_url) VALUES ('youtube', $1) "
            "ON CONFLICT (source_url) DO UPDATE SET source_url = EXCLUDED.source_url "
            "RETURNING *",
            source,
        )

        row = await db.fetchrow(
            "INSERT INTO transcriptions (video_id, full_text, segments, status) "
            "VALUES ($1, $2, $3::jsonb, 'ready') RETURNING *",
            video["id"], full_text, json.dumps(segments),
        )

        return dict(row)


class VideoFileTranscriber(BaseTranscriber):
    def __init__(self, model_name: str = "base") -> None:
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
                "(user_video_id, full_text, segments, language, status) "
                "VALUES ($1, $2, $3::jsonb, $4, 'ready') RETURNING *",
                user_video_id,
                full_text,
                json.dumps(segments),
                language,
            )
        finally:
            await asyncio.to_thread(delete_temporary_audio_file, wav_path)

        return dict(row)


class TranscriberFactory:
    _yt = YouTubeTranscriber()
    _video = VideoFileTranscriber()

    @classmethod
    def get_transcriber(cls, source: str) -> BaseTranscriber:
        if "youtube.com" in source or "youtu.be" in source:
            return cls._yt
        return cls._video


async def transcribe_video_yt(url: str, db) -> dict:
    transcriber = TranscriberFactory.get_transcriber(url)
    return await transcriber.transcribe(url, db)


async def transcribe_uploaded_video(
    video_path: str, user_video_id: str, db
) -> dict:
    transcriber = TranscriberFactory.get_transcriber(video_path)
    return await transcriber.transcribe(video_path, db, user_video_id)
