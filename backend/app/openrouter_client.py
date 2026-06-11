"""Shared OpenRouter chat-completions client and content helpers.

Extracted from ``app.routers.chat`` so that other modules (e.g.
``app.visualization``) can reuse the HTTP call and the content-cleaning
helpers without importing the chat router — which would create a circular
import (chat imports the visualization generator, the generator needs the
client). ``chat`` re-imports these names so existing references and tests
(``chat_module._call_openrouter`` / ``._strip_reasoning_tokens`` / etc.)
keep working unchanged.
"""

import json
import logging
import re

import httpx
from fastapi import HTTPException

from app.config import settings
from app.model_config import MODEL_CONFIG
from app.routers.video_player_tools import VIDEO_PLAYER_TOOLS


logger = logging.getLogger(__name__)

OPENROUTER_CHAT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_TIMEOUT_S = MODEL_CONFIG.openrouter_timeout_s


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "content-type": "application/json",
    }


async def _call_openrouter(
    messages: list[dict],
    *,
    tool_choice: str = "auto",
    model: str | None = None,
    max_tokens: int | None = None,
    stream: bool = False,
) -> dict:
    body: dict = {
        "model": model or MODEL_CONFIG.chat_model,
        "messages": messages,
    }
    if tool_choice != "none":
        body["tools"] = VIDEO_PLAYER_TOOLS
        body["tool_choice"] = tool_choice
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if stream:
        body["stream"] = True
        return await _call_openrouter_streaming(body)
    async with httpx.AsyncClient() as client:
        result = await client.post(
            OPENROUTER_CHAT_ENDPOINT,
            headers=_auth_headers(),
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
    # For long non-streaming generations OpenRouter keeps the connection
    # alive by padding the 200 body with whitespace until the payload is
    # ready. If the upstream provider dies mid-generation, the body ends
    # up whitespace-only (or otherwise non-JSON) — surface that as a 502
    # instead of an unhandled JSONDecodeError.
    try:
        return result.json()
    except json.JSONDecodeError:
        text = result.text
        logger.error(
            "OpenRouter returned non-JSON 200 body (len=%s, head=%r, tail=%r)",
            len(text),
            text[:200],
            text[-200:].strip() or "<whitespace>",
        )
        raise HTTPException(
            status_code=502, detail="Invalid response from AI provider."
        )


async def _call_openrouter_streaming(body: dict) -> dict:
    """POST with ``stream: true`` and aggregate the SSE chunks into the same
    response shape as a non-streaming call.

    Streaming is the reliable transport for long generations (e.g. the
    visualization artifact): tokens arrive as they are produced, keep-alive
    comments are explicit SSE comment lines, and a provider failure
    mid-generation surfaces as an error event instead of a silently
    truncated body.
    """
    content_parts: list[str] = []
    tool_calls_acc: dict[int, dict] = {}
    finish_reason: str | None = None

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            OPENROUTER_CHAT_ENDPOINT,
            headers=_auth_headers(),
            json=body,
            timeout=OPENROUTER_TIMEOUT_S,
        ) as response:
            if response.status_code != 200:
                text = (await response.aread()).decode("utf-8", "replace")
                logger.error(
                    "OpenRouter (stream) returned status %s body=%s",
                    response.status_code,
                    text,
                )
                raise HTTPException(
                    status_code=502, detail="Error from AI provider."
                )

            async for raw_line in response.aiter_lines():
                line = raw_line.strip()
                # Blank lines are event separators; lines starting with ':'
                # are SSE comments (": OPENROUTER PROCESSING" keep-alives).
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    logger.warning(
                        "Skipping malformed SSE data line: %r", payload[:200]
                    )
                    continue
                if event.get("error"):
                    logger.error(
                        "OpenRouter mid-stream error: %s", event["error"]
                    )
                    raise HTTPException(
                        status_code=502, detail="Error from AI provider."
                    )
                choices = event.get("choices") or []
                if not choices:
                    continue
                choice = choices[0]
                finish_reason = choice.get("finish_reason") or finish_reason
                delta = choice.get("delta") or {}
                piece = delta.get("content")
                if piece:
                    content_parts.append(piece)
                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    acc = tool_calls_acc.setdefault(
                        idx,
                        {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        },
                    )
                    if tc.get("id"):
                        acc["id"] = tc["id"]
                    fn = tc.get("function") or {}
                    if fn.get("name"):
                        acc["function"]["name"] = fn["name"]
                    if fn.get("arguments"):
                        acc["function"]["arguments"] += fn["arguments"]

    content = "".join(content_parts)
    if finish_reason is None:
        # The stream ended without the provider reporting a finish reason —
        # the connection died mid-generation and `content` is likely
        # truncated. Callers decide whether a partial result is usable.
        logger.warning(
            "OpenRouter stream ended without a finish_reason; "
            "content may be truncated (len=%s)",
            len(content),
        )
    message: dict = {"role": "assistant", "content": content}
    if tool_calls_acc:
        message["tool_calls"] = [
            tool_calls_acc[i] for i in sorted(tool_calls_acc)
        ]
    return {"choices": [{"message": message, "finish_reason": finish_reason}]}


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


