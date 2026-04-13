import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.database import get_pool
from app.models.auth_service import AuthService

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
MAX_SIZE = 500 * 1024 * 1024  # 500 MB

router = APIRouter(prefix="/files", tags=["files"])
_auth_service = AuthService()


async def _optional_user_id(request: Request) -> Optional[str]:
    """Return the user UUID string if a valid Bearer token is present, else None."""
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


@router.post("/upload_video")
async def upload_video(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format. Use mp4, webm, ogg, or mov.")

    ext = Path(file.filename).suffix or ".mp4"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / saved_name

    size = 0
    with open(dest, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_SIZE:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Max 500 MB.")
            f.write(chunk)

    user_video_id = None
    user_id = await _optional_user_id(request)
    if user_id:
        try:
            async with get_pool().acquire() as db:
                row = await db.fetchrow(
                    """INSERT INTO user_videos (user_id, file_name, file_path)
                       VALUES ($1::uuid, $2, $3) RETURNING id""",
                    user_id, file.filename, str(dest),
                )
                user_video_id = str(row["id"])
        except Exception:
            pass  # non-fatal — video is still uploaded

    return {
        "filename": saved_name,
        "original_name": file.filename,
        "url": f"/uploads/{saved_name}",
        "user_video_id": user_video_id,
    }
