from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }