import json
import logging
import httpx
import uuid as _uuid
from pydantic import BaseModel
from app.config import settings
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_user
from app.database import get_db
from app.routers.context import get_transcript, search_video_context
from app.routers.video_player_tools import VIDEO_PLAYER_TOOLS
from app.youtube import normalize_youtube_ref, resolve_or_create_yt_video
from app.model_config import MODEL_CONFIG


CHAT_MODEL = MODEL_CONFIG.chat_model
VISION_MODEL = MODEL_CONFIG.vision_model
EMBEDDING_MODEL = MODEL_CONFIG.embedding_model
PHASE2_SUMMARY_MODEL = MODEL_CONFIG.phase2_summary_model
RETRIEVAL_TOP_K = MODEL_CONFIG.rag_retrieval_top_k

OPENROUTER_CHAT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TIMEOUT_S = 60.0

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about the content "
    "of the video in simple and playfull manner to educate the end user. "
    "Every assistant turn MUST include a natural-language answer in the "
    "content field. When a player action is also appropriate (play, pause, "
    "mute, unmute, seek to a timestamp), emit one or more tool_calls "
    "alongside the answer. Never reply with tool_calls and empty content."
    "The end user might also attach an image of the current video scene using a trigger button, incorparate it in your answer if relevant and if you understand the image content. "
)


router = APIRouter()
logger = logging.getLogger(__name__)


class Chatrequest(BaseModel):
    video_id: str
    message: list[dict]
    frame_base64: str | None = None


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
        "Prefer timestamps that appear below when calling seek_video.",
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


async def _call_openrouter(
    messages: list[dict],
    *,
    tool_choice: str = "auto",
    model: str | None = None,
) -> dict:
    body: dict = {
        "model": model or CHAT_MODEL,
        "messages": messages,
    }
    if tool_choice != "none":
        body["tools"] = VIDEO_PLAYER_TOOLS
        body["tool_choice"] = tool_choice
    async with httpx.AsyncClient() as client:
        result = await client.post(
            OPENROUTER_CHAT_ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "content-type": "application/json",
            },
            json=body,
            timeout=OPENROUTER_TIMEOUT_S,
        )
    if result.status_code != 200:
        logger.error(
            "OpenRouter returned status %s body=%s",
            result.status_code,
            result.text,
        )
        raise HTTPException(status_code=502, detail="Error from AI provider.")
    return result.json()


def _tool_call_fallback_text(tool_calls: list[dict]) -> str:
    return ", ".join(
        f"*{tc['function']['name'].replace('_', ' ')}*" for tc in tool_calls
    )


def _build_tool_result_turns(tool_calls: list[dict], round1_content: str) -> list[dict]:
    turns: list[dict] = [
        {
            "role": "assistant",
            "content": round1_content if round1_content else None,
            "tool_calls": tool_calls,
        }
    ]
    for tc in tool_calls:
        turns.append(
            {
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": json.dumps({"status": "dispatched"}),
            }
        )
    return turns


async def _run_chat_loop(
    openai_messages: list[dict],
    *,
    model: str | None = None,
) -> tuple[str, list[dict]]:
    data_1 = await _call_openrouter(openai_messages, model=model)
    msg_1 = data_1["choices"][0]["message"]
    round1_content = msg_1.get("content") or ""
    round1_tool_calls = msg_1.get("tool_calls") or []

    final_content = round1_content
    final_tool_calls = round1_tool_calls

    if round1_tool_calls:
        logger.info(
            "Chat tool_calls in round 1 (count=%s); running follow-up for explanation",
            len(round1_tool_calls),
        )
        followup_messages = openai_messages + _build_tool_result_turns(
            round1_tool_calls, round1_content
        )
        try:
            data_2 = await _call_openrouter(
                followup_messages, tool_choice="none", model=model
            )
            msg_2 = data_2["choices"][0]["message"]
            round2_content = msg_2.get("content") or ""
            logger.info(
                "Chat round-2 response keys=%s content_len=%s",
                sorted(msg_2.keys()),
                len(round2_content),
            )
            if round2_content:
                final_content = round2_content
        except (HTTPException, httpx.TimeoutException):
            logger.exception(
                "Follow-up OpenRouter call failed; keeping round-1 content"
            )

    if not final_content and final_tool_calls:
        final_content = _tool_call_fallback_text(final_tool_calls)

    return final_content, final_tool_calls


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

    transcript = await get_transcript(request.video_id, db)
    if not transcript:
        raise HTTPException(
            status_code=409,
            detail="Transcription is not ready yet.",
        )
    if transcript.get("status") != "ready":
        raise HTTPException(
            status_code=409,
            detail=f"Transcription is {transcript.get('status', 'pending')}.",
        )

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

    openai_messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if retrieved_chunks:
        openai_messages.append(
            {
                "role": "system",
                "content": _grounding_message(retrieved_chunks),
            }
        )

    valid_msgs = [
        msg for msg in request.message
        if msg.get("role") in {"user", "assistant"} and isinstance(msg.get("content"), str)
    ]

    for i, msg in enumerate(valid_msgs):
        is_last_user = msg["role"] == "user" and i == len(valid_msgs) - 1
        if is_last_user and request.frame_base64:
            openai_messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": msg["content"]},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{request.frame_base64}"
                        },
                    },
                ],
            })
        else:
            openai_messages.append({"role": msg["role"], "content": msg["content"]})

    active_model = VISION_MODEL if request.frame_base64 else None

    try:
        final_content, final_tool_calls = await _run_chat_loop(
            openai_messages, model=active_model
        )
    except httpx.TimeoutException:
        logger.error("OpenRouter chat request timed out")
        raise HTTPException(
            status_code=504,
            detail="Request to AI provider timed out.",
        )

    envelope = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": final_content,
                    "tool_calls": final_tool_calls,
                }
            }
        ]
    }

    if user_message:
        await db.execute(
            "INSERT INTO chat_history "
            "(user_id, video_id, user_video_id, role, content) "
            "VALUES ($1::uuid, $2::uuid, $3::uuid, 'user', $4)",
            user_id,
            video_id,
            user_video_id,
            user_message,
        )

    if final_content:
        await db.execute(
            "INSERT INTO chat_history "
            "(user_id, video_id, user_video_id, role, content) "
            "VALUES ($1::uuid, $2::uuid, $3::uuid, 'assistant', $4)",
            user_id,
            video_id,
            user_video_id,
            final_content,
        )

    return envelope
