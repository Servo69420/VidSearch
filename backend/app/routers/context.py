import uuid as _uuid
from typing import Any

from app.openrouter_embedder import OpenRouterEmbedder
from app.rag import RAGPipeline
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
            ORDER BY (status = 'ready') DESC, created_at DESC
            LIMIT 1
            """,
            video_id,
        )
        if row is None:
            row = await db.fetchrow(
                """
                SELECT *
                FROM transcriptions
                WHERE video_id = $1::uuid
                ORDER BY (status = 'ready') DESC, created_at DESC
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
            ORDER BY (t.status = 'ready') DESC, t.created_at DESC
            LIMIT 1
            """,
            ref.video_id,
        )

    return dict(row) if row else None


async def search_video_context(
    video_id: str,
    query: str,
    db,
    *,
    embed_model: str,
    top_k: int = 6,
) -> list[dict[str, Any]]:
    transcript = await get_transcript(video_id, db)
    if not transcript:
        return []
    if transcript.get("status") != "ready":
        return []

    pipeline = RAGPipeline(db, embedder=OpenRouterEmbedder(model=embed_model))
    hits = await pipeline.search(str(transcript["id"]), query, top_k=top_k)

    return [
        {
            "idx": h.idx,
            "start_s": h.start_s,
            "end_s": h.end_s,
            "text": h.text,
            "score": h.score,
        }
        for h in hits
    ]
