import unittest
from unittest.mock import patch

from app.config import settings
from app.openrouter_embedder import OpenRouterEmbedder


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return self._response


class TestOpenRouterEmbedder(unittest.IsolatedAsyncioTestCase):
    async def test_embed_success(self):
        vector = [0.1] * 1024
        response = _FakeResponse(
            200,
            {
                "data": [
                    {"embedding": vector},
                    {"embedding": vector},
                ]
            },
        )

        with (
            patch.object(settings, "OPENROUTER_API_KEY", "test-key"),
            patch(
                "app.openrouter_embedder.httpx.AsyncClient",
                return_value=_FakeClient(response),
            ),
        ):
            embedder = OpenRouterEmbedder()
            out = await embedder.embed(["hello", "world"])

        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[0]), 1024)

    async def test_embed_raises_on_bad_dimensions(self):
        response = _FakeResponse(200, {"data": [{"embedding": [0.1, 0.2]}]})

        with (
            patch.object(settings, "OPENROUTER_API_KEY", "test-key"),
            patch(
                "app.openrouter_embedder.httpx.AsyncClient",
                return_value=_FakeClient(response),
            ),
        ):
            embedder = OpenRouterEmbedder()
            with self.assertRaises(RuntimeError):
                await embedder.embed(["hello"])

    async def test_embed_raises_on_non_200(self):
        response = _FakeResponse(500, {}, text="provider error")

        with (
            patch.object(settings, "OPENROUTER_API_KEY", "test-key"),
            patch(
                "app.openrouter_embedder.httpx.AsyncClient",
                return_value=_FakeClient(response),
            ),
        ):
            embedder = OpenRouterEmbedder()
            with self.assertRaises(RuntimeError):
                await embedder.embed(["hello"])


if __name__ == "__main__":
    unittest.main()
