from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.youtube import YOUTUBE_ID_SQL_EXPR, normalize_youtube_ref
import uuid as _uuid

router = APIRouter()


@router.get("/all")
async def get_all_history(
    db=Depends(get_db),
):
    rows = await db.fetch(
        """SELECT
               ch.id,
               ch.content,
               ch.created_at,
               ch.video_id,
               ch.user_video_id,
               yv.source_url AS yt_source_url,
               uv.file_path AS uv_file_path,
               COALESCE(
                   NULLIF(yv.title, ''),
                   yv.source_url,
                   uv.file_name,
                   'Unknown Video'
               ) AS video_title
           FROM chat_history ch
           LEFT JOIN yt_videos yv ON ch.video_id = yv.id
           LEFT JOIN user_videos uv ON ch.user_video_id = uv.id
           WHERE ch.role = 'user'
           ORDER BY ch.created_at DESC""",
    )
    return [
        {
            "id": str(r["id"]),
            "content": r["content"],
            "created_at": r["created_at"].isoformat(),
            "video_title": r["video_title"],
            "video_id": str(r["video_id"]) if r["video_id"] else None,
            "user_video_id": str(r["user_video_id"]) if r["user_video_id"] else None,
            "yt_source_url": r["yt_source_url"],
            "uv_file_path": r["uv_file_path"],
        }
        for r in rows
    ]


@router.get("/videos")
async def get_history_videos(
    db=Depends(get_db),
):
    from pathlib import Path as PyPath

    rows = await db.fetch(
        """SELECT
               ch.video_id,
               ch.user_video_id,
               COALESCE(
                   NULLIF(yv.title, ''),
                   yv.source_url,
                   uv.file_name,
                   'Unknown Video'
               ) AS video_title,
               MAX(ch.created_at) AS last_message_at,
               COUNT(*) FILTER (WHERE ch.role = 'user') AS message_count,
               yv.source_url AS yt_source_url,
               uv.file_name AS uv_file_name,
               uv.file_path AS uv_file_path
           FROM chat_history ch
           LEFT JOIN yt_videos yv ON ch.video_id = yv.id
           LEFT JOIN user_videos uv ON ch.user_video_id = uv.id
           GROUP BY ch.video_id, ch.user_video_id,
                     yv.title, yv.source_url, uv.file_name, uv.file_path
           ORDER BY last_message_at DESC""",
    )
    result = []
    for r in rows:
        video_url = None
        if r["uv_file_path"]:
            video_url = f"/uploads/{PyPath(r['uv_file_path']).name}"
        result.append({
            "video_id": str(r["video_id"]) if r["video_id"] else None,
            "user_video_id": str(r["user_video_id"]) if r["user_video_id"] else None,
            "video_title": r["video_title"],
            "last_message_at": r["last_message_at"].isoformat(),
            "message_count": r["message_count"],
            "yt_source_url": r["yt_source_url"],
            "uv_file_name": r["uv_file_name"],
            "video_url": video_url,
        })
    return result


@router.delete("/all")
async def clear_all_history(
    db=Depends(get_db),
):
    await db.execute("DELETE FROM chat_history")
    return {"deleted": True}


@router.delete("/video/{video_id}")
async def delete_video_history(
    video_id: str,
    db=Depends(get_db),
):
    yt_ref = normalize_youtube_ref(video_id)
    if yt_ref:
        await db.execute(
            f"""DELETE FROM chat_history
                WHERE video_id IN (
                    SELECT id FROM yt_videos WHERE {YOUTUBE_ID_SQL_EXPR} = $1
                )""",
            yt_ref.video_id,
        )
        return {"deleted": True}

    try:
        vid = _uuid.UUID(video_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid video ID")

    yt_row = await db.fetchrow(
        f"SELECT {YOUTUBE_ID_SQL_EXPR} AS yt_video_id FROM yt_videos WHERE id = $1::uuid",
        vid,
    )

    if yt_row and yt_row["yt_video_id"]:
        await db.execute(
            f"""DELETE FROM chat_history
                WHERE video_id IN (
                    SELECT id FROM yt_videos WHERE {YOUTUBE_ID_SQL_EXPR} = $1
                )""",
            yt_row["yt_video_id"],
        )
    else:
        await db.execute(
            """DELETE FROM chat_history
               WHERE video_id = $1::uuid OR user_video_id = $1::uuid""",
            vid,
        )
    return {"deleted": True}


@router.get("/{video_id}")
async def get_chat_history(
    video_id: str,
    db=Depends(get_db),
):
    def is_uuid(val):
        try:
            _uuid.UUID(val)
            return True
        except (ValueError, AttributeError):
            return False

    yt_ref = normalize_youtube_ref(video_id)
    if yt_ref:
        rows = await db.fetch(
            f"""SELECT ch.role, ch.content
                FROM chat_history ch
                JOIN yt_videos yv ON yv.id = ch.video_id
                WHERE {YOUTUBE_ID_SQL_EXPR} = $1
                ORDER BY ch.created_at ASC""",
            yt_ref.video_id,
        )
    elif is_uuid(video_id):
        rows = await db.fetch(
            """SELECT role, content FROM chat_history
               WHERE video_id = $1::uuid OR user_video_id = $1::uuid
               ORDER BY created_at ASC""",
            video_id,
        )
    else:
        rows = []

    return [{"role": r["role"], "content": r["content"]} for r in rows]
