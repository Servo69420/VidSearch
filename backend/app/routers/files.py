import traceback
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.database import get_db, get_pool
from app.file_input import _uploader
from app.models.auth_service import AuthService
from app.transcription import transcribe_uploaded_video

router = APIRouter(prefix="/files", tags=["files"])
_auth_service = AuthService()


async def _optional_user_id(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        async with get_pool().acquire() as db:
            payload = await _auth_service.get_current_user(token, db)
            return payload["sub"]
    except Exception:
        return None


async def _run_transcription(file_path: str, user_video_id: str, file_hash: str) -> None:
    try:
        async with get_pool().acquire() as db:
            await transcribe_uploaded_video(file_path, user_video_id, db, file_hash=file_hash)
    except Exception:
        traceback.print_exc()


@router.post("/upload_video")
async def upload_video(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    _uploader.validate(file)
    dest, file_hash = await _uploader.save(file)

    user_video_id = None
    user_id = await _optional_user_id(request)
    if user_id:
        try:
            async with get_pool().acquire() as db:
                row = await db.fetchrow(
                    """INSERT INTO user_videos (user_id, file_name, file_path, file_hash)
                       VALUES ($1::uuid, $2, $3, $4) RETURNING id""",
                    user_id, file.filename, str(dest), file_hash,
                )
                user_video_id = str(row["id"])
        except Exception:
            traceback.print_exc()

    if user_video_id:
        background_tasks.add_task(_run_transcription, str(dest), user_video_id, file_hash)

    video_url = (
        f"/files/video/{user_video_id}" if user_video_id
        else f"/uploads/{dest.name}"
    )
    return {
        "filename": dest.name,
        "original_name": file.filename,
        "url": video_url,
        "user_video_id": user_video_id,
    }


@router.get("/video/{user_video_id}")
async def serve_user_video(
    user_video_id: str,
    db=Depends(get_db),
):
    row = await db.fetchrow(
        "SELECT file_path FROM user_videos WHERE id = $1::uuid",
        user_video_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Video not found.")
    file_path = Path(row["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file missing from disk.")
    return FileResponse(str(file_path), media_type="video/mp4")
