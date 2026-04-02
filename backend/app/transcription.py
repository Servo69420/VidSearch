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
        "SELECT t.* FROM transciptions AS t 
        JOIN videos AS v ON t.video_id = v.id 
        WHERE v.source_url = $1", url
    )
    if existing:
        return dict(existing)