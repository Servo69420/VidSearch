from typing import Optional

from fastapi import APIRouter, File, Request, UploadFile

from app.database import get_pool
from app.file_input import _uploader
from app.models.auth_service import AuthService

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


@router.post("/upload_video")
async def upload_video(request: Request, file: UploadFile = File(...)):
    _uploader.validate(file)
    dest = await _uploader.save(file)

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
            pass

    return {
        "filename": dest.name,
        "original_name": file.filename,
        "url": f"/uploads/{dest.name}",
        "user_video_id": user_video_id,
    }
