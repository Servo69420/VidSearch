import traceback
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.database import get_db, get_pool
from app.file_input import _uploader
from app.transcription import transcribe_uploaded_video

router = APIRouter(prefix="/files", tags=["files"])


async def _run_transcription(file_path: str, user_video_id: str, file_hash: str) -> None:
    try:
        async with get_pool().acquire() as db:
            await transcribe_uploaded_video(file_path, user_video_id, db, file_hash=file_hash)
    except Exception:
        traceback.print_exc()


@router.post("/upload_video")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    _uploader.validate(file)
    dest, file_hash = await _uploader.save(file)

    try:
        async with get_pool().acquire() as db:
            row = await db.fetchrow(
                """INSERT INTO user_videos (file_name, file_path, file_hash)
                   VALUES ($1, $2, $3) RETURNING id""",
                file.filename, str(dest), file_hash,
            )
            user_video_id = str(row["id"])
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to store uploaded video.")

    background_tasks.add_task(_run_transcription, str(dest), user_video_id, file_hash)

    video_url = f"/files/video/{user_video_id}"
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
