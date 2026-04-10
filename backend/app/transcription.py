# Transcription Logic
import whisper
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from app.video_to_audio import video_to_audio, delete_temporary_audio_file

model = whisper.load_model("base")

def _get_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed.query).get('v', [None])[0]
    elif parsed.hostname == 'youtu.be':
        return parsed.path.lstrip("/")
    return None

async def transcribe_video_yt(url: str, db) -> dict:
    video_id = _get_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    existing = await db.fetchrow(
        "SELECT t.* FROM transcriptions t JOIN yt_videos v ON t.video_id = v.id WHERE v.source_url = $1", url
    )
    if existing:
        return dict(existing)

    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(video_id)
    full_text = " ".join(entry.text for entry in transcript)
    segments = [{ "start": e.start, "end": e.start + e.duration, "text": e.text } for e in transcript]

    video = await db.fetchrow(
        "INSERT INTO yt_videos (source_type, source_url) VALUES ('youtube', $1) ON CONFLICT (source_url) DO UPDATE SET source_url = EXCLUDED.source_url RETURNING *", url
    )

    row = await db.fetchrow(
        "INSERT INTO transcriptions (video_id, full_text, segments) VALUES ($1, $2, $3::jsonb) RETURNING *",
        video["id"], full_text, __import__("json").dumps(segments)
    )

    return dict(row)

async def transcribe_uploaded_video(video_path: str, user_video_id: str, db) -> dict:
    wav_path = video_to_audio(video_path)

    try:
        result = model.transcribe(wav_path)
        full_text = result["text"]
        segments = [
            {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
            for seg in result["segments"]
        ]
        language = result["language"]

        row = await db.fetchrow(
            "INSERT INTO transcriptions (user_video_id, full_text, segments, language) VALUES ($1, $2, $3::jsonb, $4) RETURNING *",
            user_video_id, full_text, __import__("json").dumps(segments), language
        )
    finally:
        delete_temporary_audio_file(wav_path)
    
    return dict(row)
