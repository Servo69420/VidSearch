import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class BaseFileUploader(ABC):
    @abstractmethod
    def validate(self, file: UploadFile) -> None:
        pass

    @abstractmethod
    async def save(self, file: UploadFile) -> Path:
        pass


class VideoFileUploader(BaseFileUploader):
    def __init__(
        self,
        upload_dir: Path,
        allowed_types: set[str],
        max_size: int,
    ) -> None:
        self.__upload_dir = upload_dir
        self.__allowed_types = allowed_types
        self.__max_size = max_size

    @property
    def upload_dir(self) -> Path:
        return self.__upload_dir

    def validate(self, file: UploadFile) -> None:
        if file.content_type not in self.__allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Unsupported video format. Use mp4, webm, ogg, or mov.",
            )

    async def save(self, file: UploadFile) -> Path:
        ext = Path(file.filename).suffix or ".mp4"
        dest = self.__upload_dir / f"{uuid.uuid4().hex}{ext}"
        size = 0
        with open(dest, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > self.__max_size:
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail="File too large. Max 500 MB.",
                    )
                f.write(chunk)
        return dest


_uploader = VideoFileUploader(
    upload_dir=UPLOAD_DIR,
    allowed_types={"video/mp4", "video/webm", "video/ogg", "video/quicktime"},
    max_size=500 * 1024 * 1024,
)
