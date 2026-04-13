from fastapi import APIRouter, Depends
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/all")
async def get_all_history(
    current_user=Depends(get_current_user),
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
           WHERE ch.user_id = $1::uuid AND ch.role = 'user'
           ORDER BY ch.created_at DESC""",
        current_user["sub"],
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


@router.delete("/all")
async def clear_all_history(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    await db.execute(
        "DELETE FROM chat_history WHERE user_id = $1::uuid",
        current_user["sub"],
    )
    return {"deleted": True}


@router.get("/{video_id}")
async def get_chat_history(
    video_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    import uuid as _uuid
    def is_uuid(val):
        try:
            _uuid.UUID(val)
            return True
        except (ValueError, AttributeError):
            return False

    yt_uuid = await db.fetchval(
        "SELECT id FROM yt_videos WHERE source_url = $1",
        f"https://www.youtube.com/watch?v={video_id}",
    )
    if yt_uuid:
        rows = await db.fetch(
            """SELECT role, content FROM chat_history
               WHERE user_id = $1::uuid AND video_id = $2
               ORDER BY created_at ASC""",
            current_user["sub"], yt_uuid,
        )
    elif is_uuid(video_id):
        rows = await db.fetch(
            """SELECT role, content FROM chat_history
               WHERE user_id = $1::uuid AND user_video_id = $2::uuid
               ORDER BY created_at ASC""",
            current_user["sub"], video_id,
        )
    else:
        rows = []

    return [{"role": r["role"], "content": r["content"]} for r in rows]
