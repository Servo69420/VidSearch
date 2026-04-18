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


if __name__ == "__main__":
    unittest.main()
