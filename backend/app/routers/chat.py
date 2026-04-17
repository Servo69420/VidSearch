import logging
import httpx
import uuid as _uuid
from pydantic import BaseModel
from app.config import settings
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_user
from app.database import get_db
from app.model_config import MODEL_CONFIG
from app.routers.context import search_video_context
from app.routers.video_player_tools import VIDEO_PLAYER_TOOLS
from app.youtube import normalize_youtube_ref, resolve_or_create_yt_video


# Model switches are centralized in app/model_config.py.
# Change chat, embedding, and phase-2 summary models there.
CHAT_MODEL = MODEL_CONFIG.chat_model
EMBEDDING_MODEL = MODEL_CONFIG.embedding_model
PHASE2_SUMMARY_MODEL = MODEL_CONFIG.phase2_summary_model
RETRIEVAL_TOP_K = MODEL_CONFIG.rag_retrieval_top_k


router = APIRouter()
logger = logging.getLogger(__name__)


class Chatrequest(BaseModel):
    video_id: str
    message: list[dict]


def is_uuid(val: str) -> bool:
    try:
        _uuid.UUID(val)
        return True
    except (ValueError, AttributeError):
        return False


def _format_seconds(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _grounding_message(chunks: list[dict]) -> str:
    lines = [
        "Grounding context from retrieved transcript chunks:",
        "Use this context first when answering video-content questions.",
        "If you call seek_video, only use timestamps present below.",
    ]
    last_topic: str | None = None
    for chunk in chunks:
        topic_summary = chunk.get("topic_summary")
        if topic_summary and topic_summary != last_topic:
            lines.append(f"Topic: {topic_summary}")
            last_topic = topic_summary
        lines.append(
            f"[{_format_seconds(chunk['start_s'])} - "
            f"{_format_seconds(chunk['end_s'])}] {chunk['text']}"
        )
    return "\n".join(lines)


@router.post("/ask")
async def ask(
    request: Chatrequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = current_user["sub"]
    if is_uuid(request.video_id):
        user_video_exists = await db.fetchval(
            """SELECT id
               FROM user_videos
               WHERE id = $1::uuid AND user_id = $2::uuid""",
            request.video_id,
            user_id,
        )
        if user_video_exists:
            video_id = None
            user_video_id = request.video_id
        else:
            yt_video_exists = await db.fetchval(
                "SELECT id FROM yt_videos WHERE id = $1::uuid",
                request.video_id,
            )
            if not yt_video_exists:
                raise HTTPException(status_code=404, detail="Video not found")
            video_id = request.video_id
            user_video_id = None
    else:
        yt_ref = normalize_youtube_ref(request.video_id)
        if not yt_ref:
            raise HTTPException(status_code=400, detail="Invalid video identifier")

        resolved = await resolve_or_create_yt_video(db, yt_ref.video_id)
        video_id = resolved.yt_video_id
        user_video_id = None

    user_message = next(
        (
            m.get("content")
            for m in reversed(request.message)
            if m.get("role") == "user" and isinstance(m.get("content"), str)
        ),
        None,
    )

    retrieved_chunks: list[dict] = []
    if user_message:
        try:
            retrieved_chunks = await search_video_context(
                request.video_id,
                user_message,
                db,
                embed_model=EMBEDDING_MODEL,
                top_k=RETRIEVAL_TOP_K,
            )
            logger.info(
                "Chat grounding retrieved %s chunks (video_id=%s, summary_model=%s)",
                len(retrieved_chunks),
                request.video_id,
                PHASE2_SUMMARY_MODEL,
            )
        except Exception:
            logger.exception(
                "Chat grounding failed, continuing without retrieval context"
            )

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

    if retrieved_chunks:
        openai_messages.append(
            {
                "role": "system",
                "content": _grounding_message(retrieved_chunks),
            }
        )

    for msg in request.message:
        role = msg.get("role")
        content = msg.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            openai_messages.append({"role": role, "content": content})

    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": CHAT_MODEL,
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

            can_save = True

            if can_save and user_message:
                await db.execute(
                    "INSERT INTO chat_history "
                    "(user_id, video_id, user_video_id, role, content) "
                    "VALUES ($1::uuid, $2::uuid, $3::uuid, 'user', $4)",
                    user_id, video_id, user_video_id, user_message,
                )

            msg = data["choices"][0]["message"]
            assistant_message = msg.get("content")
            if not assistant_message:
                tool_calls = msg.get("tool_calls") or []
                if tool_calls:
                    assistant_message = ", ".join(
                        f"*{tc['function']['name'].replace('_', ' ')}*"
                        for tc in tool_calls
                    )
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
