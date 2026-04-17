from __future__ import annotations

import json
import re

import httpx

from app.config import settings
from app.model_config import MODEL_CONFIG

OPENROUTER_CHAT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterSummarizer:
    def __init__(
        self,
        *,
        model: str = MODEL_CONFIG.phase2_summary_model,
        timeout_s: float = MODEL_CONFIG.openrouter_timeout_s,
    ) -> None:
        self._model = model
        self._timeout_s = timeout_s

    async def summarize(self, chunk) -> tuple[str, str | None, list[str]]:
        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        response = await self._request_summary(chunk.text)
        payload = self._parse_summary_payload(response)

        summary = str(payload.get("summary") or "").strip()
        if not summary:
            summary = chunk.text[:240].strip()

        role = payload.get("role")
        if role is not None:
            role = str(role)

        keywords_raw = payload.get("keywords")
        if isinstance(keywords_raw, list):
            keywords = [str(item).strip() for item in keywords_raw if str(item).strip()]
        else:
            keywords = []

        return summary, role, keywords[:8]

    async def _request_summary(self, text: str) -> str:
        prompt = (
            "Summarize the transcript chunk into one concise topic summary and keywords. "
            "Return ONLY valid JSON with this exact shape: "
            "{\"summary\": string, \"role\": string|null, \"keywords\": string[]}. "
            "Rules: summary max 280 chars, 3-8 keywords, no markdown.\n\n"
            f"Transcript chunk:\n{text}"
        )

        async with httpx.AsyncClient() as client:
            result = await client.post(
                OPENROUTER_CHAT_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You produce strict JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                },
                timeout=self._timeout_s,
            )

        if result.status_code != 200:
            raise RuntimeError(
                "Summary request failed "
                f"(status={result.status_code} body={result.text})"
            )

        body = result.json()
        return body["choices"][0]["message"].get("content") or ""

    def _parse_summary_payload(self, text: str) -> dict:
        candidate = text.strip()
        if not candidate:
            return {}

        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
            candidate = re.sub(r"\s*```$", "", candidate)

        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass

        first = candidate.find("{")
        last = candidate.rfind("}")
        if first != -1 and last != -1 and last > first:
            try:
                parsed = json.loads(candidate[first:last + 1])
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}

        return {}
