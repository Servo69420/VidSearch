import httpx
from pydantic import BaseModel
from app.config import settings
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_user
from app.database import get_db
from app.routers.video_player_tools import VIDEO_PLAYER_TOOLS


router = APIRouter()


class Chatrequest(BaseModel):
    video_id: str
    message: list[dict]


@router.post("/ask")
async def ask(
    request: Chatrequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    openai_messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions "
                "about the content of the video. "
                "IMPORTANT: By default, respond with text. "
                "When explaining the video content, you can also use the "
                "following tools to control the video player together with "
                "the explanation (e.g. 'play the video', 'pause it', "
                "'mute', 'skip to 2:30'). "
                "For any other message — questions, greetings, "
                "conversation — respond with normal text and "
                "call tools to assist with the explanation."
            ),
        }
    ]
    for msg in request.message:
        if msg["role"] == "user":
            openai_messages.append({"role": "user", "content": msg["content"]})

    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": "google/gemini-2.5-flash-lite", #google/gemma-4-31b-it
                    "messages": openai_messages,
                    "tools": VIDEO_PLAYER_TOOLS,
                },
                timeout=60.0,
            )
            if result.status_code != 200:
                print(
                    f"Error: OpenRouter API returned status code "
                    f"{result.status_code} with response: {result.text}"
                )
                raise HTTPException(
                    status_code=502,
                    detail="Error from AI provider.",
                )
            data = result.json()

            import uuid as _uuid

            def is_uuid(val):
                try:
                    _uuid.UUID(val)
                    return True
                except (ValueError, AttributeError):
                    return False

            user_id = current_user["sub"]

            if is_uuid(request.video_id):
                video_id = None
                user_video_id = request.video_id
            else:
                # YouTube ID — upsert into yt_videos so we always have a UUID
                yt_uuid = await db.fetchval(
                    """INSERT INTO yt_videos (source_type, source_url)
                       VALUES ('youtube', $1)
                       ON CONFLICT (source_url)
                       DO UPDATE SET source_url = EXCLUDED.source_url
                       RETURNING id""",
                    f"https://www.youtube.com/watch?v={request.video_id}",
                )
                video_id = str(yt_uuid)
                user_video_id = None

            can_save = True

            user_message = next(
                (
                    m["content"] for m in reversed(request.message)
                    if m["role"] == "user"
                ),
                None,
            )
            if can_save and user_message:
                await db.execute(
                    "INSERT INTO chat_history "
                    "(user_id, video_id, user_video_id, role, content) "
                    "VALUES ($1::uuid, $2::uuid, $3::uuid, 'user', $4)",
                    user_id, video_id, user_video_id, user_message,
                )

            assistant_message = data["choices"][0]["message"].get("content")
            if can_save and assistant_message:
                await db.execute(
                    "INSERT INTO chat_history "
                    "(user_id, video_id, user_video_id, role, content) "
                    "VALUES ($1::uuid, $2::uuid, $3::uuid, 'assistant', $4)",
                    user_id, video_id, user_video_id, assistant_message,
                )
            return data
        except httpx.TimeoutException:
            print(
                "Error: The request to OpenRouter API timed out "
                "after 60 seconds."
            )
            raise HTTPException(
                status_code=504,
                detail="Request to AI provider timed out.",
            )
