import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.summarizer import OpenRouterSummarizer


class TestOpenRouterSummarizer(unittest.IsolatedAsyncioTestCase):
    async def test_summarize_parses_json_payload(self):
        summarizer = OpenRouterSummarizer(model="test-model", timeout_s=1.0)
        chunk = SimpleNamespace(text="This is a transcript chunk")

        with (
            patch("app.summarizer.settings.OPENROUTER_API_KEY", "test-key"),
            patch.object(
                summarizer,
                "_request_summary",
                AsyncMock(
                    return_value='{"summary":"Topic summary","role":"topic","keywords":["a","b"]}'
                ),
            ),
        ):
            summary, role, keywords = await summarizer.summarize(chunk)

        self.assertEqual(summary, "Topic summary")
        self.assertEqual(role, "topic")
        self.assertEqual(keywords, ["a", "b"])

    async def test_summarize_falls_back_when_payload_invalid(self):
        summarizer = OpenRouterSummarizer(model="test-model", timeout_s=1.0)
        chunk_text = "x" * 400
        chunk = SimpleNamespace(text=chunk_text)

        with (
            patch("app.summarizer.settings.OPENROUTER_API_KEY", "test-key"),
            patch.object(
                summarizer,
                "_request_summary",
                AsyncMock(return_value="not-json"),
            ),
        ):
            summary, role, keywords = await summarizer.summarize(chunk)

        self.assertEqual(summary, chunk_text[:240])
        self.assertIsNone(role)
        self.assertEqual(keywords, [])

    async def test_summarize_uses_section_prompt_when_mode_section(self):
        summarizer = OpenRouterSummarizer(
            model="test-model", timeout_s=1.0, mode="section"
        )

        class _FakeResponse:
            status_code = 200

            def json(self):
                return {
                    "choices": [
                        {"message": {"content": '{"summary":"ok","keywords":[]}'}}
                    ]
                }

        captured = {}

        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, url, headers, json, timeout):
                captured["body"] = json
                return _FakeResponse()

        with (
            patch("app.summarizer.settings.OPENROUTER_API_KEY", "test-key"),
            patch("app.summarizer.httpx.AsyncClient", lambda *a, **kw: _FakeClient()),
        ):
            await summarizer.summarize(SimpleNamespace(text="topic one. topic two."))

        user_message = captured["body"]["messages"][-1]["content"]
        self.assertIn("adjacent topic summaries", user_message)
        self.assertNotIn("transcript chunk", user_message.lower())

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            OpenRouterSummarizer(model="m", timeout_s=1.0, mode="bogus")


if __name__ == "__main__":
    unittest.main()