# --- Reasoning / chain-of-thought leakage -------------------------------
# Some models (OpenAI Harmony-style gpt-oss, Qwen/DeepSeek <think>, etc.)
# leak their internal reasoning channel into the content field. None of it
# is meant for the end user. The patterns below are intentionally tolerant
# of pipe placement so they match canonical Harmony (`<|channel|>`), the
# malformed variants users have reported (`<|channel>` / `<channel|>`), and
# `<think>...</think>` blocks. If a model still leaks a NEW surface form,
# capture the raw pre-clean string from the debug log in _run_chat_loop and
# extend these patterns.

# Harmony: when channels are present, keep ONLY the `final` channel message.
_HARMONY_FINAL_RE = re.compile(
    r"<\|?channel\|?>\s*final\s*<\|?message\|?>"
    r"([\s\S]*?)(?=<\|?(?:channel|start|end|return)\|?>|$)",
    re.IGNORECASE,
)

# Non-final channel segments (analysis / commentary / reasoning / thought).
_HARMONY_SEGMENT_RE = re.compile(
    r"<\|?channel\|?>\s*(?:analysis|commentary|reasoning|thinking|thought)\b"
    r"[\s\S]*?(?=<\|?(?:channel|start|end|return)\|?>|$)",
    re.IGNORECASE,
)

# <think>...</think> / <thinking>...</thinking> / <reasoning>... blocks.
_THINK_BLOCK_RE = re.compile(
    r"<\s*(think|thinking|reasoning|reflection|thought)\s*>"
    r"[\s\S]*?<\s*/\s*\1\s*>",
    re.IGNORECASE,
)

# Stray standalone control tokens (and an optional trailing role word, e.g.
# the `assistant` that follows `<|start|>` in Harmony) left after the
# structural strips above.
_CONTROL_TOKEN_RE = re.compile(
    r"<\|?\s*/?\s*(?:start|end|return|channel|message|constrain)\s*\|?>"
    r"(?:\s*(?:assistant|developer|user|system))?",
    re.IGNORECASE,
)


def _strip_reasoning_tokens(text: str) -> str:
    """Remove leaked reasoning-channel tokens, keeping only the final answer."""
    if not text:
        return text
    final_matches = _HARMONY_FINAL_RE.findall(text)
    if final_matches:
        # Channels present: the answer is the final-channel message(s).
        text = "\n".join(m.strip() for m in final_matches if m.strip())
    else:
        # No explicit final channel: drop any non-final reasoning segments.
        text = _HARMONY_SEGMENT_RE.sub("", text)
    text = _THINK_BLOCK_RE.sub("", text)
    text = _CONTROL_TOKEN_RE.sub("", text)
    return text.strip()
