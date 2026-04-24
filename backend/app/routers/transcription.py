import asyncio
import json
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path

import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.model_config import MODEL_CONFIG
from app.routers.context import get_transcript
from app.routers.chat import EMBEDDING_MODEL
from app.transcription import transcribe_video_yt, transcribe_uploaded_video
from app.youtube import extract_video_id

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

_TS_RE = re.compile(
    r'(?m)^[ \t]*(\d{1,2}:\d{2}(?::\d{2})?)[ \t]*[-–—|]?[ \t]*(.+?)[ \t]*$'
)


def _seconds_to_time(seconds: float) -> str:
    total = max(0, int(seconds))
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _time_to_seconds(t: str) -> int:
    parts = list(map(int, t.split(':')))
    return sum(p * 60 ** (len(parts) - 1 - i) for i, p in enumerate(parts))


def _parse_chapters_from_description(desc: str) -> list[dict]:
    chapters = []
    last_s = -1
    for m in _TS_RE.finditer(desc):
        s = _time_to_seconds(m.group(1))
        title = m.group(2).strip()
        if not title or s < last_s:
            continue
        chapters.append({"seconds": s, "time": m.group(1), "title": title})
        last_s = s
    if len(chapters) >= 2 and chapters[0]["seconds"] <= 10:
        return chapters
    return []


async def _fetch_youtube_chapters(video_id: str) -> list[dict]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            r = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
        if r.status_code != 200:
            return []
        m = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', r.text)
        if not m:
            return []
        desc = json.loads('"' + m.group(1) + '"')
        return _parse_chapters_from_description(desc)
    except Exception:
        return []


def _chunk_title(summary: str, keywords: list) -> str:
    if keywords:
        words = [k.strip().title() for k in keywords[:3] if k.strip()]
        if words:
            return " & ".join(words)
    if summary:
        sentence = summary.split('.')[0].strip()
        return sentence[:45] + ('…' if len(sentence) > 45 else '')
    return "Section"


class YouTubeTranscriptionRequest(BaseModel):
    url: str


@router.get("/status/{video_id:path}")
async def transcription_status(
    video_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    transcript = await get_transcript(video_id, db)
    if not transcript:
        return {"ready": False, "status": "missing", "transcription_id": None}

    status = transcript.get("status") or "pending"
    return {
        "ready": status == "ready",
        "status": status,
        "transcription_id": str(transcript["id"]),
    }


@router.post("/url")
async def transcribe_url(
    body: YouTubeTranscriptionRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        result = await transcribe_video_yt(
            body.url,
            db,
            embed_model=MODEL_CONFIG.embedding_model,
            summary_model=MODEL_CONFIG.phase2_summary_model,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Transcription failed: {str(e)}"
        )


@router.post("/upload")
async def transcribe_upload(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    allowed = ("video/mp4", "video/webm", "video/x-matroska", "video/quicktime")
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format. Allowed: mp4, webm, mkv, mov."
        )

    data = await file.read()
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    await asyncio.to_thread(file_path.write_bytes, data)

    user_video = await db.fetchrow(
        "INSERT INTO user_videos (user_id, file_name, file_path) "
        "VALUES ($1::uuid, $2, $3) RETURNING *",
        current_user["sub"], file.filename, str(file_path),
    )

    try:
        result = await transcribe_uploaded_video(
            str(file_path), user_video["id"], db
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Transcription failed: {str(e)}"
        )


@router.get("/segments/{video_id:path}")
async def get_segments(
    video_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    yt_id = extract_video_id(video_id)

    if yt_id:
        chapters = await _fetch_youtube_chapters(yt_id)
        if chapters:
            return {"segments": chapters, "source": "youtube_chapters"}

    transcript = await get_transcript(video_id, db)
    if not transcript or transcript.get("status") != "ready":
        return {"segments": [], "source": "none"}

    transcription_id = str(transcript["id"])
    rows = await db.fetch(
        """SELECT start_s, summary, keywords
           FROM transcript_chunks
           WHERE transcription_id = $1::uuid AND level = 2 AND summary IS NOT NULL
           ORDER BY start_s""",
        transcription_id,
    )

    segments = [
        {
            "seconds": float(row["start_s"]),
            "time": _seconds_to_time(row["start_s"]),
            "title": _chunk_title(row["summary"], list(row["keywords"] or [])),
        }
        for row in rows
    ]

    return {"segments": segments, "source": "ai_chunks"}
