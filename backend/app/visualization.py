"""Dedicated LLM-driven visualization generation.

When the chat model decides a visual would help (by calling the
``request_visualization`` tool), the chat router runs a *separate* LLM call
through :class:`VisualizationGenerator`. That call uses its own
viz-specialised prompt, its own focused transcript context, and its own
configurable model (``MODEL_CONFIG.viz_model``) so it can produce a richer,
self-contained interactive HTML artifact than the main chat turn would.

The artifact is a complete, self-contained HTML document. The frontend
renders it inside a sandboxed ``<iframe>`` (no same-origin access, strict
CSP), so the model is instructed to keep everything inline and make no
network requests.
"""

import json
import logging
import re

import httpx
from fastapi import HTTPException

from app.model_config import MODEL_CONFIG
from app.openrouter_client import (
    _call_openrouter,
    _format_seconds,
    _strip_reasoning_tokens,
)


logger = logging.getLogger(__name__)

# A full self-contained interactive HTML document (inline CSS + JS) is large;
# give the call generous room so it is not truncated mid-document. If the model
# still hits the cap, generation is treated as failed (see finish_reason check).
VIZ_MAX_TOKENS = 16000

VIZ_SYSTEM_PROMPT = (
    "You are a data-visualization engineer. You generate a single, complete, "
    "self-contained interactive HTML document that visualizes the supplied "
    "video-transcript context for a learner.\n\n"
    "STRICT OUTPUT RULES:\n"
    "- Output ONLY the HTML document. No prose, no explanation, and do NOT "
    "wrap it in markdown code fences.\n"
    "- Never write triple backticks (```) anywhere in the output.\n"
    "- The document MUST be fully self-contained: all CSS in inline <style> "
    "and all JS in inline <script>. Do NOT reference any external resource, "
    "stylesheet, font, image URL, CDN, or library — they will be blocked by a "
    "Content-Security-Policy and the visual will break.\n"
    "- Use only vanilla JavaScript, inline SVG, or <canvas> to build charts, "
    "timelines, diagrams, or comparisons. Make it genuinely interactive "
    "(hover, click, toggle) where it aids understanding.\n"
    "- It renders inside a narrow chat panel: make the layout responsive to "
    "the container width and use a dark, modern theme with good contrast.\n"
    "- Ground every label and value strictly in the provided transcript "
    "context. Do not invent facts.\n"
    "- To let the user jump the video, an interactive element may call "
    "`parent.postMessage({ type: 'vidviz-seek', seconds: <number> }, '*')` "
    "on click, using timestamps from the context.\n"
)

# A markdown fence the model may have wrapped the document in despite the
# instruction not to (```html ... ``` / ``` ... ```).
_FENCE_RE = re.compile(r"^\s*```[a-zA-Z]*\s*\n?([\s\S]*?)\n?```\s*$")


# Regenerated artifacts keep their older versions so the user can flip back
# (ChatGPT-branch style). Cap how many are kept — each version is a full HTML
# document, so an uncapped list would bloat the chat_history row.
MAX_VIZ_VERSIONS = 5


def build_visualization_block(
    html: str,
    title: str = "Visualization",
    description: str = "",
    previous_versions: list[dict] | None = None,
) -> str:
    """Wrap generated HTML in a ```vidviz fenced JSON block for the chat content.

    The frontend (MarkdownMessage -> viz registry) intercepts ``vidviz``
    fences and dispatches ``type: "artifact"`` to the sandboxed iframe
    renderer. A standard 3-backtick fence is used so the frontend's
    code-fence-preserving transforms leave it intact; the HTML is guaranteed
    free of triple backticks by :meth:`VisualizationGenerator._extract_html`.

    ``description`` is the original generation request; the frontend sends it
    back to the /chat/visualization endpoint when the user hits Regenerate.

    With ``previous_versions`` (a regeneration), the block carries
    ``data.versions`` — oldest first, new version last and active — so the
    frontend can switch between them. Without it the data is the bare version
    dict, the shape older stored artifacts already use.
    """
    version = {"title": title, "description": description, "html": html}
    if previous_versions:
        versions = (list(previous_versions) + [version])[-MAX_VIZ_VERSIONS:]
        data = {"versions": versions, "active": len(versions) - 1}
    else:
        data = version
    spec = {"type": "artifact", "data": data}
    return "```vidviz\n" + json.dumps(spec) + "\n```"


_VIDVIZ_FENCE_RE = re.compile(r"```vidviz\s*\n([\s\S]*?)\n```", re.IGNORECASE)


