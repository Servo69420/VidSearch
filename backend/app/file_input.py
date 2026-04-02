import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
MAX_SIZE = 500 * 1024 * 1024  # 500 MB

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported video format. Use mp4, webm, ogg, or mov.")

    ext = Path(file.filename).suffix or ".mp4"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / saved_name

    size = 0
    with open(dest, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_SIZE:
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large. Max 500 MB.")
            f.write(chunk)

    return {
        "filename": saved_name,
        "original_name": file.filename,
        "url": f"/uploads/{saved_name}",
    }