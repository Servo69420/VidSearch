import asyncio
import base64
import logging
import os
import shutil
import subprocess
import sys
import tempfile

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_tool(name: str) -> str:
    # Explicit config override takes priority.
    if name == "ffmpeg" and settings.FFMPEG_PATH and os.path.isfile(settings.FFMPEG_PATH):
        return settings.FFMPEG_PATH
    exe = shutil.which(name) or shutil.which(f"{name}.exe")
    if exe:
        return exe
    conda_bin = os.path.join(sys.prefix, "Library", "bin", f"{name}.exe")
    if os.path.isfile(conda_bin):
        return conda_bin
    return name


def _subprocess_env() -> dict:
    env = os.environ.copy()
    conda_bin = os.path.join(sys.prefix, "Library", "bin")
    if conda_bin not in env.get("PATH", ""):
        env["PATH"] = conda_bin + os.pathsep + env.get("PATH", "")
    return env


def _run_sync(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        env=_subprocess_env(),
    )


class FrameCaptureRequest(BaseModel):
    video_id: str
    timestamp: float


@router.post("/capture-frame")
async def capture_frame(
    request: FrameCaptureRequest,
    current_user=Depends(get_current_user),
):
    if request.timestamp < 0:
        raise HTTPException(status_code=400, detail="Timestamp must be non-negative.")

    video_url = f"https://www.youtube.com/watch?v={request.video_id}"
    ytdlp_cmd = [sys.executable, "-m", "yt_dlp"]
    ffmpeg_path = _resolve_tool("ffmpeg")

    logger.warning(
        "capture-frame start video=%s ts=%s ffmpeg=%s sys.prefix=%s",
        request.video_id, request.timestamp, ffmpeg_path, sys.prefix,
    )

    ts = float(request.timestamp)
    tmp_dir = tempfile.mkdtemp(prefix="vidsearch_frame_")
    tmp_jpg_path = os.path.join(tmp_dir, "frame.jpg")
    try:
        # Step 1: ask yt-dlp for the raw stream URL — no ffmpeg needed.
        url_cmd = [
            *ytdlp_cmd,
            "-f", "best[height<=480][ext=mp4]/best[height<=480]/best[ext=mp4]/best",
            "--get-url",
            "--no-playlist",
            video_url,
        ]
        url_result = await asyncio.to_thread(_run_sync, url_cmd, 30)
        if url_result.returncode != 0:
            logger.error(
                "yt-dlp get-url failed code=%s stderr=%s",
                url_result.returncode,
                url_result.stderr.decode(errors="replace")[-600:],
            )
            raise HTTPException(status_code=502, detail="Failed to resolve video URL.")

        stream_url = url_result.stdout.decode(errors="replace").strip().splitlines()[0]
        if not stream_url:
            raise HTTPException(status_code=502, detail="yt-dlp returned no stream URL.")

        # Step 2: ffmpeg seeks in the stream and grabs one frame — no full download.
        ff_cmd = [
            ffmpeg_path,
            "-ss", str(ts),
            "-i", stream_url,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            tmp_jpg_path,
        ]
        ff_result = await asyncio.to_thread(_run_sync, ff_cmd, 60)
        if ff_result.returncode != 0 or not os.path.exists(tmp_jpg_path) or os.path.getsize(tmp_jpg_path) == 0:
            logger.error(
                "ffmpeg frame extract failed code=%s stderr=%s",
                ff_result.returncode,
                ff_result.stderr.decode(errors="replace")[-600:],
            )
            raise HTTPException(status_code=502, detail="ffmpeg failed to extract frame.")

        with open(tmp_jpg_path, "rb") as f:
            image_data = f.read()

        if not image_data:
            raise HTTPException(status_code=502, detail="Frame extraction produced no output.")

        return {"image_base64": base64.b64encode(image_data).decode()}

    except (asyncio.TimeoutError, subprocess.TimeoutExpired):
        raise HTTPException(status_code=504, detail="Frame capture timed out.")
    except FileNotFoundError:
        logger.exception("yt-dlp or ffmpeg not found")
        raise HTTPException(status_code=500, detail="yt-dlp or ffmpeg is not installed on the server.")
    except HTTPException:
        raise
    except Exception:
        logger.exception("frame capture failed")
        raise HTTPException(status_code=502, detail="Failed to capture frame.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