def extract_visualization_versions(content: str) -> list[dict]:
    """Return the artifact versions stored in ``content``'s vidviz block.

    Oldest first. Handles both block shapes (bare version dict and
    ``versions`` list) and returns ``[]`` for anything unparseable, so a
    corrupt stored block degrades to a fresh single-version artifact.
    """
    match = _VIDVIZ_FENCE_RE.search(content or "")
    if not match:
        return []
    try:
        spec = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    data = spec.get("data") if isinstance(spec, dict) else None
    if not isinstance(data, dict):
        return []
    versions = data.get("versions")
    if isinstance(versions, list):
        return [
            v for v in versions
            if isinstance(v, dict) and isinstance(v.get("html"), str)
        ]
    if isinstance(data.get("html"), str):
        return [{
            "title": data.get("title") or "Visualization",
            "description": data.get("description") or "",
            "html": data["html"],
        }]
    return []


class VisualizationGenerator:
    """Generates a self-contained HTML artifact from transcript context."""

    def __init__(self, model: str | None = None):
        self._model = model or MODEL_CONFIG.viz_model

    @property
    def model(self) -> str:
        return self._model

    def _format_context(self, context_chunks: list[dict]) -> str:
        lines: list[str] = []
        for chunk in context_chunks or []:
            start = chunk.get("start_s")
            end = chunk.get("end_s")
            text = chunk.get("text", "")
            if start is not None and end is not None:
                lines.append(
                    f"[{_format_seconds(start)} - {_format_seconds(end)}] {text}"
                )
            elif text:
                lines.append(text)
        return "\n".join(lines)

    def _extract_html(self, content: str) -> str | None:
        text = _strip_reasoning_tokens(content or "").strip()
        match = _FENCE_RE.match(text)
        if match:
            text = match.group(1).strip()
        # Remove any stray triple backticks so they cannot break the vidviz
        # fence the document gets embedded in.
        text = text.replace("```", "").strip()
        if "<" not in text:
            # Doesn't look like markup — treat as a failed generation.
            return None
        if not self._looks_complete(text):
            logger.warning("Visualization HTML looks truncated; discarding")
            return None
        return text

    @staticmethod
    def _looks_complete(text: str) -> bool:
        """Reject documents that are structurally cut off.

        A truncated artifact (stream died mid-generation) typically ends
        inside an unterminated <style>/<script> raw-text element; the browser
        then renders an empty page and any bootstrap script the frontend
        appends is swallowed as raw text instead of executing.
        """
        lower = text.lower()
        if "<html" in lower and "</html>" not in lower:
            return False
        for tag in ("style", "script"):
            if lower.count(f"<{tag}") > lower.count(f"</{tag}"):
                return False
        return True

    async def generate(
        self, description: str, context_chunks: list[dict]
    ) -> str | None:
        """Return a self-contained HTML document, or ``None`` on failure.

        Visualization is best-effort: any provider error returns ``None`` so
        the caller can still answer the user in plain text.
        """
        context_text = self._format_context(context_chunks)
        user_content = (
            f"Visualization request: {description.strip() or 'Summarize the key points.'}\n\n"
            "Transcript context (timestamps in [start - end]):\n"
            f"{context_text or '(no transcript context available)'}"
        )
        messages = [
            {"role": "system", "content": VIZ_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        try:
            # Streamed: artifact generation routinely outruns the keep-alive
            # window of a non-streaming call (see _call_openrouter_streaming).
            data = await _call_openrouter(
                messages,
                tool_choice="none",
                model=self._model,
                max_tokens=VIZ_MAX_TOKENS,
                stream=True,
            )
        except (HTTPException, httpx.HTTPError):
            logger.exception("Visualization generation call failed")
            return None

        try:
            choice = data["choices"][0]
            content = choice["message"].get("content") or ""
        except (KeyError, IndexError, TypeError):
            logger.warning("Visualization response had unexpected shape")
            return None

        # Anything other than a clean "stop" means the document is truncated:
        # "length" = token cap, None = the SSE stream died mid-generation
        # (observed in the wild: the artifact ends mid-<style> and renders as
        # an empty black box). Treat all of them as a best-effort failure.
        finish_reason = choice.get("finish_reason")
        if finish_reason != "stop":
            logger.warning(
                "Visualization generation did not finish cleanly "
                "(finish_reason=%r); discarding",
                finish_reason,
            )
            return None

        return self._extract_html(content)
