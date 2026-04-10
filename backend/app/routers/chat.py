import httpx
from pydantic import BaseModel
from app.config import settings
from fastapi import APIRouter, HTTPException, Depends
from app.routers.auth import get_current_user
from app.database import get_db


router = APIRouter()

VIDEO_PLAYER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "play_video",
            "description": (
                "Start or resume video playback. Use when the user asks "
                "to play, start, or resume the video."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pause_video",
            "description": (
                "Pause video playback. Use when the user asks "
                "to pause or stop the video."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seek_video",
            "description": (
                "Seek to a specific time in the video. Use when the user "
                "asks to jump to, go to, or skip to a specific timestamp. "
                "Convert timestamps like '2:30' to seconds (150)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "number",
                        "description": "Time in seconds to seek to.",
                    }
                },
                "required": ["seconds"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mute_video",
            "description": (
                "Mute the video. Use when the user asks to mute "
                "or silence the video."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unmute_video",
            "description": (
                "Unmute the video. Use when the user asks to unmute "
                "or turn the sound back on."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


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
                "When explaining the video content, you can also use the following tools to "
                "control the video player together with the explanation (e.g. 'play the video', "
                "'pause it', 'mute', 'skip to 2:30'). "
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
                    "model": "google/gemma-4-31b-it", #google/gemma-4-31b-it
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

            is_yt = await db.fetchval(
                "SELECT 1 FROM yt_videos WHERE id = $1::uuid", request.video_id
            )
            video_id = request.video_id if is_yt else None
            user_video_id = None if is_yt else request.video_id
            user_id = current_user["sub"]

            user_message = next(
                (m["content"] for m in reversed(request.message) if m["role"] == "user"),
                None,
            )
            if user_message:
                await db.execute(
                    """INSERT INTO chat_history (user_id, video_id, user_video_id, role, content)
                    VALUES ($1::uuid, $2::uuid, $3::uuid, 'user', $4)""",
                    user_id, video_id, user_video_id, user_message,
                )
            
            assistant_message = data["choices"][0]["message"].get("content")
            if assistant_message:
                await db.execute(
                    """INSERT INTO chat_history (user_id, video_id, user_video_id, role, content)
                    VALUES ($1::uuid, $2::uuid, $3::uuid, 'assistant', $4)""",
                    user_id, video_id, user_video_id, assistant_message,
                )
        except httpx.TimeoutException:
            print(
                "Error: The request to OpenRouter API timed out "
                "after 60 seconds."
            )
            raise HTTPException(
                status_code=504,
                detail="Request to AI provider timed out.",
            )
