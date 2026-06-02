"""Unit tests for the cost-saving additions to the chat pipeline:

- reasoning_effort threaded into the OpenRouter request body
- the frame-analysis cache (get-or-create, describe, cache-hit short-circuit)
- the new model_config cost fields

These run fully offline (OpenRouter and the DB are mocked). They verify the
DECISION logic, not end-to-end cost — proving the bill actually drops needs a
live OpenRouter key + Postgres.
"""

import importlib
import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.routers import chat as chat_module


class _FakeResp:
    status_code = 200

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}


class _FakeClient:
    """Async-context-manager stand-in for httpx.AsyncClient that captures the
    JSON body passed to .post()."""

    def __init__(self, capture):
        self._capture = capture

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, headers=None, json=None, timeout=None):
        self._capture["body"] = json
        return _FakeResp()


class TestReasoningEffortBody(unittest.IsolatedAsyncioTestCase):
    async def test_reasoning_included_when_set(self):
        cap: dict = {}
        with patch.object(chat_module.httpx, "AsyncClient", lambda *a, **k: _FakeClient(cap)):
            await chat_module._call_openrouter(
                [{"role": "user", "content": "hi"}],
                tool_choice="none",
                reasoning_effort="low",
            )
        self.assertEqual(cap["body"].get("reasoning"), {"effort": "low"})

    async def test_reasoning_omitted_when_none(self):
        cap: dict = {}
        with patch.object(chat_module.httpx, "AsyncClient", lambda *a, **k: _FakeClient(cap)):
            await chat_module._call_openrouter(
                [{"role": "user", "content": "hi"}],
                tool_choice="none",
            )
        self.assertNotIn("reasoning", cap["body"])


class TestRunChatLoopThreadsReasoning(unittest.IsolatedAsyncioTestCase):
    async def test_threads_reasoning_effort(self):
        mock = AsyncMock(return_value={"choices": [{"message": {"content": "hi"}}]})
        with patch.object(chat_module, "_call_openrouter", mock):
            await chat_module._run_chat_loop(
                [{"role": "user", "content": "x"}], reasoning_effort="medium"
            )
        self.assertEqual(mock.await_args.kwargs.get("reasoning_effort"), "medium")


class TestGetOrCreateFrameCapture(unittest.IsolatedAsyncioTestCase):
    async def test_cache_hit_returns_analysis_and_bumps_count(self):
        db = AsyncMock()
        db.fetchrow.return_value = {"id": "fid", "analysis": "a description"}
        out = await chat_module._get_or_create_frame_capture("u", "v", 10.0, db)
        self.assertEqual(out, {"id": "fid", "analysis": "a description"})
        db.execute.assert_awaited()        # ask_count / last_asked_at bump
        db.fetchval.assert_not_awaited()   # no insert on a hit

    async def test_cache_miss_creates_row_without_analysis(self):
        db = AsyncMock()
        db.fetchrow.return_value = None
        db.fetchval.return_value = "newid"
        out = await chat_module._get_or_create_frame_capture("u", "v", 10.0, db)
        self.assertEqual(out, {"id": "newid", "analysis": None})
        db.fetchval.assert_awaited()

    async def test_db_failure_returns_none(self):
        db = AsyncMock()
        db.fetchrow.side_effect = Exception("boom")
        out = await chat_module._get_or_create_frame_capture("u", "v", 10.0, db)
        self.assertIsNone(out)


class TestDescribeFrame(unittest.IsolatedAsyncioTestCase):
    async def test_uses_cheap_model_and_low_effort(self):
        mock = AsyncMock(
            return_value={"choices": [{"message": {"content": "  a frame  "}}]}
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            out = await chat_module._describe_frame("b64")
        self.assertEqual(out, "a frame")
        self.assertEqual(
            mock.await_args.kwargs.get("model"), chat_module.VISION_DESCRIPTION_MODEL
        )
        self.assertEqual(mock.await_args.kwargs.get("reasoning_effort"), "low")

    async def test_returns_none_on_provider_failure(self):
        mock = AsyncMock(side_effect=httpx.TimeoutException("t"))
        with patch.object(chat_module, "_call_openrouter", mock):
            out = await chat_module._describe_frame("b64")
        self.assertIsNone(out)


class TestModelConfigCostFields(unittest.TestCase):
    def test_cost_defaults(self):
        module = importlib.import_module("app.model_config")
        with patch.dict(os.environ, {}, clear=True):
            module = importlib.reload(module)
        cfg = module.MODEL_CONFIG
        self.assertEqual(
            cfg.vision_description_model, "google/gemini-2.5-flash-lite:nitro"
        )
        self.assertEqual(cfg.reasoning_effort_chat, "low")
        self.assertEqual(cfg.reasoning_effort_vision, "medium")
        self.assertEqual(cfg.frame_cache_bucket_s, 2.0)

    def test_cost_env_overrides(self):
        env = {
            "OPENROUTER_REASONING_EFFORT_CHAT": "high",
            "OPENROUTER_VISION_DESCRIPTION_MODEL": "cheap/model",
            "FRAME_CACHE_BUCKET_S": "5",
        }
        module = importlib.import_module("app.model_config")
        with patch.dict(os.environ, env, clear=True):
            module = importlib.reload(module)
        cfg = module.MODEL_CONFIG
        self.assertEqual(cfg.reasoning_effort_chat, "high")
        self.assertEqual(cfg.vision_description_model, "cheap/model")
        self.assertEqual(cfg.frame_cache_bucket_s, 5.0)


if __name__ == "__main__":
    unittest.main()
