import uuid as _uuid
from typing import Any

from app.youtube import YOUTUBE_ID_SQL_EXPR, normalize_youtube_ref


def _is_uuid(value: str) -> bool:
    try:
        _uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


async def get_transcript(video_id: str, db) -> dict[str, Any] | None:
    """Fetch the latest transcription row for a given video identifier.

    `video_id` accepts either:
      - a UUID string, interpreted as `user_videos.id`
      - a YouTube video ID (e.g. "aircAruvnKk"), resolved via `yt_videos.source_url`
    """
    if _is_uuid(video_id):
        row = await db.fetchrow(
            """
            SELECT *
            FROM transcriptions
            WHERE user_video_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            video_id,
        )
    else:
        ref = normalize_youtube_ref(video_id)
        if not ref:
            return None

        row = await db.fetchrow(
            f"""
            SELECT t.*
            FROM transcriptions t
            JOIN yt_videos v ON v.id = t.video_id
            WHERE {YOUTUBE_ID_SQL_EXPR} = $1
            ORDER BY t.created_at DESC
            LIMIT 1
            """,
            ref.video_id,
        )

    return dict(row) if row else None
