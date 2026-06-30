
# Run tests: conda run -n VidSearchpy11 python -m unittest discover -s tests -v
# Run tests: conda run -n VidSearchpy12 python -m unittest discover -s tests -v

import os
import sys

# Ensure the conda env's binaries (ffmpeg, etc.) are visible to subprocesses.
_conda_bin = os.path.join(sys.prefix, "Library", "bin")
if _conda_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _conda_bin + os.pathsep + os.environ.get("PATH", "")

from contextlib import asynccontextmanager  # noqa: E402
from pathlib import Path  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from app.routers import chat, chat_history, files, frame_capture  # noqa: E402
from app.database import connect, disconnect  # noqa: E402
from app.routers import transcription  # noqa: E402


UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()


app = FastAPI(title="VidSearch API", version="0.1.0", lifespan=lifespan)
app.include_router(files.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.include_router(
    chat_history.router, prefix="/chat-history", tags=["chat-history"]
)


@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(
    transcription.router, prefix="/transcription", tags=["transcription"]
)
app.include_router(frame_capture.router, tags=["frame-capture"])
