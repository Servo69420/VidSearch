import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings

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
async def ask(request: Chatrequest):
    openai_messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions "
                "about the content of the video. "
                "IMPORTANT: By default, respond with text. "
                "ONLY use a tool when the user EXPLICITLY asks to "
                "control the video player (e.g. 'play the video', "
                "'pause it', 'mute', 'skip to 2:30'). "
                "For any other message — questions, greetings, "
                "conversation — respond with normal text and "
                "do NOT call any tool."
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
                    "model": "google/gemini-2.5-flash",
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
            return result.json()
        except httpx.TimeoutException:
            print(
                "Error: The request to OpenRouter API timed out "
                "after 60 seconds."
            )
            raise HTTPException(
                status_code=504,
                detail="Request to AI provider timed out.",
            )
