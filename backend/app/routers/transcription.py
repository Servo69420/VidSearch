from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path

import uuid

from app.database import get_db
from app.routers.auth import get_current_user
from app.transcription import transcribe_video_yt, transcribe_uploaded_video

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

class YouTubeTranscriptionRequest(BaseModel):
    url: str

@router.post("/url")
async def transcribe_url(
    body: YouTubeTranscriptionRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        result = await transcribe_video_yt(body.url, db)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

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
    file_path.write_bytes(data)

    user_video = await db.fetchrow(
        "INSERT INTO user_videos (user_id, original_filename, file_path) VALUES ($1::uuid, $2, $3) RETURNING *",
        current_user["sub"], file.filename, str(file_path)
    )

    try:
        result = await transcribe_uploaded_video(str(file_path), user_video["id"], db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")