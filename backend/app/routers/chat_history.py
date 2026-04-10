from fastapi import APIRouter, Depends
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter()

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
