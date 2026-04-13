import uuid as _uuid
from typing import Any


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
        source_url = f"https://www.youtube.com/watch?v={video_id}"
        row = await db.fetchrow(
            """
            SELECT t.*
            FROM transcriptions t
            JOIN yt_videos v ON v.id = t.video_id
            WHERE v.source_url = $1
            ORDER BY t.created_at DESC
            LIMIT 1
            """,
            source_url,
        )

    return dict(row) if row else None
