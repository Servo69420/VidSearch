from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

OPENROUTER_EMBEDDING_ENDPOINT = "https://openrouter.ai/api/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "perplexity/pplx-embed-v1-0.6b"
DEFAULT_EMBEDDING_DIMENSIONS = 1024


class OpenRouterEmbedder:
    def __init__(
        self,
        *,
        model: str = DEFAULT_EMBEDDING_MODEL,
        expected_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
        timeout_s: float = 60.0,
    ) -> None:
        self._model = model
        self._expected_dimensions = expected_dimensions
        self._timeout_s = timeout_s

    @property
    def model(self) -> str:
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        payload = {
            "model": self._model,
            "input": [t if t and t.strip() else " " for t in texts],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_EMBEDDING_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=self._timeout_s,
            )

        if response.status_code != 200:
            raise RuntimeError(
                "Embedding request failed "
                f"(status={response.status_code} body={response.text})"
            )

        body = response.json()
        vectors = self._extract_vectors(body)

        if len(vectors) != len(texts):
            raise RuntimeError(
                "Embedding response count mismatch "
                f"(expected={len(texts)} got={len(vectors)})"
            )

        for idx, vector in enumerate(vectors):
            if len(vector) != self._expected_dimensions:
                raise RuntimeError(
                    "Embedding dimensions mismatch "
                    f"for item {idx} (expected={self._expected_dimensions} "
                    f"got={len(vector)})"
                )

        return vectors

    @staticmethod
    def _extract_vectors(body: dict[str, Any]) -> list[list[float]]:
        data = body.get("data")
        if isinstance(data, list):
            vectors: list[list[float]] = []
            for row in data:
                if not isinstance(row, dict) or "embedding" not in row:
                    raise RuntimeError("Embedding response missing `embedding` field")
                embedding = row["embedding"]
                if not isinstance(embedding, list):
                    raise RuntimeError("Embedding value is not a list")
                vectors.append([float(v) for v in embedding])
            return vectors

        embeddings = body.get("embeddings")
        if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
            return [[float(v) for v in row] for row in embeddings]

        raise RuntimeError("Unexpected embedding response format")
