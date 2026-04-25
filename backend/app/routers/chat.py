import json
import logging
import re
import httpx
import uuid as _uuid
from pydantic import BaseModel
from app.config import settings
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_user
from app.database import get_db
from app.routers.context import get_transcript, search_video_context, fetch_chunks_at_time
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
    "alongside the answer. Never reply with tool_calls and empty content. "
    "IMPORTANT: When the user asks what is happening NOW or CURRENTLY (e.g. "
    "'what does he say now?', 'what is presented now?'), you already have "
    "the current position context in the grounding — answer from it directly "
    "WITHOUT calling seek_video. Only call seek_video when the user "
    "explicitly asks to jump to a DIFFERENT part of the video. "
    "Do NOT write tool calls as text in the content field (no "
    "`ToolCall(...)`, no JSON like `[{\"tool_call_id\": ...}]`) — the "
    "structured `tool_calls` field is the only place the UI reads them. "
    "Format any mathematical notation using LaTeX inside `$...$` for inline "
    "math (e.g. `$x^3$`, `$\\int_0^{10} f(x)\\,dx$`) and `$$...$$` for "
    "display math, so the UI renders proper superscripts and symbols. "
    "The end user might also attach an image of the current video scene using a trigger button, "
    "incorporate it in your answer if relevant and if you understand the image content. "
    "The end user might also attach a text file — its full content will appear in a system message. "
    "Read and analyse the text file content carefully and use it to answer the user's question. "
)


router = APIRouter()
logger = logging.getLogger(__name__)


class Chatrequest(BaseModel):
    video_id: str
    message: list[dict]
    frame_base64: str | None = None
    current_time_s: float | None = None
    txt_context: str | None = None


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


_TOOLCALL_LITERAL_RE = re.compile(
    r"\[?\s*ToolCall\s*\([^\[\]]*?\)\s*\]?", re.IGNORECASE
)

_TOOLCALL_JSON_RE = re.compile(
    r"""\.?\s*\[?\s*\{\s*["']tool_call_id["'][\s\S]*?(?:\}\s*\]|\}|$)""",
)

# Gemma / mistral native tool-call tags: <tool_call>...</tool_call>,
# <|tool_call|>...</|tool_call|>, or the mixed <|tool_call>...</tool_call|>
_GEMMA_TOOLCALL_RE = re.compile(
    r"(?:<\|tool_call\|?>|<tool_call>)[\s\S]*?(?:</\|?tool_call\|?>|<tool_call\|>)",
    re.IGNORECASE,
)


def _parse_gemma_tool_calls(text: str) -> tuple[str, list[dict]]:
    """Extract Gemma-style inline tool calls; return (cleaned_text, tool_calls)."""
    extracted: list[dict] = []

    def _replacer(m: re.Match) -> str:
        inner = m.group(0)
        json_match = re.search(r"\{[\s\S]*\}", inner)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                name = parsed.get("name") or parsed.get("function")
                args = parsed.get("arguments") or parsed.get("parameters") or {}
                if name:
                    extracted.append({
                        "id": f"gemma_{len(extracted)}",
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps(args),
                        },
                    })
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        return ""

    cleaned = _GEMMA_TOOLCALL_RE.sub(_replacer, text).strip()
    return cleaned, extracted


def _strip_tool_call_literals(text: str) -> str:
    if not text:
        return text
    cleaned = _TOOLCALL_LITERAL_RE.sub("", text)
    cleaned = _TOOLCALL_JSON_RE.sub("", cleaned)
    cleaned, _ = _parse_gemma_tool_calls(cleaned)
    return cleaned.strip()


def _tool_call_fallback_text(tool_calls: list[dict]) -> str:
    return ", ".join(
        f"*{tc['function']['name'].replace('_', ' ')}*" for tc in tool_calls
    )


def _build_followup_turns(tool_calls: list[dict], round1_content: str) -> list[dict]:
    assistant_content = round1_content or (
        "I've initiated the video action. Now let me answer your question."
    )
    return [
        {"role": "assistant", "content": assistant_content},
        {"role": "user", "content": "Please give a brief natural-language answer to my question."},
    ]


async def _run_chat_loop(
    openai_messages: list[dict],
    *,
    model: str | None = None,
) -> tuple[str, list[dict]]:
    data_1 = await _call_openrouter(openai_messages, model=model)
    msg_1 = data_1["choices"][0]["message"]
    round1_content = msg_1.get("content") or ""
    round1_tool_calls = msg_1.get("tool_calls") or []

    # Gemma/mistral models embed tool calls as text rather than structured fields.
    # Extract them so round 2 still runs and the user gets a real answer.
    if not round1_tool_calls and round1_content:
        round1_content, gemma_calls = _parse_gemma_tool_calls(round1_content)
        if gemma_calls:
            round1_tool_calls = gemma_calls
            logger.info("Extracted %s Gemma-format tool call(s) from content", len(gemma_calls))

    final_content = round1_content
    final_tool_calls = round1_tool_calls

    if round1_tool_calls:
        logger.info(
            "Chat tool_calls in round 1 (count=%s); running follow-up for explanation",
            len(round1_tool_calls),
        )
        followup_messages = openai_messages + _build_followup_turns(
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

    final_content = _strip_tool_call_literals(final_content)

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

    if request.current_time_s is not None:
        current_chunks: list[dict] = []
        try:
            current_chunks = await fetch_chunks_at_time(
                request.video_id, request.current_time_s, db
            )
        except Exception:
            logger.exception("fetch_chunks_at_time failed")

        if current_chunks:
            lines = [
                f"Transcript at the user's current playback position "
                f"({_format_seconds(request.current_time_s)}) — this is what is being said RIGHT NOW:",
            ]
            for c in current_chunks:
                lines.append(
                    f"[{_format_seconds(c['start_s'])} - {_format_seconds(c['end_s'])}] {c['text']}"
                )
            openai_messages.append({"role": "system", "content": "\n".join(lines)})
        else:
            openai_messages.append({
                "role": "system",
                "content": (
                    f"The user is currently at {_format_seconds(request.current_time_s)} "
                    f"({request.current_time_s:.1f}s) in the video."
                ),
            })

    if retrieved_chunks:
        openai_messages.append(
            {
                "role": "system",
                "content": _grounding_message(retrieved_chunks),
            }
        )

    if request.txt_context:
        openai_messages.append({
            "role": "system",
            "content": (
                "The user has attached a text file. Read and analyse its full content carefully "
                "to answer their question.\n\n"
                f"--- ATTACHED TEXT FILE ---\n{request.txt_context}\n--- END OF FILE ---"
            ),
        })

    valid_msgs = [
        msg for msg in request.message
        if msg.get("role") in {"user", "assistant"} and isinstance(msg.get("content"), str)
    ]

    for i, msg in enumerate(valid_msgs):
        is_last_user = msg["role"] == "user" and i == len(valid_msgs) - 1
        msg_content = msg["content"]
        if is_last_user and request.txt_context:
            msg_content = (
                f"<attached_file>\n{request.txt_context}\n</attached_file>\n\n"
                + msg_content
            )
        if is_last_user and request.frame_base64:
            openai_messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": msg_content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{request.frame_base64}"
                        },
                    },
                ],
            })
        else:
            openai_messages.append({"role": msg["role"], "content": msg_content})

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
