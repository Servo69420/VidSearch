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

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_tool(name: str) -> str:
    """Find the absolute path to an executable, or fall back to the bare name."""
    exe = shutil.which(name) or shutil.which(f"{name}.exe")
    return exe or name


def _run_sync(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
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

    logger.info(
        "capture-frame start video=%s ts=%s ffmpeg=%s",
        request.video_id, request.timestamp, ffmpeg_path,
    )

    ts = float(request.timestamp)
    clip_start = max(0.0, ts - 0.5)
    clip_end = ts + 1.5

    tmp_dir = tempfile.mkdtemp(prefix="vidsearch_frame_")
    output_template = os.path.join(tmp_dir, "clip.%(ext)s")
    tmp_jpg_path = os.path.join(tmp_dir, "frame.jpg")
    try:
        # Step 1: download only the tiny time window around the target timestamp.
        dl_cmd = [
            *ytdlp_cmd,
            "-f", "best[ext=mp4]/best",
            "--download-sections", f"*{clip_start}-{clip_end}",
            "--force-keyframes-at-cuts",
            "--ffmpeg-location", ffmpeg_path,
            "-o", output_template,
            "--no-playlist",
            "--no-warnings",
            video_url,
        ]
        result = await asyncio.to_thread(_run_sync, dl_cmd, 90)

        # Find whatever file yt-dlp actually produced in the temp dir.
        produced = [
            os.path.join(tmp_dir, f)
            for f in os.listdir(tmp_dir)
            if f.startswith("clip.") and os.path.getsize(os.path.join(tmp_dir, f)) > 0
        ]

        if result.returncode != 0 or not produced:
            logger.error(
                "yt-dlp download-sections failed code=%s files=%s stdout=%s stderr=%s",
                result.returncode,
                os.listdir(tmp_dir),
                result.stdout.decode(errors="replace")[-400:],
                result.stderr.decode(errors="replace")[-800:],
            )
            raise HTTPException(status_code=502, detail="Failed to fetch video clip.")

        clip_path = produced[0]
        logger.info("capture-frame downloaded clip=%s size=%s", clip_path, os.path.getsize(clip_path))

        # Step 2: extract a single frame from the tiny local clip.
        seek_within_clip = ts - clip_start
        ff_cmd = [
            ffmpeg_path,
            "-ss", str(seek_within_clip),
            "-i", clip_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            tmp_jpg_path,
        ]
        result = await asyncio.to_thread(_run_sync, ff_cmd, 30)
        if result.returncode != 0 or not os.path.exists(tmp_jpg_path) or os.path.getsize(tmp_jpg_path) == 0:
            logger.error(
                "ffmpeg exited %s stderr=%s",
                result.returncode, result.stderr.decode(errors="replace")[-500:],
            )
            # Fallback: try without the seek — maybe the clip is too short.
            ff_cmd_fallback = [
                ffmpeg_path, "-i", clip_path, "-vframes", "1", "-q:v", "2", "-y", tmp_jpg_path,
            ]
            result = await asyncio.to_thread(_run_sync, ff_cmd_fallback, 30)
            if result.returncode != 0 or not os.path.exists(tmp_jpg_path) or os.path.getsize(tmp_jpg_path) == 0:
                logger.error(
                    "ffmpeg fallback exited %s stderr=%s",
                    result.returncode, result.stderr.decode(errors="replace")[-500:],
                )
                raise HTTPException(status_code=502, detail="ffmpeg failed. See server logs.")

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
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except OSError:
            pass
